"""Learning path models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LearningPathCreate(BaseModel):
    user_id: UUID | None = None
    document_id: UUID
    goal: str | None = None
    title: str = Field(min_length=1)
    summary: str | None = None


class LearningPath(BaseModel):
    id: UUID
    user_id: UUID | None = None
    document_id: UUID
    goal: str | None = None
    title: str
    summary: str | None = None
    created_at: datetime


class LearningPathStepCreate(BaseModel):
    learning_path_id: UUID
    module_id: UUID | None = None
    node_id: UUID | None = None
    step_index: int = Field(ge=0)
    reason: str | None = None
    estimated_minutes: int | None = Field(default=None, gt=0)
    status: str = "new"


class LearningPathStep(BaseModel):
    id: UUID
    learning_path_id: UUID
    module_id: UUID | None = None
    node_id: UUID | None = None
    step_index: int
    reason: str | None = None
    estimated_minutes: int | None = None
    status: str
    created_at: datetime


class LearningPathWithSteps(BaseModel):
    path: LearningPath
    steps: list[LearningPathStep]
