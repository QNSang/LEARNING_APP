# Learning Graph Generation Logic

Tai lieu nay chuyen hoa logic tu Neo4j LLM Graph Builder thanh pipeline phu hop voi app hoc tap.

## Muc tieu

Tao graph khong chi gom entity/relation, ma gom cac don vi hoc tap co y nghia:

- khai niem can hieu,
- su kien/cau phat bieu can nho,
- quy trinh can lam duoc,
- vi du minh hoa,
- cong thuc,
- dieu kien tien quyet,
- cau hoi kiem tra.

## Pipeline de xuat

```text
1. Upload document
2. Parse document
3. Create chunks
4. Generate chunk embeddings
5. Extract learning nodes
6. Extract learning edges
7. Link nodes to chunks
8. Deduplicate nodes
9. Validate graph
10. Detect communities/modules
11. Generate module summaries
12. Generate learning path
13. Generate quiz/flashcards
```

## Step 1 - Upload document

Input:

- PDF
- DOCX
- PPTX
- TXT
- Web article
- YouTube transcript trong tuong lai

Can luu:

- file name,
- file hash,
- subject,
- user id,
- status,
- token count,
- selected model,
- processing config.

## Step 2 - Parse document

Parser nen tra ve list item:

```json
{
  "page_num": 1,
  "content": "...",
  "metadata": {
    "source": "pdf",
    "file_name": "machine-learning.pdf",
    "source_ref": "machine-learning.pdf - page 1"
  }
}
```

Can uu tien giu citation tot vi moi cau tra loi hoc tap nen co nguon.

## Step 3 - Create chunks

Moi chunk nen co:

- `chunk_id`,
- `document_id`,
- `text`,
- `position`,
- `page_start`,
- `page_end`,
- `source_ref`,
- `embedding`,
- `token_count`.

Nen tao quan he logic:

```text
Document -> Chunk
Chunk -> NEXT_CHUNK -> Chunk
```

Trong Postgres co the luu bang:

- `chunks`
- `chunk_links`

## Step 4 - Extract learning nodes

Thay vi de LLM extract entity tong quat, app nen bat LLM tra ve schema hoc tap.

Node types de xuat:

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

Ban hien tai da co:

```text
concept
fact
procedure
```

Day la loi nen giu lai, sau do mo rong dan.

## Step 5 - Extract learning edges

Relationship types de xuat:

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

Quan trong nhat cho hoc tap:

- `requires`: A can truoc B.
- `part_of`: A la mot phan cua B.
- `example_of`: A la vi du cua B.
- `tested_by`: cau hoi/bai tap kiem tra node nao.

## Step 6 - Link node to chunks

Moi node can biet no den tu dau:

```text
KnowledgeNode -> source chunks
```

Can luu:

- node_id,
- chunk_id,
- confidence,
- evidence text,
- source_ref.

Loi ich:

- click node de xem nguon.
- AI tutor co citation.
- quiz co the dan lai tai lieu.
- tranh hallucination.

## Step 7 - Deduplication

Dedup nen co 4 tang:

1. Exact normalized term.
2. String similarity.
3. Embedding similarity.
4. LLM merge proposal.

Can tranh cac node trung:

```text
Gradient Descent
gradient descent
GD
Giai thuat ha gradient
```

Khi merge, phai merge ca:

- source refs,
- chunk refs,
- importance,
- edges.

## Step 8 - Validation

Can co rule de chan graph loi.

Vi du:

```text
example_of: example -> concept
tested_by: exercise -> concept/fact/procedure
requires: concept/procedure -> concept/procedure
misconception_of: misconception -> concept
```

Neu edge sai type thi drop hoac dua vao hang doi review.

## Step 9 - Community / Module detection

Neo4j repo dung GDS Leiden. Neu app chua dung Neo4j, co the lam ban don gian:

- dua tren connected components,
- dua tren prerequisite clusters,
- dua tren Louvain/Leiden bang Python,
- hoac dung LLM gom node thanh module.

Output:

```text
Module
- title
- summary
- node_ids
- recommended_order
- difficulty
```

Trong app hoc tap, community nen hien thi nhu chuong/bai hoc.

## Step 10 - Generate learning path

Learning path nen dua tren:

- prerequisite edges,
- importance,
- module order,
- user mastery,
- goal cua user.

Vi du:

```text
Start:
1. Core concepts with no prerequisites
2. Supporting concepts required by many nodes
3. Procedures after required concepts
4. Detail nodes only when needed
```

## Step 11 - Generate practice items

Tu moi node co the sinh:

- flashcard,
- multiple choice question,
- short answer,
- cloze deletion,
- explain-in-your-own-words prompt,
- applied exercise.

Moi practice item phai lien ket voi node:

```text
PracticeItem -> tests -> KnowledgeNode
```

## Step 12 - Update mastery

Sau khi nguoi hoc tra loi, update:

- mastery score,
- last reviewed,
- next review,
- difficulty,
- stability,
- retrievability.

Co the dung FSRS cho spaced repetition.

## Summary

Logic graph nen tien hoa tu:

```text
Document -> AI extracted graph
```

thanh:

```text
Document
-> Chunk graph
-> Learning knowledge graph
-> Module graph
-> Practice graph
-> Mastery graph
```
