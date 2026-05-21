"""Mastery repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.mastery import UserNodeMastery, UserNodeMasteryCreate

from .base import execute_query, first_or_none, to_record


class MasteryRepository:
    """Persistence operations for per-user node mastery."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list_by_user(self, user_id: UUID) -> list[UserNodeMastery]:
        response = execute_query(
            self.client.table("user_node_mastery")
            .select("*")
            .eq("user_id", str(user_id))
            .order("updated_at", desc=True)
        )
        return [UserNodeMastery.model_validate(row) for row in response.data or []]

    def upsert(self, payload: UserNodeMasteryCreate) -> UserNodeMastery:
        response = execute_query(
            self.client.table("user_node_mastery")
            .upsert(to_record(payload), on_conflict="user_id,node_id")
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Mastery record was not saved.", status_code=500)
        return UserNodeMastery.model_validate(row)


def get_mastery_repository() -> MasteryRepository:
    return MasteryRepository()
