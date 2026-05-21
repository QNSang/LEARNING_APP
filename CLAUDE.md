---
name: ai-learning-os
description: >
  Master project guide for the AI Learning OS / KnowledgeMap Learning System.
  Use this file before planning or coding work in this repository. The project
  may be rebuilt from scratch, but the graph design must learn from Neo4j LLM
  Graph Builder: Document, Chunk, Entity, relationships, community/module
  detection, hybrid retrieval, graph cleanup, and citation-grounded answers.
---

# AI Learning OS - Master Project Guide

This file is the working source of truth for rebuilding or extending the project.
It is intentionally written in ASCII to avoid encoding problems.

Reference docs live in `IDEA/`.

Key references:

- `IDEA/01-product-vision.md`
- `IDEA/02-neo4j-graph-builder-summary.md`
- `IDEA/03-learning-graph-generation-logic.md`
- `IDEA/04-data-model-proposal.md`
- `IDEA/05-feature-design.md`
- `IDEA/06-roadmap.md`

## 1. Product Direction

AI Learning OS transforms learning materials into a structured learning graph,
then uses that graph to guide learning, practice, mastery tracking, and review.

Core loop:

```text
Upload document
-> Parse and chunk
-> Extract learning graph
-> Link nodes to source chunks
-> Detect modules
-> Generate learning path
-> Generate practice items
-> Track mastery
-> Schedule spaced repetition
-> Adapt the next learning step
```

The product must not stop at "chat with PDF". The goal is a graph-based adaptive
learning system.

## 2. Non-Negotiable Principles

1. Every AI answer must cite source chunks when the answer is based on user material.
2. Every knowledge node must have a learning role.
3. The graph drives learning paths, practice, and gap detection. It is not decoration.
4. Active recall is more important than passive reading.
5. AI calls must be routed through a provider abstraction with cache, retry, fallback, and logging.
6. Extraction must use strict schemas. Do not allow free-form node or edge labels in production.
7. Graph quality tools are first-class: duplicate detection, orphan detection, validation, and reprocessing.

## 3. Neo4j Lessons To Apply

The project should learn from `neo4j-labs/llm-graph-builder`, especially these ideas:

```text
(Document)
  <- PART_OF -
(Chunk)
  - NEXT_CHUNK -> (Chunk)
  - HAS_ENTITY -> (KnowledgeNode)

(KnowledgeNode) - learning relationship -> (KnowledgeNode)

(KnowledgeNode) - IN_MODULE -> (Module)
(Module) - PARENT_MODULE -> (Module)
```

Important ideas from Neo4j LLM Graph Builder:

- Keep Document, Chunk, Entity/Node, and Community/Module as separate concepts.
- Store chunk order with `NEXT_CHUNK`.
- Link extracted nodes back to source chunks with evidence.
- Create embeddings for chunks and nodes.
- Support hybrid retrieval: vector search, full-text search, graph traversal, and module/community search.
- Run post-processing after extraction: duplicate merge, orphan cleanup, index creation, community detection.
- Return source/chunk/entity details with chat answers.
- Support retry, cancel, and reprocess states.

For this learning app, "Community" should usually be called "Module" or "Learning Unit".

## 4. Rebuild Strategy

The user is willing to rebuild the project from scratch. Prefer a clean architecture if it reduces future friction.

Recommended default stack:

```text
Frontend: Next.js, React, Tailwind, React Flow
Backend: FastAPI, Python
Database: Supabase/Postgres + pgvector
Optional graph engine later: Neo4j
LLM providers: Gemini, Groq, OpenRouter fallback, Ollama for local dev
```

Do not migrate to Neo4j immediately unless the task explicitly asks for it. Design the data model so it can be mirrored to Neo4j later.

## 5. Target Directory Structure

If rebuilding from scratch, use this structure:

