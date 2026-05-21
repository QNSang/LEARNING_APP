"""Subject workspace models for multi-document knowledge bases."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    user_id: UUID | None = None
    title: str = Field(min_length=1)
    subject: str | None = None
    description: str | None = None


class Workspace(BaseModel):
    id: UUID
    user_id: UUID | None = None
    title: str
    subject: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class WorkspaceDocumentCreate(BaseModel):
    workspace_id: UUID
    document_id: UUID


class WorkspaceDocument(BaseModel):
    id: UUID
    workspace_id: UUID
    document_id: UUID
    created_at: datetime


class WorkspaceDocumentDetail(BaseModel):
    id: UUID
    title: str
    subject: str | None = None
    status: str
    created_at: datetime


class CrossDocumentConcept(BaseModel):
    canonical_key: str
    label: str
    document_count: int
    node_count: int
    documents: list[WorkspaceDocumentDetail]
    descriptions: list[str] = Field(default_factory=list)


class WorkspaceKnowledgeBase(BaseModel):
    workspace: Workspace
    documents: list[WorkspaceDocumentDetail]
    cross_document_concepts: list[CrossDocumentConcept]
