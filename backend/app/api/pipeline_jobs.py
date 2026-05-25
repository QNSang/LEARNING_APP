"""Pipeline job API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.errors import AppError
from app.db.repositories.pipeline_job_repo import (
    PipelineJobRepository,
    get_pipeline_job_repository,
)
from app.models.pipeline_job import PipelineJob


router = APIRouter(tags=["pipeline-jobs"])


@router.get("/pipeline-jobs/{job_id}", response_model=PipelineJob)
async def get_pipeline_job(
    job_id: UUID,
    repo: PipelineJobRepository = Depends(get_pipeline_job_repository),
) -> PipelineJob:
    """Return one async pipeline job."""

    job = repo.get(job_id)
    if job is None:
        raise AppError("Pipeline job not found.", status_code=404)
    return job


@router.get(
    "/documents/{document_id}/pipeline-jobs/latest",
    response_model=PipelineJob,
)
async def get_latest_document_pipeline_job(
    document_id: UUID,
    repo: PipelineJobRepository = Depends(get_pipeline_job_repository),
) -> PipelineJob:
    """Return the latest async pipeline job for a document."""

    job = repo.latest_for_document(document_id)
    if job is None:
        raise AppError("Pipeline job not found.", status_code=404)
    return job
