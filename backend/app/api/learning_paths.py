"""Learning path API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.errors import AppError
from app.models.learning_path import LearningPathWithSteps
from app.services.learning_path_service import (
    LearningPathService,
    get_learning_path_service,
)


router = APIRouter(tags=["learning_paths"])


class LearningPathRequest(BaseModel):
    user_id: UUID | None = None
    goal: str | None = None


@router.post(
    "/documents/{document_id}/learning-path",
    response_model=LearningPathWithSteps,
)
async def generate_learning_path(
    document_id: UUID,
    payload: LearningPathRequest | None = None,
    service: LearningPathService = Depends(get_learning_path_service),
) -> LearningPathWithSteps:
    """Generate a prerequisite-aware learning path from the document graph."""

    payload = payload or LearningPathRequest()
    return service.generate(
        document_id=document_id,
        user_id=payload.user_id,
        goal=payload.goal,
    )


@router.get(
    "/documents/{document_id}/learning-path",
    response_model=LearningPathWithSteps,
)
async def get_latest_learning_path(
    document_id: UUID,
    user_id: UUID | None = None,
    service: LearningPathService = Depends(get_learning_path_service),
) -> LearningPathWithSteps:
    """Return the latest generated learning path for a document."""

    path = service.latest_for_document(document_id=document_id, user_id=user_id)
    if path is None:
        raise AppError("Learning path not found.", status_code=404)
    return path
