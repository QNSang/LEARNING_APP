"""Learning path repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.learning_path import (
    LearningPath,
    LearningPathCreate,
    LearningPathStep,
    LearningPathStepCreate,
    LearningPathWithSteps,
)

from .base import execute_query, first_or_none, to_record


class LearningPathRepository:
    """Persistence operations for learning paths and path steps."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list_by_document(
        self,
        document_id: UUID,
        *,
        user_id: UUID | None = None,
    ) -> list[LearningPath]:
        query = (
            self.client.table("learning_paths")
            .select("*")
            .eq("document_id", str(document_id))
            .order("created_at", desc=True)
        )
        if user_id is None:
            query = query.is_("user_id", "null")
        else:
            query = query.eq("user_id", str(user_id))
        response = execute_query(query)
        return [LearningPath.model_validate(row) for row in response.data or []]

    def get_with_steps(self, learning_path_id: UUID) -> LearningPathWithSteps | None:
        path_response = execute_query(
            self.client.table("learning_paths")
            .select("*")
            .eq("id", str(learning_path_id))
            .limit(1)
        )
        path_row = first_or_none(path_response.data or [])
        if not path_row:
            return None

        step_response = execute_query(
            self.client.table("learning_path_steps")
            .select("*")
            .eq("learning_path_id", str(learning_path_id))
            .order("step_index")
        )
        return LearningPathWithSteps(
            path=LearningPath.model_validate(path_row),
            steps=[
                LearningPathStep.model_validate(row)
                for row in step_response.data or []
            ],
        )

    def create(self, payload: LearningPathCreate) -> LearningPath:
        response = execute_query(
            self.client.table("learning_paths").insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Learning path was not created.", status_code=500)
        return LearningPath.model_validate(row)

    def create_steps(
        self,
        payloads: list[LearningPathStepCreate],
    ) -> list[LearningPathStep]:
        if not payloads:
            return []
        response = execute_query(
            self.client.table("learning_path_steps").insert(
                [to_record(payload) for payload in payloads]
            )
        )
        return [
            LearningPathStep.model_validate(row)
            for row in response.data or []
        ]


def get_learning_path_repository() -> LearningPathRepository:
    return LearningPathRepository()
