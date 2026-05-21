"""Chunk models."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ChunkLinkType = Literal["first_chunk", "next_chunk", "similar"]


class ChunkCreate(BaseModel):
    document_id: UUID
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)
    token_count: int | None = Field(default=None, ge=0)
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    source_ref: str | None = None


class Chunk(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    token_count: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_ref: str | None = None
    created_at: datetime


class ChunkLinkCreate(BaseModel):
    document_id: UUID
    from_chunk_id: UUID | None = None
    to_chunk_id: UUID
    link_type: ChunkLinkType
    score: float | None = Field(default=None, ge=0)


class ChunkLink(BaseModel):
    id: UUID
    document_id: UUID
    from_chunk_id: UUID | None = None
    to_chunk_id: UUID
    link_type: ChunkLinkType
    score: float | None = None
    created_at: datetime
