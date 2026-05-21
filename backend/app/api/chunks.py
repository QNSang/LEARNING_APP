"""Chunk API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.repositories.chunk_repo import ChunkRepository, get_chunk_repository
from app.models.chunk import Chunk


router = APIRouter(tags=["chunks"])


@router.get("/documents/{document_id}/chunks", response_model=list[Chunk])
async def list_document_chunks(
    document_id: UUID,
    repo: ChunkRepository = Depends(get_chunk_repository),
) -> list[Chunk]:
    """Return chunks for a document."""

    return repo.list_by_document(document_id)
