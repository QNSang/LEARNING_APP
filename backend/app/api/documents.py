"""Document API routes."""

import hashlib
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.repositories.document_repo import DocumentRepository, get_document_repository
from app.db.repositories.pipeline_job_repo import (
    PipelineJobRepository,
    get_pipeline_job_repository,
)
from app.models.document import Document, DocumentCreate
from app.models.graph import LearningGraph
from app.models.pipeline_job import PipelineJobCreate, PipelineJobStatus, PipelineJobUpdate
from app.pipeline.orchestrator import (
    ChunkingResult,
    DocumentPipeline,
    GraphCleanupResult,
    get_document_pipeline,
)


router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentUploadResponse(BaseModel):
    document: Document
    job_id: UUID
    task_id: str
    status: PipelineJobStatus


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


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    subject: str | None = Form(default=None),
    selected_model: str | None = Form(default=None),
    settings: Settings = Depends(get_settings),
    repo: DocumentRepository = Depends(get_document_repository),
    job_repo: PipelineJobRepository = Depends(get_pipeline_job_repository),
) -> DocumentUploadResponse:
    """Store an uploaded file locally and enqueue the async pipeline."""

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
    job = job_repo.create(PipelineJobCreate(document_id=document.id))

    try:
        from app.worker.tasks import run_document_pipeline

        task = run_document_pipeline.delay(str(document.id), str(job.id))
        job = job_repo.update(
            job.id,
            PipelineJobUpdate(celery_task_id=task.id),
        )
    except Exception as exc:
        job_repo.update(
            job.id,
            PipelineJobUpdate(
                status="failed",
                stage="failed",
                progress=100,
                error_message=str(exc),
            ),
        )
        raise AppError("Unable to enqueue document pipeline.", status_code=503) from exc

    return DocumentUploadResponse(
        document=document,
        job_id=job.id,
        task_id=job.celery_task_id or "",
        status=job.status,
    )


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


@router.post("/{document_id}/extract-graph", response_model=LearningGraph)
async def extract_document_graph(
    document_id: UUID,
    repo: DocumentRepository = Depends(get_document_repository),
    pipeline: DocumentPipeline = Depends(get_document_pipeline),
) -> LearningGraph:
    """Run Phase 4 Gemini extraction for an already chunked document."""

    document = repo.get(document_id)
    if document is None:
        raise AppError("Document not found.", status_code=404)

    return pipeline.extract_learning_graph(document_id).graph


@router.post("/{document_id}/cleanup-graph", response_model=GraphCleanupResult)
async def cleanup_document_graph(
    document_id: UUID,
    repo: DocumentRepository = Depends(get_document_repository),
    pipeline: DocumentPipeline = Depends(get_document_pipeline),
) -> GraphCleanupResult:
    """Run Phase 5 deduplication and validation for a document graph."""

    document = repo.get(document_id)
    if document is None:
        raise AppError("Document not found.", status_code=404)

    return pipeline.cleanup_learning_graph(document_id)
