"""Async pipeline job models."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


PipelineJobStatus = Literal["pending", "processing", "success", "failed"]
PipelineJobStage = Literal[
    "queued",
    "parse",
    "chunk",
    "extract",
    "cleanup",
    "done",
    "failed",
]


class PipelineJobCreate(BaseModel):
    document_id: UUID
    celery_task_id: str | None = None
    status: PipelineJobStatus = "pending"
    stage: PipelineJobStage = "queued"
    progress: int = Field(default=0, ge=0, le=100)
    error_message: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)


class PipelineJobUpdate(BaseModel):
    celery_task_id: str | None = None
    status: PipelineJobStatus | None = None
    stage: PipelineJobStage | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    error_message: str | None = None
    result: dict[str, Any] | None = None


class PipelineJob(BaseModel):
    id: UUID
    document_id: UUID
    celery_task_id: str | None = None
    status: PipelineJobStatus
    stage: PipelineJobStage
    progress: int
    error_message: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
