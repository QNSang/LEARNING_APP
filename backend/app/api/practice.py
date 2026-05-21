"""Practice item API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.repositories.practice_repo import PracticeRepository, get_practice_repository
from app.models.practice import (
    PracticeAttempt,
    PracticeAttemptCreate,
    PracticeItem,
    PracticeItemCreate,
)
from app.pipeline.practice_gen import (
    PracticeGenerationResult,
    PracticeGenerator,
    get_practice_generator,
)


router = APIRouter(tags=["practice"])


@router.get("/documents/{document_id}/practice", response_model=list[PracticeItem])
async def list_document_practice(
    document_id: UUID,
    repo: PracticeRepository = Depends(get_practice_repository),
) -> list[PracticeItem]:
    """Return generated practice items for a document."""

    return repo.list_by_document(document_id)


@router.post(
    "/documents/{document_id}/generate-practice",
    response_model=PracticeGenerationResult,
)
async def generate_document_practice(
    document_id: UUID,
    generator: PracticeGenerator = Depends(get_practice_generator),
) -> PracticeGenerationResult:
    """Generate grounded practice items from a document graph."""

    return generator.generate_for_document(document_id)


@router.post("/practice", response_model=PracticeItem)
async def create_practice_item(
    payload: PracticeItemCreate,
    repo: PracticeRepository = Depends(get_practice_repository),
) -> PracticeItem:
    """Create a practice item."""

    return repo.create_item(payload)


@router.post("/practice/attempts", response_model=PracticeAttempt)
async def create_practice_attempt(
    payload: PracticeAttemptCreate,
    repo: PracticeRepository = Depends(get_practice_repository),
) -> PracticeAttempt:
    """Store a practice attempt without changing review scheduling."""

    return repo.create_attempt(payload)
