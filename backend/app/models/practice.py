"""Practice models."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


PracticeType = Literal["flashcard", "mcq", "short_answer", "cloze", "explain", "exercise"]


class PracticeItemCreate(BaseModel):
    node_id: UUID
    document_id: UUID
    type: PracticeType
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    choices: list[Any] | dict[str, Any] | None = None
    explanation: str | None = None
    source_ref: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)


class PracticeItem(BaseModel):
    id: UUID
    node_id: UUID
    document_id: UUID
    type: PracticeType
    question: str
    answer: str
    choices: list[Any] | dict[str, Any] | None = None
    explanation: str | None = None
    source_ref: str | None = None
    difficulty: int | None = None
    created_at: datetime


class PracticeAttemptCreate(BaseModel):
    user_id: UUID | None = None
    practice_item_id: UUID
    node_id: UUID
    answer: str | None = None
    is_correct: bool | None = None
    score: float | None = Field(default=None, ge=0, le=1)
    feedback: str | None = None


class PracticeAttempt(BaseModel):
    id: UUID
    user_id: UUID | None = None
    practice_item_id: UUID
    node_id: UUID
    answer: str | None = None
    is_correct: bool | None = None
    score: float | None = None
    feedback: str | None = None
    created_at: datetime
