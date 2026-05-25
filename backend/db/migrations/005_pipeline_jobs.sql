-- Async document pipeline job tracking.

CREATE TABLE IF NOT EXISTS pipeline_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  celery_task_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'processing', 'success', 'failed')),
  stage TEXT NOT NULL DEFAULT 'queued'
    CHECK (stage IN ('queued', 'parse', 'chunk', 'extract', 'cleanup', 'done', 'failed')),
  progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  error_message TEXT,
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS set_pipeline_jobs_updated_at ON pipeline_jobs;
CREATE TRIGGER set_pipeline_jobs_updated_at
BEFORE UPDATE ON pipeline_jobs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_document_id
  ON pipeline_jobs(document_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status
  ON pipeline_jobs(status);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_celery_task_id
  ON pipeline_jobs(celery_task_id);
