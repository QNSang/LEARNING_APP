"""Chunk API routes."""

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags=["chunks"])


class ChunkSummary(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    text: str
    source_ref: str | None = None


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkSummary])
async def list_document_chunks(document_id: str) -> list[ChunkSummary]:
    """Return chunks for a document.

    Phase 0 wires the route; the parser/chunker will populate it in Phase 3.
    """

    return []
