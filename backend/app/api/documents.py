"""Document API routes."""

import hashlib
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.repositories.document_repo import DocumentRepository, get_document_repository
from app.models.document import Document, DocumentCreate
from app.pipeline.orchestrator import (
    ChunkingResult,
    DocumentPipeline,
    get_document_pipeline,
)


router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentUploadResponse(BaseModel):
    document: Document


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


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    subject: str | None = Form(default=None),
    selected_model: str | None = Form(default=None),
    settings: Settings = Depends(get_settings),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentUploadResponse:
    """Store an uploaded file locally and create a document record."""

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise AppError(
            "Unsupported file type. Phase 3 supports PDF and TXT.",
            status_code=400,
        )

    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    if not content:
        raise AppError("Uploaded file is empty.", status_code=400)

    file_hash = hashlib.sha256(content).hexdigest()
    safe_name = Path(file.filename or f"{file_hash}{suffix}").name
    stored_path = upload_dir / f"{file_hash[:16]}-{safe_name}"

    async with aiofiles.open(stored_path, "wb") as output:
        await output.write(content)

    document = repo.create(
        DocumentCreate(
            title=safe_name,
            subject=subject,
            file_path=str(stored_path),
            file_hash=file_hash,
            selected_model=selected_model,
            processing_config={
                "chunk_size_chars": settings.chunk_size_chars,
                "chunk_overlap_chars": settings.chunk_overlap_chars,
            },
        )
    )
    return DocumentUploadResponse(document=document)


@router.post("/{document_id}/process", response_model=ChunkingResult)
async def process_document(
    document_id: UUID,
    repo: DocumentRepository = Depends(get_document_repository),
    pipeline: DocumentPipeline = Depends(get_document_pipeline),
) -> ChunkingResult:
    """Run Phase 3 parse and chunk pipeline for an uploaded document."""

    document = repo.get(document_id)
    if document is None:
        raise AppError("Document not found.", status_code=404)
    if not document.file_path:
        raise AppError("Document has no uploaded file path.", status_code=400)

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise AppError("Uploaded source file was not found.", status_code=404)

    return pipeline.parse_and_chunk(document_id, file_path)
