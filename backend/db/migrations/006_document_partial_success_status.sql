-- Allow documents to finish with partial extraction success.

ALTER TABLE documents
  DROP CONSTRAINT IF EXISTS documents_status_check;

ALTER TABLE documents
  ADD CONSTRAINT documents_status_check
  CHECK (status IN (
    'new',
    'processing',
    'ready',
    'partial_success',
    'error',
    'cancelled',
    'ready_to_reprocess'
  ));
