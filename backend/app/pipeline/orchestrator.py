"""Pipeline orchestration and state machine."""

import logging
from pathlib import Path
from typing import Callable
from uuid import UUID

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.repositories.chunk_repo import ChunkRepository
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.graph_repo import GraphRepository
from app.models.chunk import Chunk, ChunkCreate, ChunkLinkCreate
from app.models.document import DocumentUpdate
from app.models.graph import (
    KnowledgeEdgeCreate,
    KnowledgeNodeCreate,
    LearningGraph,
    NodeChunkRefCreate,
)
from app.pipeline.chunker import create_chunks
from app.pipeline.deduplicator import DeduplicationResult, GraphDeduplicator
from app.pipeline.extractor import GraphExtractor
from app.pipeline.parser import parse_document
from app.pipeline.validator import GraphValidationResult, GraphValidator


logger = logging.getLogger(__name__)


class ChunkingResult(BaseModel):
    document_id: UUID
    chunk_count: int
    chunks: list[Chunk]


class GraphCleanupResult(BaseModel):
    document_id: UUID
    deduplication: DeduplicationResult
    validation: GraphValidationResult
    graph: LearningGraph


class ExtractionResult(BaseModel):
    graph: LearningGraph
    total_chunks: int
    successful_chunks: int
    failed_chunks: int
    failed_chunk_ids: list[str] = []


class FullPipelineResult(BaseModel):
    document_id: UUID
    chunk_count: int
    node_count: int
    edge_count: int
    document_status: str
    failed_chunk_count: int = 0


