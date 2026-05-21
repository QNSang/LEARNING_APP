"""Graph validation pipeline step."""

from uuid import UUID

from pydantic import BaseModel

from app.db.repositories.graph_repo import GraphRepository
from app.models.graph import EdgeType, NodeType


ALLOWED_NODE_TYPES = set(NodeType.__args__)
ALLOWED_EDGE_TYPES = set(EdgeType.__args__)


def is_allowed_node_type(value: str) -> bool:
    return value in ALLOWED_NODE_TYPES


def is_allowed_edge_type(value: str) -> bool:
    return value in ALLOWED_EDGE_TYPES


def normalize_node_key(value: str) -> str:
    """Normalize an LLM node key into a stable snake_case-ish identifier."""

    normalized = "".join(char.lower() if char.isalnum() else "_" for char in value)
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized[:120]


class GraphValidationResult(BaseModel):
    removed_edges: int = 0
    removed_orphan_nodes: int = 0
    removed_duplicate_citations: int = 0


class GraphValidator:
    """Clean invalid graph records after extraction and deduplication."""

    def __init__(self, graph_repo: GraphRepository | None = None) -> None:
        self.graph_repo = graph_repo or GraphRepository()

    def validate(self, document_id: UUID) -> GraphValidationResult:
        graph = self.graph_repo.get_graph(document_id)
        result = GraphValidationResult()

        node_ids = {node.id for node in graph.nodes}
        for edge in graph.edges:
            if (
                edge.from_node_id == edge.to_node_id
                or edge.from_node_id not in node_ids
                or edge.to_node_id not in node_ids
                or not is_allowed_edge_type(edge.edge_type)
            ):
                self.graph_repo.delete_edge(edge.id)
                result.removed_edges += 1

        seen_citations: set[tuple[UUID, UUID]] = set()
        cited_node_ids: set[UUID] = set()
        for citation in graph.citations:
            if citation.node_id not in node_ids:
                self.graph_repo.delete_citation(citation.id)
                result.removed_duplicate_citations += 1
                continue

            pair = (citation.node_id, citation.chunk_id)
            if pair in seen_citations:
                self.graph_repo.delete_citation(citation.id)
                result.removed_duplicate_citations += 1
                continue

            seen_citations.add(pair)
            cited_node_ids.add(citation.node_id)

        connected_node_ids = cited_node_ids | {
            edge.from_node_id
            for edge in graph.edges
            if edge.from_node_id in node_ids and edge.to_node_id in node_ids
        } | {
            edge.to_node_id
            for edge in graph.edges
            if edge.from_node_id in node_ids and edge.to_node_id in node_ids
        }

        for node in graph.nodes:
            if node.id not in connected_node_ids or not is_allowed_node_type(node.type):
                self.graph_repo.delete_node(node.id)
                result.removed_orphan_nodes += 1

        return result
