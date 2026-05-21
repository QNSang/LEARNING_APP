-- AI Learning OS initial schema.
-- Designed for Supabase/Postgres first, with graph-shaped tables that can be
-- mirrored to Neo4j later.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  subject TEXT,
  file_path TEXT,
  file_hash TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN (
      'new',
      'processing',
      'ready',
      'error',
      'cancelled',
      'ready_to_reprocess'
    )),
  token_count INTEGER CHECK (token_count IS NULL OR token_count >= 0),
  selected_model TEXT,
  processing_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
  text TEXT NOT NULL,
  token_count INTEGER CHECK (token_count IS NULL OR token_count >= 0),
  page_start INTEGER CHECK (page_start IS NULL OR page_start >= 0),
  page_end INTEGER CHECK (page_end IS NULL OR page_end >= 0),
  source_ref TEXT,
  embedding vector,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (document_id, chunk_index),
  CHECK (
    page_start IS NULL
    OR page_end IS NULL
    OR page_end >= page_start
  )
);

CREATE TABLE IF NOT EXISTS chunk_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  from_chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE,
  to_chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  link_type TEXT NOT NULL CHECK (link_type IN ('first_chunk', 'next_chunk', 'similar')),
  score DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (score IS NULL OR score >= 0)
);

CREATE TABLE IF NOT EXISTS knowledge_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  node_key TEXT NOT NULL,
  label TEXT NOT NULL,
  term TEXT,
  type TEXT NOT NULL CHECK (type IN (
    'concept',
    'fact',
    'procedure',
    'formula',
    'example',
    'misconception',
    'learning_objective',
    'exercise'
  )),
  importance TEXT NOT NULL DEFAULT 'supporting'
    CHECK (importance IN ('core', 'supporting', 'detail')),
  difficulty INTEGER CHECK (difficulty IS NULL OR difficulty BETWEEN 1 AND 5),
  description TEXT,
  node_data JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding vector,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (document_id, node_key)
);

CREATE TABLE IF NOT EXISTS knowledge_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  from_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  to_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  edge_type TEXT NOT NULL CHECK (edge_type IN (
    'requires',
    'explains',
    'part_of',
    'example_of',
    'applies_to',
    'contrasts_with',
    'causes',
    'leads_to',
    'tested_by',
    'misconception_of'
  )),
  reason TEXT,
  confidence DOUBLE PRECISION CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (from_node_id <> to_node_id),
  UNIQUE (document_id, from_node_id, to_node_id, edge_type)
);

-- Citation relationship. In Neo4j terms this is equivalent to:
-- (Chunk)-[:HAS_ENTITY { evidence, confidence, source_ref }]->(KnowledgeNode)
CREATE TABLE IF NOT EXISTS node_chunk_refs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  evidence TEXT,
  source_ref TEXT,
  confidence DOUBLE PRECISION CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (node_id, chunk_id)
);

CREATE TABLE IF NOT EXISTS modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  summary TEXT,
  difficulty INTEGER CHECK (difficulty IS NULL OR difficulty BETWEEN 1 AND 5),
  order_index INTEGER CHECK (order_index IS NULL OR order_index >= 0),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS module_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  order_index INTEGER CHECK (order_index IS NULL OR order_index >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (module_id, node_id)
);

CREATE TABLE IF NOT EXISTS practice_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN (
    'flashcard',
    'mcq',
    'short_answer',
    'cloze',
    'explain',
    'exercise'
  )),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  choices JSONB,
  explanation TEXT,
  source_ref TEXT,
  difficulty INTEGER CHECK (difficulty IS NULL OR difficulty BETWEEN 1 AND 5),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_node_mastery (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  mastery_score DOUBLE PRECISION NOT NULL DEFAULT 0
    CHECK (mastery_score BETWEEN 0 AND 1),
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new', 'learning', 'review', 'mastered', 'weak')),
  last_reviewed_at TIMESTAMPTZ,
  next_review_at TIMESTAMPTZ,
  review_count INTEGER NOT NULL DEFAULT 0 CHECK (review_count >= 0),
  correct_count INTEGER NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
  wrong_count INTEGER NOT NULL DEFAULT 0 CHECK (wrong_count >= 0),
  fsrs_state JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, node_id)
);

CREATE TABLE IF NOT EXISTS practice_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  practice_item_id UUID NOT NULL REFERENCES practice_items(id) ON DELETE CASCADE,
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  answer TEXT,
  is_correct BOOLEAN,
  score DOUBLE PRECISION CHECK (score IS NULL OR score BETWEEN 0 AND 1),
  feedback TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS learning_paths (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  goal TEXT,
  title TEXT NOT NULL,
  summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS learning_path_steps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
  module_id UUID REFERENCES modules(id) ON DELETE SET NULL,
  node_id UUID REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
  step_index INTEGER NOT NULL CHECK (step_index >= 0),
  reason TEXT,
  estimated_minutes INTEGER CHECK (estimated_minutes IS NULL OR estimated_minutes > 0),
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new', 'in_progress', 'completed', 'skipped')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (learning_path_id, step_index),
  CHECK (module_id IS NOT NULL OR node_id IS NOT NULL)
);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_documents_updated_at ON documents;
CREATE TRIGGER set_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_user_node_mastery_updated_at ON user_node_mastery;
CREATE TRIGGER set_user_node_mastery_updated_at
BEFORE UPDATE ON user_node_mastery
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_order ON chunks(document_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_chunks_text_fts
  ON chunks USING gin (to_tsvector('simple', text));

CREATE INDEX IF NOT EXISTS idx_chunk_links_document_id ON chunk_links(document_id);
CREATE INDEX IF NOT EXISTS idx_chunk_links_from_chunk ON chunk_links(from_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_links_to_chunk ON chunk_links(to_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_links_type ON chunk_links(link_type);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_document_id ON knowledge_nodes(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_term_fts
  ON knowledge_nodes USING gin (to_tsvector('simple', coalesce(term, '') || ' ' || coalesce(description, '')));

CREATE INDEX IF NOT EXISTS idx_knowledge_edges_document_id ON knowledge_edges(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_from_node ON knowledge_edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_to_node ON knowledge_edges(to_node_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_type ON knowledge_edges(edge_type);

CREATE INDEX IF NOT EXISTS idx_node_chunk_refs_node_id ON node_chunk_refs(node_id);
CREATE INDEX IF NOT EXISTS idx_node_chunk_refs_chunk_id ON node_chunk_refs(chunk_id);

CREATE INDEX IF NOT EXISTS idx_modules_document_id ON modules(document_id);
CREATE INDEX IF NOT EXISTS idx_module_nodes_module_id ON module_nodes(module_id);
CREATE INDEX IF NOT EXISTS idx_module_nodes_node_id ON module_nodes(node_id);

CREATE INDEX IF NOT EXISTS idx_practice_items_document_id ON practice_items(document_id);
CREATE INDEX IF NOT EXISTS idx_practice_items_node_id ON practice_items(node_id);

CREATE INDEX IF NOT EXISTS idx_user_node_mastery_user_id ON user_node_mastery(user_id);
CREATE INDEX IF NOT EXISTS idx_user_node_mastery_node_id ON user_node_mastery(node_id);
CREATE INDEX IF NOT EXISTS idx_user_node_mastery_next_review ON user_node_mastery(next_review_at);

CREATE INDEX IF NOT EXISTS idx_practice_attempts_user_id ON practice_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_practice_attempts_node_id ON practice_attempts(node_id);

CREATE INDEX IF NOT EXISTS idx_learning_paths_user_document ON learning_paths(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_learning_path_steps_path_order ON learning_path_steps(learning_path_id, step_index);
