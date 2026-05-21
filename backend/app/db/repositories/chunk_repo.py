"""Chunk repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.chunk import Chunk, ChunkCreate, ChunkLink, ChunkLinkCreate

from .base import execute_query, first_or_none, to_record


class ChunkRepository:
    """Persistence operations for document chunks and chunk links."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list_by_document(self, document_id: UUID) -> list[Chunk]:
        response = execute_query(
            self.client.table("chunks")
            .select("*")
            .eq("document_id", str(document_id))
            .order("chunk_index")
        )
        return [Chunk.model_validate(row) for row in response.data or []]

    def get_many(self, chunk_ids: list[UUID]) -> list[Chunk]:
        if not chunk_ids:
            return []
        response = execute_query(
            self.client.table("chunks")
            .select("*")
            .in_("id", [str(chunk_id) for chunk_id in chunk_ids])
            .order("chunk_index")
        )
        return [Chunk.model_validate(row) for row in response.data or []]

    def create(self, payload: ChunkCreate) -> Chunk:
        response = execute_query(self.client.table("chunks").insert(to_record(payload)))
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Chunk was not created.", status_code=500)
        return Chunk.model_validate(row)

    def create_many(self, payloads: list[ChunkCreate]) -> list[Chunk]:
        if not payloads:
            return []
        response = execute_query(
            self.client.table("chunks")
            .insert([to_record(payload) for payload in payloads])
        )
        return [Chunk.model_validate(row) for row in response.data or []]

    def create_link(self, payload: ChunkLinkCreate) -> ChunkLink:
        response = execute_query(
            self.client.table("chunk_links").insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Chunk link was not created.", status_code=500)
        return ChunkLink.model_validate(row)


def get_chunk_repository() -> ChunkRepository:
    return ChunkRepository()
