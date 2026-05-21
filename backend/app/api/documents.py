"""Document API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.errors import AppError
from app.db.repositories.document_repo import DocumentRepository, get_document_repository
from app.models.document import Document, DocumentCreate


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[Document])
async def list_documents(
    repo: DocumentRepository = Depends(get_document_repository),
) -> list[Document]:
    """Return known documents."""

    return repo.list()


@router.post("", response_model=Document, status_code=201)
async def create_document(
    payload: DocumentCreate,
    repo: DocumentRepository = Depends(get_document_repository),
) -> Document:
    """Create a document metadata record."""

    return repo.create(payload)


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: UUID,
    repo: DocumentRepository = Depends(get_document_repository),
) -> Document:
    """Return one document by id."""

    document = repo.get(document_id)
    if document is None:
        raise AppError("Document not found.", status_code=404)
    return document
