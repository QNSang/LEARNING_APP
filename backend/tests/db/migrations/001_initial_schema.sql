-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for documents
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  title TEXT NOT NULL,
  subject TEXT,
  file_path TEXT,           -- path in Supabase Storage
  status TEXT DEFAULT 'processing',  -- processing | ready | error
  sha256 TEXT,              -- For deduplication/caching Pass 1
  summaries JSONB,          -- Cache of chunk summaries
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Table for knowledge graph nodes
CREATE TABLE IF NOT EXISTS graph_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents ON DELETE CASCADE,
  node_id TEXT NOT NULL,    -- snake_case id from AI (e.g., gradient_descent)
  label TEXT NOT NULL,
  term TEXT,                -- English term original
  definition TEXT,          -- short explanation of concept
  type TEXT NOT NULL,       -- concept | procedure | fact
  chunk_index INTEGER,      -- order for sorting/dedup
  source_ref TEXT,          -- display source (e.g., Chapter 1, Slide 15)
  importance TEXT NOT NULL, -- core | supporting | detail
  explanation JSONB,        -- cached result from Node Explanation prompt
  embedding vector(384),    -- sentence-transformers embedding for dedup
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Table for knowledge graph edges
CREATE TABLE IF NOT EXISTS graph_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents ON DELETE CASCADE,
  from_node TEXT NOT NULL,  -- node_id (snake_case)
  to_node TEXT NOT NULL,    -- node_id (snake_case)
  edge_type TEXT NOT NULL,  -- requires | part_of | explains
  reason TEXT,              -- explanation of this relationship
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Table for student essays and grading results
CREATE TABLE IF NOT EXISTS essays (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  node_id UUID REFERENCES graph_nodes,
  content TEXT NOT NULL,
  grading_result JSONB,     -- result from Essay Grading prompt
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_nodes_document_id ON graph_nodes(document_id);
CREATE INDEX IF NOT EXISTS idx_edges_document_id ON graph_edges(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
