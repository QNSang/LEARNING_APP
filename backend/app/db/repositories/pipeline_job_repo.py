"""Pipeline job repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.pipeline_job import PipelineJob, PipelineJobCreate, PipelineJobUpdate

from .base import execute_query, first_or_none, to_record


class PipelineJobRepository:
    """Persistence operations for async document pipeline jobs."""

    table_name = "pipeline_jobs"

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def create(self, payload: PipelineJobCreate) -> PipelineJob:
        response = execute_query(
            self.client.table(self.table_name).insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Pipeline job was not created.", status_code=500)
        return PipelineJob.model_validate(row)

    def get(self, job_id: UUID) -> PipelineJob | None:
        response = execute_query(
            self.client.table(self.table_name)
            .select("*")
            .eq("id", str(job_id))
            .limit(1)
        )
        row = first_or_none(response.data or [])
        return PipelineJob.model_validate(row) if row else None

    def latest_for_document(self, document_id: UUID) -> PipelineJob | None:
        response = execute_query(
            self.client.table(self.table_name)
            .select("*")
            .eq("document_id", str(document_id))
            .order("created_at", desc=True)
            .limit(1)
        )
        row = first_or_none(response.data or [])
        return PipelineJob.model_validate(row) if row else None

    def update(self, job_id: UUID, payload: PipelineJobUpdate) -> PipelineJob:
        record = to_record(payload)
        if not record:
            job = self.get(job_id)
            if job is None:
                raise AppError("Pipeline job not found.", status_code=404)
            return job

        response = execute_query(
            self.client.table(self.table_name).update(record).eq("id", str(job_id))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Pipeline job not found.", status_code=404)
        return PipelineJob.model_validate(row)


def get_pipeline_job_repository() -> PipelineJobRepository:
    return PipelineJobRepository()