```text
project-root/
  backend/
    app/
      api/
        documents.py
        chunks.py
        graph.py
        modules.py
        practice.py
        mastery.py
        tutor.py
        learning_paths.py
      core/
        config.py
        logging.py
        errors.py
      db/
        supabase_client.py
        repositories/
          document_repo.py
          chunk_repo.py
          graph_repo.py
          module_repo.py
          practice_repo.py
          mastery_repo.py
      models/
        document.py
        chunk.py
        graph.py
        module.py
        practice.py
        mastery.py
      pipeline/
        orchestrator.py
        parser.py
        chunker.py
        embedder.py
        extractor.py
        deduplicator.py
        validator.py
        community.py
        practice_gen.py
      retrieval/
        vector_retriever.py
        graph_retriever.py
        hybrid_retriever.py
        context_builder.py
      services/
        ai_service.py
        fsrs_service.py
        learning_path_service.py
        mastery_service.py
      main.py
    db/
      migrations/
    tests/
      unit/
      integration/
      pipeline/
    requirements.txt
    .env.example
  frontend/
    app/
    components/
    lib/
    hooks/
    stores/
    package.json
    .env.example
  IDEA/
  CLAUDE.md
```

If continuing from the current repo instead of rebuilding, do not create duplicate parallel folders blindly. Migrate incrementally from:

```text
backend/routers
backend/pipeline
backend/db
backend/models
frontend/app
frontend/components
```

to the target structure only when that migration is part of the task.

## 6. Data Model

Use Supabase/Postgres first. Keep names close to graph concepts so migration to Neo4j is straightforward.

### 6.1 documents

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  title TEXT NOT NULL,
  subject TEXT,
  file_path TEXT,
  file_hash TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'new',
  token_count INT,
  selected_model TEXT,
  processing_config JSONB DEFAULT '{}',
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

Status values:

```text
new
processing
ready
error
cancelled
ready_to_reprocess
```

### 6.2 chunks

```sql
CREATE TABLE chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  text TEXT NOT NULL,
  token_count INT,
  page_start INT,
  page_end INT,
  source_ref TEXT,
  embedding VECTOR,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

Do not hardcode embedding dimension in documentation or code unless the embedding model is fixed.
Dimension must match the selected embedding provider.

### 6.3 chunk_links

```sql
CREATE TABLE chunk_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  from_chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  to_chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  link_type TEXT NOT NULL,
  score FLOAT
);
```

Allowed `link_type`:

```text
next_chunk
similar
```

### 6.4 knowledge_nodes

```sql
CREATE TABLE knowledge_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  node_key TEXT NOT NULL,
  label TEXT NOT NULL,
  term TEXT NOT NULL,
  type TEXT NOT NULL,
  importance FLOAT DEFAULT 0.5,
  difficulty FLOAT DEFAULT 0.5,
  description TEXT,
  node_data JSONB DEFAULT '{}',
  embedding VECTOR,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(document_id, node_key)
);
```

Allowed node types:

```text
concept
fact
procedure
formula
example
misconception
learning_objective
exercise
```

### 6.5 knowledge_edges

```sql
CREATE TABLE knowledge_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  from_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  to_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  edge_type TEXT NOT NULL,
  reason TEXT,
  confidence FLOAT DEFAULT 1.0,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

Allowed edge types:

```text
requires
explains
part_of
example_of
applies_to
contrasts_with
causes
leads_to
tested_by
misconception_of
```

### 6.6 node_chunk_refs

This table is mandatory for grounded learning and citations.

```sql
CREATE TABLE node_chunk_refs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  evidence TEXT,
  source_ref TEXT,
  confidence FLOAT DEFAULT 1.0
);
```

Every production knowledge node should have at least one `node_chunk_ref`.

### 6.7 modules and module_nodes

```sql
CREATE TABLE modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  summary TEXT,
  difficulty FLOAT DEFAULT 0.5,
  order_index INT DEFAULT 0,
  metadata JSONB DEFAULT '{}'
);

CREATE TABLE module_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  order_index INT DEFAULT 0
);
```

### 6.8 practice and mastery

