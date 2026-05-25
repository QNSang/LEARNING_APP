"""Document models."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


DocumentStatus = Literal[
    "new",
    "processing",
    "ready",
    "partial_success",
    "error",
    "cancelled",
    "ready_to_reprocess",
]


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1)
    subject: str | None = None
    file_path: str | None = None
    file_hash: str | None = None
    token_count: int | None = Field(default=None, ge=0)
    selected_model: str | None = None
    processing_config: dict[str, Any] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    subject: str | None = None
    file_path: str | None = None
    file_hash: str | None = None
    status: DocumentStatus | None = None
    token_count: int | None = Field(default=None, ge=0)
    selected_model: str | None = None
    processing_config: dict[str, Any] | None = None
    error_message: str | None = None


class Document(BaseModel):
    id: UUID
    user_id: UUID | None = None
    title: str
    subject: str | None = None
    file_path: str | None = None
    file_hash: str | None = None
    status: DocumentStatus
    token_count: int | None = None
    selected_model: str | None = None
    processing_config: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
