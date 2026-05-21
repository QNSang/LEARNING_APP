"""Mastery repository."""

from datetime import UTC, datetime
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

    def get_by_user_and_node(
        self,
        *,
        user_id: UUID | None,
        node_id: UUID,
    ) -> UserNodeMastery | None:
        query = self.client.table("user_node_mastery").select("*").eq("node_id", str(node_id))
        if user_id is None:
            query = query.is_("user_id", "null")
        else:
            query = query.eq("user_id", str(user_id))

        response = execute_query(query.limit(1))
        row = first_or_none(response.data or [])
        return UserNodeMastery.model_validate(row) if row else None

    def list_due(
        self,
        *,
        user_id: UUID | None = None,
        limit: int = 25,
        due_at: datetime | None = None,
    ) -> list[dict]:
        due_time = due_at or datetime.now(UTC)
        query = (
            self.client.table("user_node_mastery")
            .select("*, knowledge_nodes!inner(label, description, document_id)")
            .lte("next_review_at", due_time.isoformat())
            .order("next_review_at")
            .limit(limit)
        )
        if user_id is None:
            query = query.is_("user_id", "null")
        else:
            query = query.eq("user_id", str(user_id))

        response = execute_query(query)
        return response.data or []

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
