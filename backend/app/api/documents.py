"""Document API routes."""

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentSummary(BaseModel):
    id: str
    title: str
    status: str


@router.get("", response_model=list[DocumentSummary])
async def list_documents() -> list[DocumentSummary]:
    """Return known documents.

    Phase 0 keeps this endpoint intentionally empty until persistence is added.
    """

    return []


@router.get("/{document_id}", response_model=DocumentSummary)
async def get_document(document_id: str) -> DocumentSummary:
    """Return a placeholder document shape for frontend integration."""

    return DocumentSummary(
        id=document_id,
        title="Phase 0 placeholder document",
        status="new",
    )
