"""Spaced repetition review models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.mastery import UserNodeMastery
from app.models.practice import PracticeItem


class ReviewQueueItem(BaseModel):
    mastery: UserNodeMastery
    practice_item: PracticeItem | None = None
    node_label: str
    node_description: str | None = None
    prerequisite_count: int = 0
    priority: float = Field(ge=0)


class ReviewQueue(BaseModel):
    user_id: UUID | None = None
    due_at: datetime
    items: list[ReviewQueueItem]


class ReviewSubmission(BaseModel):
    user_id: UUID | None = None
    practice_item_id: UUID
    node_id: UUID
    answer: str | None = None
    is_correct: bool | None = None
    score: float = Field(ge=0, le=1)
    feedback: str | None = None


class ReviewResult(BaseModel):
    attempt_id: UUID
    mastery: UserNodeMastery
    fsrs_state: dict[str, Any]