```sql
CREATE TABLE practice_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id UUID REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  choices JSONB,
  explanation TEXT,
  source_ref TEXT,
  difficulty FLOAT DEFAULT 0.5,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_node_mastery (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  mastery_score FLOAT DEFAULT 0.0,
  status TEXT DEFAULT 'new',
  last_reviewed_at TIMESTAMPTZ,
  next_review_at TIMESTAMPTZ,
  review_count INT DEFAULT 0,
  correct_count INT DEFAULT 0,
  wrong_count INT DEFAULT 0,
  fsrs_state JSONB DEFAULT '{}',
  UNIQUE(user_id, node_id)
);

CREATE TABLE practice_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  practice_item_id UUID REFERENCES practice_items(id) ON DELETE SET NULL,
  node_id UUID REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
  answer TEXT,
  is_correct BOOLEAN,
  score FLOAT,
  feedback TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

Practice item types:

```text
flashcard
mcq
short_answer
cloze
explain
exercise
```

Mastery statuses:

```text
new
learning
review
mastered
weak
```

### 6.9 learning paths

```sql
CREATE TABLE learning_paths (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
  goal TEXT,
  title TEXT NOT NULL,
  summary TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE learning_path_steps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
  module_id UUID REFERENCES modules(id) ON DELETE SET NULL,
  node_id UUID REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
  step_index INT NOT NULL,
  reason TEXT,
  estimated_minutes INT,
  status TEXT DEFAULT 'pending'
);
```

## 7. Pipeline Design

Pipeline states:

```text
new -> processing -> ready
processing -> error -> ready_to_reprocess -> processing
processing -> cancelled
```

Target pipeline:

```text
parse
-> chunk
-> embed_chunks
-> extract_graph
-> link_refs
-> embed_nodes
-> deduplicate
-> validate
-> detect_modules
-> summarize_modules
-> generate_path
-> generate_practice
```

Rules:

- Each step must be idempotent.
- Each step must log start, success, failure, duration, and item counts.
- A failed step must leave the document in a recoverable state when possible.
- Long pipelines must support retry from the last completed step.
- The first milestone only needs parse, chunk, extract, save graph, and view graph.

## 8. LLM Provider Strategy

Use an `AIService` or equivalent abstraction for all model calls.

Recommended provider roles:

```text
Gemini Flash: long-context document understanding, multimodal, module summaries
Groq Llama 3.3 70B: fast extraction, structured generation, quiz generation
Groq 8B or similar: cheap simple tasks
OpenRouter free models: fallback and experiments only
Ollama: local development and offline testing
```

Do not hardcode one provider throughout the app.

The AI service should support:

- chat/generate,
- structured JSON generation,
- embeddings,
- retry on rate limits,
- fallback models,
- cache by deterministic prompt hash,
- token and latency logging.

## 9. Extraction Contract

Extraction must return strict JSON. No markdown.

Required output shape:

```json
{
  "nodes": [
    {
      "term": "canonical name",
      "label": "display name",
      "type": "concept",
      "description": "short explanation",
      "importance": 0.8,
      "difficulty": 0.4,
      "node_data": {},
      "evidence": "exact phrase or short quote from the chunk"
    }
  ],
  "edges": [
    {
      "from_term": "term from nodes",
      "to_term": "term from nodes",
      "edge_type": "requires",
      "reason": "why this relation exists",
      "confidence": 0.9
    }
  ]
}
```

Extraction rules:

- `from_term` and `to_term` must match extracted node terms or known canonical terms.
- Use only allowed node and edge types.
- Every node needs evidence.
- Do not extract dates, numbers, or isolated parameters as nodes unless they are central learning facts.
- Prefer fewer high-quality nodes over many noisy nodes.

## 10. Validation Rules

Use edge type constraints.

Examples:

```text
example_of: example -> concept/fact/procedure/formula
tested_by: exercise -> concept/fact/procedure/formula
misconception_of: misconception -> concept/fact/procedure
requires: concept/procedure/formula -> concept/procedure/formula
part_of: any learning node -> concept/module-like parent
```

Drop invalid edges or mark them for review. Never silently keep invalid relationships.

## 11. Deduplication

Use four layers:

```text
1. exact normalized match
2. string similarity
3. embedding similarity
4. LLM merge proposal
```

When merging nodes:

1. Keep the more important or better-described node as canonical.
2. Move `node_chunk_refs` to the canonical node.
3. Redirect incoming and outgoing edges.
4. Remove self-loops.
5. Preserve aliases in `node_data.aliases`.
6. Log the merge reason and score.

## 12. Retrieval Modes

Inspired by Neo4j chat modes, the learning app should support:

```text
document: vector/full-text retrieval over chunks
concept: retrieve one node plus its source chunks
graph: retrieve node neighborhood by graph traversal
hybrid: vector + graph + source chunks
module: retrieve module summaries and key nodes
review: retrieve weak prerequisite nodes for practice
```

Tutor answers should return:

```json
{
  "answer": "...",
  "citations": [
    {
      "chunk_id": "...",
      "source_ref": "...",
      "evidence": "..."
    }
  ],
  "nodes_used": [],
  "mode": "hybrid",
  "model": "..."
}
```

## 13. Graph Quality Tools

Build these as real product features, not only backend utilities:

- duplicate node detector,
- merge duplicate nodes,
- orphan node detector,
- edge type validator,
- graph quality report,
- reprocess document,
- retry failed chunk,
- inspect node source chunks,
- inspect module/community grouping.

Graph quality report should include:

```text
node_count
edge_count
orphan_count
duplicate_candidates
edge_type_distribution
nodes_without_source_refs
average_refs_per_node
```

## 14. Frontend Product Views

Main views:

```text
Dashboard
Document upload
Knowledge graph
Node detail
Source chunks
Module view
Learning path
Tutor chat
Practice
Daily review
Graph quality
```

Graph view modes:

```text
Knowledge View
Prerequisite View
Module View
Practice View
Mastery View
Source View
```

Node detail panel should show:

- definition or summary,
- source evidence,
- related chunks,
- prerequisites,
- related nodes,
- examples,
- common mistakes,
- generated practice,
- mastery status.

## 15. Testing Strategy

Phase-specific smoke tests are required.

### Phase 0 smoke test

Minimum for foundation:

```text
1. Upload fixture document.
2. Document status eventually becomes ready or error with useful message.
3. Chunks are created.
4. Knowledge nodes are created.
5. Knowledge edges are created.
6. Graph endpoint returns nodes and edges.
```

Do not require modules, practice items, or tutor in Phase 0.

### Later smoke test

After modules/practice/tutor exist:

```text
1. Every production node has at least one node_chunk_ref.
2. Modules are generated.
3. Practice items are generated.
4. Tutor answer includes citations.
5. Mastery updates after practice submission.
```

Unit tests should cover:

- parser,
- chunker,
- extractor schema parsing,
- validator,
- deduplicator,
- retrieval context builder,
- practice generation,
- mastery scoring,
- AI retry/fallback/cache.

## 16. Engineering Standards

Use these standards as direction, not as an excuse for large unrelated refactors.

Backend:

- Prefer Python 3.11+.
- Prefer FastAPI and Pydantic v2.
- Prefer repository classes for new table groups.
- Do not put complex SQL directly in route handlers.
- Type new public functions.
- Use structured logging.
- Keep pipeline steps idempotent.

Frontend:

- Keep the first screen useful, not a marketing landing page.
- Use existing Next.js app conventions if continuing current code.
- Use React Flow for graph visualization unless replacing it is part of a deliberate redesign.
- Keep controls dense and practical for repeated study workflows.

Database:

- Add new migrations rather than editing applied migrations.
- Prefer additive migrations.
- Add RLS for user-owned tables when auth is in scope.
- Keep embedding dimensions aligned with the selected provider.

## 17. Implementation Roadmap

### Phase 0 - Fix or Rebuild Foundation

Goal: stable upload -> process -> save graph -> view graph.

Tasks:

- Decide whether to continue current repo or rebuild in target structure.
- Standardize `file_hash`.
- Fix migration/code mismatch.
- Add or remove `.txt` parser support.
- Normalize Vietnamese text with Unicode NFC.
- Fix deduplication function naming.
- Add backend and frontend `.env.example`.
- Add Phase 0 smoke test.

### Phase 1 - Chunk and Source References

Goal: every node can be traced back to source text.

Tasks:

- Add `chunks`.
- Add `chunk_links`.
- Add `node_chunk_refs`.
- Save chunk text and source refs.
- Save node evidence.
- Add source tab in node detail panel.

### Phase 2 - Neo4j-Inspired Graph Quality

Goal: higher-quality graph.

Tasks:

- Add richer learning node and edge types.
- Add validator.
- Add duplicate detector and merge.
- Add orphan detector.
- Add graph quality report.

### Phase 3 - GraphRAG Tutor

Goal: grounded tutor with citations.

Tasks:

- Add vector retrieval over chunks.
- Add graph neighborhood retrieval.
- Add hybrid retrieval.
- Add tutor endpoint.
- Return citations and nodes used.

### Phase 4 - Modules and Learning Path

Goal: turn graph into a course-like path.

Tasks:

- Detect modules from graph communities.
- Summarize modules.
- Generate path from prerequisite edges.
- Add module view and learning path sidebar.

### Phase 5 - Practice and Mastery

Goal: graph becomes a progress map.

Tasks:

- Generate flashcards and quizzes.
- Add practice submission.
- Track mastery per node.
- Color graph by mastery.

### Phase 6 - Spaced Repetition

Goal: long-term retention.

Tasks:

- Integrate FSRS.
- Add daily review queue.
- Prioritize weak prerequisites.
- Add knowledge gap detection.

### Phase 7 - Multi-Document Knowledge Base

Goal: subject-level learning workspace.

Tasks:

- Add subjects/workspaces.
- Merge graphs across documents.
- Cross-document dedup.
- Compare explanations across sources.

### Phase 8 - Optional Neo4j Runtime

Goal: use Neo4j when Postgres graph traversal becomes limiting.

Tasks:

- Add `USE_NEO4J` feature flag.
- Mirror documents, chunks, nodes, edges, modules to Neo4j.
- Add Neo4j graph retriever using Cypher.
- Keep Supabase as system of record unless explicitly changed.

## 18. Common Mistakes To Avoid

| Mistake | Correct approach |
|---|---|
| Building only chat-with-PDF | Build learning graph + practice + mastery |
| Letting LLM invent arbitrary labels | Use strict allowed node and edge types |
| Creating nodes without source refs | Require `node_chunk_refs` |
| Treating graph as decoration | Use it for path, retrieval, practice, gap detection |
| Hardcoding one LLM provider | Use AI service with routing and fallback |
| Hardcoding embedding dimension | Match selected embedding model |
| Skipping deduplication | Run duplicate detection and merge |
| Ignoring failed pipeline recovery | Support retry/reprocess |
| Copying Neo4j app directly | Adapt the graph ideas to a learning product |
| Rebuilding without smoke tests | Add Phase 0 smoke test first |

## 19. Quick Reference

Node types:

```text
concept fact procedure formula example misconception learning_objective exercise
```

Edge types:

```text
requires explains part_of example_of applies_to contrasts_with causes leads_to tested_by misconception_of
```

Pipeline:

```text
parse -> chunk -> embed_chunks -> extract_graph -> link_refs -> embed_nodes -> deduplicate -> validate -> detect_modules -> summarize_modules -> generate_path -> generate_practice
```

Retrieval:

```text
document concept graph hybrid module review
```

Statuses:

```text
documents: new processing ready error cancelled ready_to_reprocess
mastery: new learning review mastered weak
```
