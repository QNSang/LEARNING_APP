"""Mastery models."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


MasteryStatus = Literal["new", "learning", "review", "mastered", "weak"]


class UserNodeMasteryCreate(BaseModel):
    user_id: UUID | None = None
    node_id: UUID
    mastery_score: float = Field(default=0, ge=0, le=1)
    status: MasteryStatus = "new"
    last_reviewed_at: datetime | None = None
    next_review_at: datetime | None = None
    review_count: int = Field(default=0, ge=0)
    correct_count: int = Field(default=0, ge=0)
    wrong_count: int = Field(default=0, ge=0)
    fsrs_state: dict[str, Any] = Field(default_factory=dict)


class UserNodeMastery(BaseModel):
    id: UUID
    user_id: UUID | None = None
    node_id: UUID
    mastery_score: float
    status: MasteryStatus
    last_reviewed_at: datetime | None = None
    next_review_at: datetime | None = None
    review_count: int
    correct_count: int
    wrong_count: int
    fsrs_state: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
