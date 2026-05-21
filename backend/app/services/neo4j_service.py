"""Optional Neo4j mirror service."""

from datetime import UTC, datetime
from uuid import UUID

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.repositories.chunk_repo import ChunkRepository
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.graph_repo import GraphRepository
from app.models.neo4j_runtime import Neo4jRuntimeStatus, Neo4jSyncResult


class Neo4jMirrorService:
    """Mirror Postgres graph records into Neo4j when enabled."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        document_repo: DocumentRepository | None = None,
        chunk_repo: ChunkRepository | None = None,
        graph_repo: GraphRepository | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.document_repo = document_repo or DocumentRepository()
        self.chunk_repo = chunk_repo or ChunkRepository()
        self.graph_repo = graph_repo or GraphRepository()

    def status(self) -> Neo4jRuntimeStatus:
        if not self.settings.use_neo4j:
            return Neo4jRuntimeStatus(
                state="disabled",
                enabled=False,
                configured=False,
                message="Neo4j runtime is disabled. Set USE_NEO4J=true to enable mirroring.",
            )
        if not self._is_configured:
            return Neo4jRuntimeStatus(
                state="not_configured",
                enabled=True,
                configured=False,
                message="Neo4j runtime is enabled but URI, user, or password is missing.",
            )

        try:
            with self._driver() as driver:
                driver.verify_connectivity()
        except ImportError:
            return Neo4jRuntimeStatus(
                state="unavailable",
                enabled=True,
                configured=True,
                message="Install the optional neo4j Python package to use Neo4j mirroring.",
            )
        except Exception:
            return Neo4jRuntimeStatus(
                state="unavailable",
                enabled=True,
                configured=True,
                message="Neo4j is configured but the database is not reachable.",
            )

        return Neo4jRuntimeStatus(
            state="ready",
            enabled=True,
            configured=True,
            message="Neo4j runtime is ready.",
        )

    def sync_document(self, document_id: UUID) -> Neo4jSyncResult:
        status = self.status()
        if status.state != "ready":
            raise AppError(status.message, status_code=503)

        document = self.document_repo.get(document_id)
        if document is None:
            raise AppError("Document not found.", status_code=404)

        chunks = self.chunk_repo.list_by_document(document_id)
        graph = self.graph_repo.get_graph(document_id)

        with self._driver() as driver:
            with driver.session(database=self.settings.neo4j_database) as session:
                session.execute_write(
                    self._merge_document_graph,
                    document.model_dump(mode="json"),
                    [chunk.model_dump(mode="json") for chunk in chunks],
                    [node.model_dump(mode="json") for node in graph.nodes],
                    [edge.model_dump(mode="json") for edge in graph.edges],
                )

        return Neo4jSyncResult(
            document_id=document_id,
            synced_at=datetime.now(UTC),
            nodes_synced=len(graph.nodes),
            edges_synced=len(graph.edges),
            chunks_synced=len(chunks),
            runtime_status=status,
        )

    @property
    def _is_configured(self) -> bool:
        return bool(
            self.settings.neo4j_uri
            and self.settings.neo4j_user
            and self.settings.neo4j_password
        )

    def _driver(self):
        from neo4j import GraphDatabase

        return GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password),
        )

    @staticmethod
    def _merge_document_graph(tx, document, chunks, nodes, edges) -> None:
        tx.run(
            """
            MERGE (d:Document {id: $document.id})
            SET d.title = $document.title,
                d.subject = $document.subject,
                d.status = $document.status,
                d.file_hash = $document.file_hash,
                d.updated_at = datetime()
            """,
            document=document,
        )
        tx.run(
            """
            UNWIND $chunks AS chunk
            MATCH (d:Document {id: chunk.document_id})
            MERGE (c:Chunk {id: chunk.id})
            SET c.chunk_index = chunk.chunk_index,
                c.text = chunk.text,
                c.source_ref = chunk.source_ref,
                c.token_count = chunk.token_count
            MERGE (c)-[:PART_OF]->(d)
            """,
            chunks=chunks,
        )
        tx.run(
            """
            UNWIND $nodes AS node
            MATCH (d:Document {id: node.document_id})
            MERGE (n:KnowledgeNode {id: node.id})
            SET n.node_key = node.node_key,
                n.label = node.label,
                n.term = node.term,
                n.type = node.type,
                n.importance = node.importance,
                n.difficulty = node.difficulty,
                n.description = node.description
            MERGE (n)-[:PART_OF]->(d)
            """,
            nodes=nodes,
        )
        tx.run(
            """
            UNWIND $edges AS edge
            MATCH (from:KnowledgeNode {id: edge.from_node_id})
            MATCH (to:KnowledgeNode {id: edge.to_node_id})
            MERGE (from)-[r:LEARNING_RELATION {id: edge.id}]->(to)
            SET r.edge_type = edge.edge_type,
                r.reason = edge.reason,
                r.confidence = edge.confidence
            """,
            edges=edges,
        )


def get_neo4j_mirror_service() -> Neo4jMirrorService:
    return Neo4jMirrorService()
