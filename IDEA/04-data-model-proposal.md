# Data Model Proposal

Muc tieu: giu Supabase/Postgres trong giai doan dau, nhung thiet ke du lieu du linh hoat de sau nay co the chuyen sang Neo4j neu can.

## 1. documents

Luu metadata tai lieu.

```text
documents
- id
- user_id
- title
- subject
- file_path
- file_hash
- status
- token_count
- selected_model
- processing_config
- error_message
- created_at
- updated_at
```

Status de xuat:

```text
new
processing
ready
error
cancelled
ready_to_reprocess
```

## 2. chunks

Luu text da chia nho.

```text
chunks
- id
- document_id
- chunk_index
- text
- token_count
- page_start
- page_end
- source_ref
- embedding
- created_at
```

## 3. chunk_links

Luu quan he giua chunk.

```text
chunk_links
- id
- document_id
- from_chunk_id
- to_chunk_id
- link_type
- score
```

`link_type`:

```text
next_chunk
similar
```

## 4. knowledge_nodes

Thay the/bo sung cho `graph_nodes`.

```text
knowledge_nodes
- id
- document_id
- node_key
- label
- term
- type
- importance
- difficulty
- description
- node_data
- embedding
- created_at
```

`type`:

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

`node_data` tuy type:

```json
{
  "definition": "...",
  "steps": [],
  "statement": "...",
  "evidence": "...",
  "formula": "...",
  "common_mistake": "..."
}
```

## 5. knowledge_edges

Luu quan he hoc tap giua node.

```text
knowledge_edges
- id
- document_id
- from_node_id
- to_node_id
- edge_type
- reason
- confidence
- created_at
```

`edge_type`:

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

## 6. node_chunk_refs

Bang rat quan trong de truy nguon.

```text
node_chunk_refs
- id
- node_id
- chunk_id
- evidence
- source_ref
- confidence
```

Loi ich:

- citation,
- explain from source,
- grounded AI tutor,
- review nguon goc khi click node.

## 7. modules

Tu community detection hoac LLM grouping.

```text
modules
- id
- document_id
- title
- summary
- difficulty
- order_index
- metadata
```

## 8. module_nodes

Lien ket module voi node.

```text
module_nodes
- id
- module_id
- node_id
- order_index
```

## 9. practice_items

Luu flashcard/quiz/bai tap.

```text
practice_items
- id
- node_id
- document_id
- type
- question
- answer
- choices
- explanation
- source_ref
- difficulty
- created_at
```

`type`:

```text
flashcard
mcq
short_answer
cloze
explain
exercise
```

## 10. user_node_mastery

Theo doi muc do thanh thao cua nguoi hoc.

```text
user_node_mastery
- id
- user_id
- node_id
- mastery_score
- status
- last_reviewed_at
- next_review_at
- review_count
- correct_count
- wrong_count
- fsrs_state
```

`status`:

```text
new
learning
review
mastered
weak
```

## 11. practice_attempts

Luu lich su lam bai.

```text
practice_attempts
- id
- user_id
- practice_item_id
- node_id
- answer
- is_correct
- score
- feedback
- created_at
```

## 12. learning_paths

Lo trinh hoc do AI tao.

```text
learning_paths
- id
- user_id
- document_id
- goal
- title
- summary
- created_at
```

## 13. learning_path_steps

```text
learning_path_steps
- id
- learning_path_id
- module_id
- node_id
- step_index
- reason
- estimated_minutes
- status
```

## Ghi chu quan trong

Data model nen uu tien:

- truy nguon tot,
- validate graph de,
- update mastery de,
- search hybrid de,
- co kha nang migrate sang Neo4j.

Neu sau nay chuyen Neo4j:

- `documents`, `chunks`, `knowledge_nodes`, `modules` thanh nodes.
- `chunk_links`, `knowledge_edges`, `node_chunk_refs`, `module_nodes` thanh relationships.
