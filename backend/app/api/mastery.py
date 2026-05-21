"""Mastery tracking API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.repositories.mastery_repo import MasteryRepository, get_mastery_repository
from app.models.mastery import UserNodeMastery, UserNodeMasteryCreate


router = APIRouter(tags=["mastery"])


@router.get("/users/{user_id}/mastery", response_model=list[UserNodeMastery])
async def list_user_mastery(
    user_id: UUID,
    repo: MasteryRepository = Depends(get_mastery_repository),
) -> list[UserNodeMastery]:
    """Return mastery records for a user."""

    return repo.list_by_user(user_id)


@router.put("/mastery", response_model=UserNodeMastery)
async def upsert_mastery(
    payload: UserNodeMasteryCreate,
    repo: MasteryRepository = Depends(get_mastery_repository),
) -> UserNodeMastery:
    """Create or update mastery for a node."""

    return repo.upsert(payload)
