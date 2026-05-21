"""Module and learning-unit API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.repositories.module_repo import ModuleRepository, get_module_repository
from app.models.module import Module, ModuleCreate, ModuleNode, ModuleNodeCreate


router = APIRouter(tags=["modules"])


@router.get("/documents/{document_id}/modules", response_model=list[Module])
async def list_document_modules(
    document_id: UUID,
    repo: ModuleRepository = Depends(get_module_repository),
) -> list[Module]:
    """Return modules for a document."""

    return repo.list_by_document(document_id)


@router.post("/modules", response_model=Module, status_code=201)
async def create_module(
    payload: ModuleCreate,
    repo: ModuleRepository = Depends(get_module_repository),
) -> Module:
    """Create a module."""

    return repo.create(payload)


@router.post("/module-nodes", response_model=ModuleNode, status_code=201)
async def add_module_node(
    payload: ModuleNodeCreate,
    repo: ModuleRepository = Depends(get_module_repository),
) -> ModuleNode:
    """Attach a graph node to a module."""

    return repo.add_node(payload)
