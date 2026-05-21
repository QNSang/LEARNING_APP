"""Pipeline orchestration and state machine."""

from pathlib import Path
from uuid import UUID

from pydantic import BaseModel

from app.core.config import get_settings
from app.db.repositories.chunk_repo import ChunkRepository
from app.db.repositories.document_repo import DocumentRepository
from app.models.chunk import Chunk, ChunkCreate, ChunkLinkCreate
from app.models.document import DocumentUpdate
from app.pipeline.chunker import create_chunks
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
    ) -> None:
        self.document_repo = document_repo or DocumentRepository()
        self.chunk_repo = chunk_repo or ChunkRepository()
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


def get_document_pipeline() -> DocumentPipeline:
    return DocumentPipeline()
