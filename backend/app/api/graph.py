"""Learning graph API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.repositories.graph_repo import GraphRepository, get_graph_repository
from app.models.graph import LearningGraph


router = APIRouter(tags=["graph"])


@router.get("/documents/{document_id}/graph", response_model=LearningGraph)
async def get_document_graph(
    document_id: UUID,
    repo: GraphRepository = Depends(get_graph_repository),
) -> LearningGraph:
    """Return the learning graph for a document."""

    return repo.get_graph(document_id)
