# Roadmap

Roadmap nay uu tien tinh thuc te: lam on dinh pipeline va data model truoc, sau do moi them AI tutor/adaptive learning.

## Phase 0 - Fix Foundation

Muc tieu: lam cho app hien tai chay on dinh.

Viec can lam:

- Dong bo migration voi code backend.
- Sua loi `file_hash` vs `sha256`.
- Them cot `node_data`, `token_count` neu code dang dung.
- Sua parser `.txt` hoac bo `.txt` khoi upload allowed list.
- Sua typo `_llm_deduplication`.
- Chuan hoa encoding tieng Viet.
- Them env example cho backend/frontend.
- Them basic pipeline test.

Ket qua:

```text
Upload document -> process -> save graph -> view graph
```

phai chay on dinh.

## Phase 1 - Document / Chunk / Node Ref Model

Muc tieu: them nen tang GraphRAG dung nghia.

Viec can lam:

- Tao bang `chunks`.
- Tao bang `node_chunk_refs`.
- Luu chunk text, page, source_ref, token_count.
- Link node voi chunk/evidence.
- Tao chunk embeddings.
- Them API lay source chunk cua node.

Ket qua:

Nguoi dung click node va xem duoc nguon goc trong tai lieu.

## Phase 2 - Better Graph Generation

Muc tieu: graph chat luong hon.

Viec can lam:

- Mo rong schema node: formula, example, misconception.
- Mo rong edge types: requires, example_of, tested_by.
- Them validation rules theo node/edge type.
- Them duplicate merge.
- Them orphan detection.
- Them graph quality report.

Ket qua:

Graph it trung lap, it node loi, dung hon cho learning path.

## Phase 3 - GraphRAG Tutor

Muc tieu: chatbot tra loi dua tren graph + chunks.

Viec can lam:

- Them retrieval mode `document`.
- Them retrieval mode `concept`.
- Them retrieval mode `graph`.
- Lay neighbor nodes khi hoi ve mot concept.
- Tra ve citations/chunk refs.
- Cache AI explanations.

Ket qua:

AI tutor co the tra loi theo tai lieu va graph, khong chi theo vector search.

## Phase 4 - Learning Path and Modules

Muc tieu: bien graph thanh lo trinh hoc.

Viec can lam:

- Detect modules/community.
- Tao module summary.
- Tao recommended order dua tren prerequisites.
- Hien module view tren frontend.
- Tao learning path theo goal.

Ket qua:

Nguoi hoc nhin thay minh nen hoc gi truoc, hoc gi sau.

## Phase 5 - Practice and Mastery

Muc tieu: app bat dau giup nguoi hoc nho va kiem tra.

Viec can lam:

- Sinh flashcard tu node.
- Sinh quiz tu node/module.
- Luu practice attempts.
- Cham cau tra loi ngan bang AI.
- Tao `user_node_mastery`.
- Hien mastery color tren graph.

Ket qua:

Graph tro thanh ban do tien do hoc, khong chi ban do kien thuc.

## Phase 6 - Spaced Repetition

Muc tieu: giup nguoi hoc on tap dung luc.

Viec can lam:

- Tich hop FSRS.
- Tao daily review queue.
- Cap nhat next review sau moi attempt.
- Hien lich on tap.
- Uu tien node weak/prerequisite.

Ket qua:

App co co che giup nguoi hoc ghi nho dai han.

## Phase 7 - Multi-Document Knowledge Base

Muc tieu: hoc theo workspace/subject thay vi tung file rieng le.

Viec can lam:

- Tao subject workspace.
- Merge graph giua nhieu documents.
- Dedup cross-document.
- So sanh concept giua cac nguon.
- Tao personal textbook.

Ket qua:

Nguoi hoc co mot knowledge base ca nhan theo mon hoc.

## Phase 8 - Advanced / Optional

Tinh nang nang cao:

- Neo4j integration cho graph lon.
- Graph community bang Leiden/Louvain.
- Multimodal parsing voi Gemini Vision.
- Speech answer grading.
- Teacher/classroom mode.
- Browser extension de import web/course content.
- Export Anki/Markdown/Notion.

## Thu tu uu tien ngan gon

Nen lam theo thu tu:

```text
1. Fix schema/pipeline bugs
2. Add chunks and node-source references
3. Add GraphRAG tutor with citations
4. Add duplicate/orphan cleanup
5. Add learning path
6. Add quiz/flashcard
7. Add mastery + FSRS
```
