"""Learning graph models."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


NodeType = Literal[
    "concept",
    "fact",
    "procedure",
    "formula",
    "example",
    "misconception",
    "learning_objective",
    "exercise",
]
NodeImportance = Literal["core", "supporting", "detail"]
EdgeType = Literal[
    "requires",
    "explains",
    "part_of",
    "example_of",
    "applies_to",
    "contrasts_with",
    "causes",
    "leads_to",
    "tested_by",
    "misconception_of",
]


class KnowledgeNodeCreate(BaseModel):
    document_id: UUID
    node_key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    term: str | None = None
    type: NodeType
    importance: NodeImportance = "supporting"
    difficulty: int | None = Field(default=None, ge=1, le=5)
    description: str | None = None
    node_data: dict[str, Any] = Field(default_factory=dict)


class KnowledgeNode(BaseModel):
    id: UUID
    document_id: UUID
    node_key: str
    label: str
    term: str | None = None
    type: NodeType
    importance: NodeImportance
    difficulty: int | None = None
    description: str | None = None
    node_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class KnowledgeEdgeCreate(BaseModel):
    document_id: UUID
    from_node_id: UUID
    to_node_id: UUID
    edge_type: EdgeType
    reason: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class KnowledgeEdge(BaseModel):
    id: UUID
    document_id: UUID
    from_node_id: UUID
    to_node_id: UUID
    edge_type: EdgeType
    reason: str | None = None
    confidence: float | None = None
    created_at: datetime


class NodeChunkRefCreate(BaseModel):
    node_id: UUID
    chunk_id: UUID
    evidence: str | None = None
    source_ref: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class NodeChunkRef(BaseModel):
    id: UUID
    node_id: UUID
    chunk_id: UUID
    evidence: str | None = None
    source_ref: str | None = None
    confidence: float | None = None
    created_at: datetime


class LearningGraph(BaseModel):
    document_id: UUID
    nodes: list[KnowledgeNode]
    edges: list[KnowledgeEdge]
    citations: list[NodeChunkRef]
