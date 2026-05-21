"""Practice repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.practice import (
    PracticeAttempt,
    PracticeAttemptCreate,
    PracticeItem,
    PracticeItemCreate,
)

from .base import execute_query, first_or_none, to_record


class PracticeRepository:
    """Persistence operations for practice items and attempts."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list_by_document(self, document_id: UUID) -> list[PracticeItem]:
        response = execute_query(
            self.client.table("practice_items")
            .select("*")
            .eq("document_id", str(document_id))
            .order("created_at")
        )
        return [PracticeItem.model_validate(row) for row in response.data or []]

    def get_item(self, practice_item_id: UUID) -> PracticeItem | None:
        response = execute_query(
            self.client.table("practice_items")
            .select("*")
            .eq("id", str(practice_item_id))
            .limit(1)
        )
        row = first_or_none(response.data or [])
        return PracticeItem.model_validate(row) if row else None

    def get_first_for_node(self, node_id: UUID) -> PracticeItem | None:
        response = execute_query(
            self.client.table("practice_items")
            .select("*")
            .eq("node_id", str(node_id))
            .order("created_at")
            .limit(1)
        )
        row = first_or_none(response.data or [])
        return PracticeItem.model_validate(row) if row else None

    def create_item(self, payload: PracticeItemCreate) -> PracticeItem:
        response = execute_query(
            self.client.table("practice_items").insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Practice item was not created.", status_code=500)
        return PracticeItem.model_validate(row)

    def create_items(self, payloads: list[PracticeItemCreate]) -> list[PracticeItem]:
        if not payloads:
            return []
        response = execute_query(
            self.client.table("practice_items").insert(
                [to_record(payload) for payload in payloads]
            )
        )
        return [
            PracticeItem.model_validate(row)
            for row in response.data or []
        ]

    def create_attempt(self, payload: PracticeAttemptCreate) -> PracticeAttempt:
        response = execute_query(
            self.client.table("practice_attempts")
            .insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Practice attempt was not created.", status_code=500)
        return PracticeAttempt.model_validate(row)


def get_practice_repository() -> PracticeRepository:
    return PracticeRepository()
