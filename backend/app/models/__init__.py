"""Pydantic model package for the target backend layout."""

from app.models.chunk import Chunk, ChunkCreate, ChunkLink, ChunkLinkCreate
from app.models.document import Document, DocumentCreate, DocumentUpdate
from app.models.graph import (
    KnowledgeEdge,
    KnowledgeEdgeCreate,
    KnowledgeNode,
    KnowledgeNodeCreate,
    LearningGraph,
    NodeChunkRef,
    NodeChunkRefCreate,
)
from app.models.mastery import UserNodeMastery, UserNodeMasteryCreate
from app.models.module import Module, ModuleCreate, ModuleNode, ModuleNodeCreate
from app.models.practice import (
    PracticeAttempt,
    PracticeAttemptCreate,
    PracticeItem,
    PracticeItemCreate,
)

__all__ = [
    "Chunk",
    "ChunkCreate",
    "ChunkLink",
    "ChunkLinkCreate",
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "KnowledgeEdge",
    "KnowledgeEdgeCreate",
    "KnowledgeNode",
    "KnowledgeNodeCreate",
    "LearningGraph",
    "Module",
    "ModuleCreate",
    "ModuleNode",
    "ModuleNodeCreate",
    "NodeChunkRef",
    "NodeChunkRefCreate",
    "PracticeAttempt",
    "PracticeAttemptCreate",
    "PracticeItem",
    "PracticeItemCreate",
    "UserNodeMastery",
    "UserNodeMasteryCreate",
]
