"""Pipeline orchestration and state machine."""

from pathlib import Path
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
from app.pipeline.extractor import GraphExtractor
from app.pipeline.parser import parse_document


class ChunkingResult(BaseModel):
    document_id: UUID
    chunk_count: int
    chunks: list[Chunk]


class DocumentPipeline:
    """Coordinates parse and chunk steps for a document."""

    def __init__(
        self,
        document_repo: DocumentRepository | None = None,
        chunk_repo: ChunkRepository | None = None,
        graph_repo: GraphRepository | None = None,
        graph_extractor: GraphExtractor | None = None,
    ) -> None:
        self.document_repo = document_repo or DocumentRepository()
        self.chunk_repo = chunk_repo or ChunkRepository()
        self.graph_repo = graph_repo or GraphRepository()
        self.graph_extractor = graph_extractor or GraphExtractor()
        self.settings = get_settings()

    def parse_and_chunk(self, document_id: UUID, file_path: Path) -> ChunkingResult:
        """Parse a source file, create chunks, and persist chunk links."""

        self.document_repo.update(document_id, DocumentUpdate(status="processing"))

        try:
            pages = parse_document(file_path)
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

    def extract_learning_graph(self, document_id: UUID) -> LearningGraph:
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

            for chunk in chunks:
                extracted = self.graph_extractor.extract_chunk(chunk)
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

            self.document_repo.update(document_id, DocumentUpdate(status="ready"))
            return self.graph_repo.get_graph(document_id)
        except Exception as exc:
            self.document_repo.update(
                document_id,
                DocumentUpdate(status="error", error_message=str(exc)),
            )
            raise


def get_document_pipeline() -> DocumentPipeline:
    return DocumentPipeline()
