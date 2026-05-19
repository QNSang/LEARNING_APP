# AI Learning OS

AI Learning OS is a graph-based adaptive learning project. The goal is to turn
learning materials into a structured learning graph, then use that graph to
drive tutoring, practice, mastery tracking, and spaced repetition.

This repository is being rebuilt around a Neo4j-inspired graph architecture:

```text
Document
-> Chunk
-> KnowledgeNode
-> KnowledgeEdge
-> Module
-> LearningPath
-> Practice
-> Mastery
```

## Current Focus

The current milestone is project foundation:

1. Define the product and graph architecture.
2. Create the rebuild folder structure.
3. Keep the graph model inspired by Neo4j LLM Graph Builder.
4. Prepare for a clean backend pipeline:
   `parse -> chunk -> embed -> extract -> deduplicate -> validate`.

## Key Documents

- `CLAUDE.md`: master project guide and engineering direction.
- `IDEA/`: product ideas, Neo4j research summary, data model proposal, and roadmap.

## Planned Stack

- Frontend: Next.js, React, Tailwind CSS, React Flow
- Backend: FastAPI, Python
- Database: Supabase/Postgres with pgvector
- Optional graph runtime: Neo4j
- LLM providers: Gemini, Groq, OpenRouter fallback, Ollama for local development

## Development Status

This project is in rebuild/planning foundation stage. Most runtime files are
currently placeholders. The next implementation step is the Phase 0 smoke path:

```text
upload document -> parse -> chunk -> extract graph -> save graph -> view graph
```
