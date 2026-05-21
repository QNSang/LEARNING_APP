"""Repository package for table-group data access."""

from app.db.repositories.chunk_repo import ChunkRepository
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.graph_repo import GraphRepository
from app.db.repositories.mastery_repo import MasteryRepository
from app.db.repositories.module_repo import ModuleRepository
from app.db.repositories.practice_repo import PracticeRepository

__all__ = [
    "ChunkRepository",
    "DocumentRepository",
    "GraphRepository",
    "MasteryRepository",
    "ModuleRepository",
    "PracticeRepository",
]
