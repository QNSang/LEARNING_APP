"""Learning graph API routes."""

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags=["graph"])


class GraphResponse(BaseModel):
    document_id: str
    nodes: list[dict]
    edges: list[dict]
    citations: list[dict]


@router.get("/documents/{document_id}/graph", response_model=GraphResponse)
async def get_document_graph(document_id: str) -> GraphResponse:
    """Return the learning graph for a document.

    Phase 0 returns an empty graph so the frontend can integrate against the
    final response shape before extraction is implemented.
    """

    return GraphResponse(
        document_id=document_id,
        nodes=[],
        edges=[],
        citations=[],
    )