class DocumentPipeline:
    """Coordinates parse and chunk steps for a document."""

    def __init__(
        self,
        document_repo: DocumentRepository | None = None,
        chunk_repo: ChunkRepository | None = None,
        graph_repo: GraphRepository | None = None,
        graph_extractor: GraphExtractor | None = None,
        graph_deduplicator: GraphDeduplicator | None = None,
        graph_validator: GraphValidator | None = None,
    ) -> None:
        self.document_repo = document_repo or DocumentRepository()
        self.chunk_repo = chunk_repo or ChunkRepository()
        self.graph_repo = graph_repo or GraphRepository()
        self.graph_extractor = graph_extractor or GraphExtractor()
        self.graph_deduplicator = graph_deduplicator or GraphDeduplicator(self.graph_repo)
        self.graph_validator = graph_validator or GraphValidator(self.graph_repo)
        self.settings = get_settings()

    def parse_and_chunk(
        self,
        document_id: UUID,
        file_path: Path,
        on_stage: Callable[[str, int], None] | None = None,
    ) -> ChunkingResult:
        """Parse a source file, create chunks, and persist chunk links."""

        self.document_repo.update(document_id, DocumentUpdate(status="processing"))

        try:
            if on_stage:
                on_stage("parse", 10)
            pages = parse_document(file_path)
            if on_stage:
                on_stage("chunk", 25)
            prepared_chunks = create_chunks(
                pages,
                chunk_size_chars=self.settings.chunk_size_chars,
                chunk_overlap_chars=self.settings.chunk_overlap_chars,
            )
            chunks = self.chunk_repo.create_many(
                [
                    ChunkCreate(
                        document_id=document_id,
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        token_count=chunk.token_count,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        source_ref=chunk.source_ref,
                    )
                    for chunk in prepared_chunks
                ]
            )
            self._create_chunk_links(document_id, chunks)
            self.document_repo.update(
                document_id,
                DocumentUpdate(
                    status="ready",
                    token_count=sum(chunk.token_count or 0 for chunk in chunks),
                ),
            )
            return ChunkingResult(
                document_id=document_id,
                chunk_count=len(chunks),
                chunks=chunks,
            )
        except Exception as exc:
            self.document_repo.update(
                document_id,
                DocumentUpdate(status="error", error_message=str(exc)),
            )
            raise

    def run_full_pipeline(
        self,
        document_id: UUID,
        on_stage: Callable[[str, int], None] | None = None,
    ) -> FullPipelineResult:
        """Run parse, chunk, graph extraction, and graph cleanup for a document."""

        document = self.document_repo.get(document_id)
        if document is None:
            raise AppError("Document not found.", status_code=404)
        if not document.file_path:
            raise AppError("Document has no uploaded file path.", status_code=400)

        file_path = Path(document.file_path)
        if not file_path.exists():
            raise AppError("Uploaded source file was not found.", status_code=404)

        chunking = self.parse_and_chunk(document_id, file_path, on_stage=on_stage)
        if on_stage:
            on_stage("extract", 45)
        extraction = self.extract_learning_graph(document_id)
        if on_stage:
            on_stage("cleanup", 80)
        cleanup = self.cleanup_learning_graph(document_id)
        document = self.document_repo.get(document_id)
        document_status = document.status if document else "ready"

        return FullPipelineResult(
            document_id=document_id,
            chunk_count=chunking.chunk_count,
            node_count=len(cleanup.graph.nodes),
            edge_count=len(cleanup.graph.edges),
            document_status=document_status,
            failed_chunk_count=extraction.failed_chunks,
        )

    def cleanup_learning_graph(self, document_id: UUID) -> GraphCleanupResult:
        """Run Phase 5 duplicate merge and validation cleanup."""

        previous_document = self.document_repo.get(document_id)
        previous_status = previous_document.status if previous_document else "ready"
        previous_error = previous_document.error_message if previous_document else None
        self.document_repo.update(document_id, DocumentUpdate(status="processing"))
        try:
            deduplication = self.graph_deduplicator.deduplicate(document_id)
            validation = self.graph_validator.validate(document_id)
            graph = self.graph_repo.get_graph(document_id)
            final_status = (
                "partial_success"
                if previous_status == "partial_success"
                else "ready"
            )
            self.document_repo.update(
                document_id,
                DocumentUpdate(status=final_status, error_message=previous_error),
            )
            return GraphCleanupResult(
                document_id=document_id,
                deduplication=deduplication,
                validation=validation,
                graph=graph,
            )
        except Exception as exc:
            self.document_repo.update(
                document_id,
                DocumentUpdate(status="error", error_message=str(exc)),
            )
            raise

    def _create_chunk_links(self, document_id: UUID, chunks: list[Chunk]) -> None:
        if not chunks:
            return

        self.chunk_repo.create_link(
            ChunkLinkCreate(
                document_id=document_id,
                from_chunk_id=None,
                to_chunk_id=chunks[0].id,
                link_type="first_chunk",
            )
        )

        for previous, current in zip(chunks, chunks[1:]):
            self.chunk_repo.create_link(
                ChunkLinkCreate(
                    document_id=document_id,
                    from_chunk_id=previous.id,
                    to_chunk_id=current.id,
                    link_type="next_chunk",
                )
            )

    def extract_learning_graph(self, document_id: UUID) -> ExtractionResult:
        """Extract and persist learning graph nodes, edges, and citations."""

        chunks = self.chunk_repo.list_by_document(document_id)
        if not chunks:
            raise AppError("Document has no chunks to extract from.", status_code=400)

        self.document_repo.update(document_id, DocumentUpdate(status="processing"))
        try:
            node_ids_by_key: dict[str, UUID] = {
                node.node_key: node.id
                for node in self.graph_repo.list_nodes(document_id)
            }
            failed_chunk_ids: list[str] = []

            for chunk in chunks:
                try:
                    extracted = self.graph_extractor.extract_chunk(
                        chunk,
                        existing_node_keys=list(node_ids_by_key.keys()),
                    )
                except AppError as exc:
                    failed_chunk_ids.append(str(chunk.id))
                    logger.warning(
                        "Skipping chunk %s during graph extraction: %s",
                        chunk.id,
                        exc.message,
                    )
                    continue

                for extracted_node in extracted.nodes:
                    saved_node = self.graph_repo.upsert_node(
                        KnowledgeNodeCreate(
                            document_id=document_id,
                            node_key=extracted_node.node_key,
                            label=extracted_node.label,
                            type=extracted_node.type,
                            importance=extracted_node.importance,
                            difficulty=extracted_node.difficulty,
                            description=extracted_node.description,
                            node_data={
                                "source_ref": chunk.source_ref,
                                "chunk_index": chunk.chunk_index,
                            },
                        )
                    )
                    node_ids_by_key[saved_node.node_key] = saved_node.id
                    self.graph_repo.upsert_citation(
                        NodeChunkRefCreate(
                            node_id=saved_node.id,
                            chunk_id=chunk.id,
                            evidence=extracted_node.evidence,
                            source_ref=chunk.source_ref,
                            confidence=extracted_node.confidence,
                        )
                    )

                for extracted_edge in extracted.edges:
                    from_node_id = node_ids_by_key.get(extracted_edge.from_node_key)
                    to_node_id = node_ids_by_key.get(extracted_edge.to_node_key)
                    if not from_node_id or not to_node_id or from_node_id == to_node_id:
                        continue
                    self.graph_repo.upsert_edge(
                        KnowledgeEdgeCreate(
                            document_id=document_id,
                            from_node_id=from_node_id,
                            to_node_id=to_node_id,
                            edge_type=extracted_edge.edge_type,
                            reason=extracted_edge.reason,
                            confidence=extracted_edge.confidence,
                        )
                    )

            successful_chunks = len(chunks) - len(failed_chunk_ids)
            extraction_summary = {
                "total_chunks": len(chunks),
                "successful_chunks": successful_chunks,
                "failed_chunks": len(failed_chunk_ids),
                "failed_chunk_ids": failed_chunk_ids,
            }

            document = self.document_repo.get(document_id)
            processing_config = dict(document.processing_config) if document else {}
            processing_config["extraction"] = extraction_summary

            if successful_chunks == 0:
                message = "Graph extraction failed for every chunk."
                self.document_repo.update(
                    document_id,
                    DocumentUpdate(
                        status="error",
                        processing_config=processing_config,
                        error_message=message,
                    ),
                )
                raise AppError(message, status_code=502)

            if failed_chunk_ids:
                message = (
                    f"Graph extraction partially succeeded: "
                    f"{successful_chunks}/{len(chunks)} chunks processed."
                )
                status = "partial_success"
                error_message = message
            else:
                status = "ready"
                error_message = None

            self.document_repo.update(
                document_id,
                DocumentUpdate(
                    status=status,
                    processing_config=processing_config,
                    error_message=error_message,
                ),
            )
            graph = self.graph_repo.get_graph(document_id)
            return ExtractionResult(
                graph=graph,
                total_chunks=len(chunks),
                successful_chunks=successful_chunks,
                failed_chunks=len(failed_chunk_ids),
                failed_chunk_ids=failed_chunk_ids,
            )
        except Exception as exc:
            self.document_repo.update(
                document_id,
                DocumentUpdate(status="error", error_message=str(exc)),
            )
            raise


def get_document_pipeline() -> DocumentPipeline:
    return DocumentPipeline()
