"""Celery tasks for document processing."""

from typing import cast
from uuid import UUID

from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.pipeline_job_repo import PipelineJobRepository
from app.models.document import DocumentUpdate
from app.models.pipeline_job import PipelineJobStage, PipelineJobUpdate
from app.pipeline.orchestrator import DocumentPipeline
from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.run_document_pipeline")
def run_document_pipeline(document_id: str, job_id: str) -> dict[str, object]:
    """Run the end-to-end document pipeline in a Celery worker."""

    parsed_document_id = UUID(document_id)
    parsed_job_id = UUID(job_id)
    job_repo = PipelineJobRepository()
    document_repo = DocumentRepository()
    pipeline = DocumentPipeline(document_repo=document_repo)

    try:
        def update_stage(stage: str, progress: int) -> None:
            job_repo.update(
                parsed_job_id,
                PipelineJobUpdate(
                    status="processing",
                    stage=cast(PipelineJobStage, stage),
                    progress=progress,
                ),
            )

        result = pipeline.run_full_pipeline(parsed_document_id, on_stage=update_stage)

        summary = {
            "chunk_count": result.chunk_count,
            "node_count": result.node_count,
            "edge_count": result.edge_count,
        }
        job_repo.update(
            parsed_job_id,
            PipelineJobUpdate(
                status="success",
                stage="done",
                progress=100,
                error_message=None,
                result=summary,
            ),
        )
        return summary
    except Exception as exc:
        message = str(exc)
        job_repo.update(
            parsed_job_id,
            PipelineJobUpdate(
                status="failed",
                stage="failed",
                progress=100,
                error_message=message,
            ),
        )
        document_repo.update(
            parsed_document_id,
            DocumentUpdate(status="error", error_message=message),
        )
        raise
