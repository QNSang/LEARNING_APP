# Neo4j LLM Graph Builder - Summary

Repo tham khao: https://github.com/neo4j-labs/llm-graph-builder

## Muc tieu cua repo

Repo nay bien du lieu phi cau truc thanh Knowledge Graph trong Neo4j bang LLM va LangChain.

Nguon du lieu ho tro:

- Local files
- PDF
- YouTube transcript
- Wikipedia
- Web page
- AWS S3
- Google Cloud Storage

## Kien truc tong quat

```text
Source
-> Document node
-> Chunks
-> Chunk embeddings
-> LLM graph extraction
-> Entity nodes and relationships
-> Chunk-Entity links
-> Vector / full-text indexes
-> Post-processing
-> Chat modes / GraphRAG
```

## Graph schema chinh

Repo dung graph model dang:

```text
(Document)
  <-[:PART_OF]-
(Chunk)
  -[:NEXT_CHUNK]-> (Chunk)
  -[:HAS_ENTITY]-> (Entity)

(Entity)-[RELATION]->(Entity)

(Entity)-[:IN_COMMUNITY]->(Community)
(Community)-[:PARENT_COMMUNITY]->(Community)
```

Y nghia:

- `Document`: nguon tai lieu.
- `Chunk`: doan text nho, co position/page/timestamp.
- `Entity`: thuc the/kien thuc duoc LLM trich xuat.
- `Community`: cum entity co lien quan.

## Cac relationship quan trong

- `PART_OF`: chunk thuoc document.
- `FIRST_CHUNK`: chunk dau tien cua document.
- `NEXT_CHUNK`: noi thu tu cac chunk.
- `HAS_ENTITY`: chunk chua entity.
- `SIMILAR`: hai chunk gan nhau theo embedding.
- `IN_COMMUNITY`: entity thuoc community.
- `PARENT_COMMUNITY`: community con thuoc community cha.

## LLM extraction

Repo dung `LLMGraphTransformer` cua LangChain de bien chunk thanh graph document.

Co the cau hinh:

- model LLM,
- allowed node labels,
- allowed relationship types,
- additional instructions,
- chunk size,
- chunks to combine.

Day la y tuong rat dang hoc: graph extraction nen co schema va instruction ro rang, khong de LLM tu tao label qua tu do.

## Post-processing

Repo co nhieu buoc lam sach va tang chat luong graph:

- Tao embedding cho chunk.
- Tao embedding cho entity.
- Tao vector index.
- Tao full-text index.
- Tim chunk tuong tu bang KNN va tao `SIMILAR`.
- Tim duplicate nodes.
- Merge duplicate nodes.
- Xoa orphan/disconnected nodes.
- Gom community bang Neo4j GDS.
- Tom tat community bang LLM.

## Chat modes

Repo co nhieu mode hoi dap:

- `vector`: tim chunk bang vector search.
- `fulltext`: tim chunk bang full-text.
- `graph_vector`: vector search roi mo rong sang graph.
- `graph_vector_fulltext`: ket hop graph, vector va full-text.
- `entity_vector`: tim entity roi lay context lien quan.
- `global_vector`: tim community summary.
- `graph`: sinh Cypher query hoi truc tiep graph.

## Diem nen ung dung vao app hoc tap

1. Tach `Document`, `Chunk`, `Knowledge Node`.
2. Luu quan he chunk -> node de truy nguon.
3. Luu `NEXT_CHUNK` de giu ngu canh.
4. Tao embedding cho chunk va node.
5. Them post-processing: duplicate, orphan, community.
6. Co nhieu chat modes theo muc dich hoc.
7. Co retry/cancel/reprocess cho pipeline dai.
8. Chatbot tra ve source, chunk, entity, community details.

## Diem khong nen copy nguyen

- Khong nen chuyen ngay sang Neo4j neu Supabase/Postgres van du.
- Khong nen dung graph schema qua tong quat cho app hoc tap.
- Khong nen de LLM tu sinh label tuy y.
- Khong nen copy UI vi repo nay thien ve graph builder cho developer, khong phai learning app.
