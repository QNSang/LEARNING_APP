"""Knowledge graph repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.graph import (
    KnowledgeEdge,
    KnowledgeEdgeCreate,
    KnowledgeNode,
    KnowledgeNodeCreate,
    LearningGraph,
    NodeChunkRef,
    NodeChunkRefCreate,
)

from .base import execute_query, first_or_none, to_record


class GraphRepository:
    """Persistence operations for learning graph nodes, edges, and citations."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list_nodes(self, document_id: UUID) -> list[KnowledgeNode]:
        response = execute_query(
            self.client.table("knowledge_nodes")
            .select("*")
            .eq("document_id", str(document_id))
            .order("created_at")
        )
        return [KnowledgeNode.model_validate(row) for row in response.data or []]

    def list_edges(self, document_id: UUID) -> list[KnowledgeEdge]:
        response = execute_query(
            self.client.table("knowledge_edges")
            .select("*")
            .eq("document_id", str(document_id))
            .order("created_at")
        )
        return [KnowledgeEdge.model_validate(row) for row in response.data or []]

    def list_citations(self, document_id: UUID) -> list[NodeChunkRef]:
        response = execute_query(
            self.client.table("node_chunk_refs")
            .select("*, knowledge_nodes!inner(document_id)")
            .eq("knowledge_nodes.document_id", str(document_id))
            .order("created_at")
        )
        citations: list[NodeChunkRef] = []
        for row in response.data or []:
            row.pop("knowledge_nodes", None)
            citations.append(NodeChunkRef.model_validate(row))
        return citations

    def get_graph(self, document_id: UUID) -> LearningGraph:
        return LearningGraph(
            document_id=document_id,
            nodes=self.list_nodes(document_id),
            edges=self.list_edges(document_id),
            citations=self.list_citations(document_id),
        )

    def create_node(self, payload: KnowledgeNodeCreate) -> KnowledgeNode:
        response = execute_query(
            self.client.table("knowledge_nodes")
            .insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Knowledge node was not created.", status_code=500)
        return KnowledgeNode.model_validate(row)

    def create_edge(self, payload: KnowledgeEdgeCreate) -> KnowledgeEdge:
        response = execute_query(
            self.client.table("knowledge_edges")
            .insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Knowledge edge was not created.", status_code=500)
        return KnowledgeEdge.model_validate(row)

    def create_citation(self, payload: NodeChunkRefCreate) -> NodeChunkRef:
        response = execute_query(
            self.client.table("node_chunk_refs")
            .insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Citation was not created.", status_code=500)
        return NodeChunkRef.model_validate(row)


def get_graph_repository() -> GraphRepository:
    return GraphRepository()
