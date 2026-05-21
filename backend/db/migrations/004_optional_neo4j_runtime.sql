-- Optional Neo4j runtime sync metadata.

CREATE TABLE IF NOT EXISTS neo4j_sync_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('success', 'error')),
  nodes_synced INTEGER NOT NULL DEFAULT 0 CHECK (nodes_synced >= 0),
  edges_synced INTEGER NOT NULL DEFAULT 0 CHECK (edges_synced >= 0),
  chunks_synced INTEGER NOT NULL DEFAULT 0 CHECK (chunks_synced >= 0),
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_neo4j_sync_runs_document_id
  ON neo4j_sync_runs(document_id, created_at DESC);
