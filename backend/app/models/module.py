"""Module models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ModuleCreate(BaseModel):
    document_id: UUID
    title: str = Field(min_length=1)
    summary: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    order_index: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Module(BaseModel):
    id: UUID
    document_id: UUID
    title: str
    summary: str | None = None
    difficulty: int | None = None
    order_index: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ModuleNodeCreate(BaseModel):
    module_id: UUID
    node_id: UUID
    order_index: int | None = Field(default=None, ge=0)


class ModuleNode(BaseModel):
    id: UUID
    module_id: UUID
    node_id: UUID
    order_index: int | None = None
    created_at: datetime
