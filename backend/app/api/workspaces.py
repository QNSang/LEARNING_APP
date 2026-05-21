"""Subject workspace API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.repositories.workspace_repo import WorkspaceRepository, get_workspace_repository
from app.models.workspace import (
    CrossDocumentConcept,
    Workspace,
    WorkspaceCreate,
    WorkspaceDocument,
    WorkspaceDocumentCreate,
    WorkspaceKnowledgeBase,
)


router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[Workspace])
async def list_workspaces(
    user_id: UUID | None = None,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> list[Workspace]:
    """Return subject workspaces."""

    return repo.list(user_id=user_id)


@router.post("", response_model=Workspace, status_code=201)
async def create_workspace(
    payload: WorkspaceCreate,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> Workspace:
    """Create a subject workspace."""

    return repo.create(payload)


@router.post("/{workspace_id}/documents/{document_id}", response_model=WorkspaceDocument)
async def add_document_to_workspace(
    workspace_id: UUID,
    document_id: UUID,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> WorkspaceDocument:
    """Attach a document to a subject workspace."""

    return repo.add_document(
        WorkspaceDocumentCreate(
            workspace_id=workspace_id,
            document_id=document_id,
        )
    )


@router.get("/{workspace_id}/knowledge-base", response_model=WorkspaceKnowledgeBase)
async def get_workspace_knowledge_base(
    workspace_id: UUID,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> WorkspaceKnowledgeBase:
    """Return a workspace-level view across multiple documents."""

    return repo.get_knowledge_base(workspace_id)


@router.get("/{workspace_id}/cross-document-concepts", response_model=list[CrossDocumentConcept])
async def get_cross_document_concepts(
    workspace_id: UUID,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> list[CrossDocumentConcept]:
    """Return duplicate or shared concepts across workspace documents."""

    return repo.find_cross_document_concepts(workspace_id)
