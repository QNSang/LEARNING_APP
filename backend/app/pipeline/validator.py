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
    normalized = "".join(char.lower() if char.isalnum() else "_" for char in value)
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized[:120]


class GraphValidationResult(BaseModel):
    removed_edges: int = 0
    removed_orphan_nodes: int = 0
    removed_duplicate_citations: int = 0
    audit_log: list[str] = []          # ← thêm audit log


class GraphValidator:
    """Clean invalid graph records after extraction and deduplication."""

    def __init__(self, graph_repo: GraphRepository | None = None) -> None:
        self.graph_repo = graph_repo or GraphRepository()

    def validate(self, document_id: UUID) -> GraphValidationResult:
        graph = self.graph_repo.get_graph(document_id)
        result = GraphValidationResult()

        # ── Pass 1: Xóa edges không hợp lệ ──────────────────────────────
        node_ids = {node.id for node in graph.nodes}
        for edge in graph.edges:
            reason = None
            if edge.from_node_id == edge.to_node_id:
                reason = "self-loop"
            elif edge.from_node_id not in node_ids:
                reason = "from_node missing"
            elif edge.to_node_id not in node_ids:
                reason = "to_node missing"
            elif not is_allowed_edge_type(edge.edge_type):
                reason = f"invalid edge_type: {edge.edge_type}"

            if reason:
                self.graph_repo.delete_edge(edge.id)
                result.removed_edges += 1
                result.audit_log.append(f"edge {edge.id} removed: {reason}")

        # ── Pass 2: Xóa duplicate citations ──────────────────────────────
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

        # ── Pass 3: Xóa orphan nodes — bảo vệ core ───────────────────────
        # Recompute sau Pass 1 vì edges đã thay đổi
        valid_edges = self.graph_repo.get_graph(document_id).edges
        connected_node_ids = cited_node_ids | {
            e.from_node_id for e in valid_edges
            if e.from_node_id in node_ids and e.to_node_id in node_ids
        } | {
            e.to_node_id for e in valid_edges
            if e.from_node_id in node_ids and e.to_node_id in node_ids
        }

        for node in graph.nodes:
            if not is_allowed_node_type(node.type):
                self.graph_repo.delete_node(node.id)
                result.removed_orphan_nodes += 1
                result.audit_log.append(f"node '{node.label}' removed: invalid type {node.type}")
                continue

            if node.id not in connected_node_ids:
                if getattr(node, "importance", None) == "core":   # ← bảo vệ core
                    result.audit_log.append(
                        f"node '{node.label}' kept: orphan but importance=core"
                    )
                    continue
                self.graph_repo.delete_node(node.id)
                result.removed_orphan_nodes += 1
                result.audit_log.append(
                    f"node '{node.label}' removed: orphan, importance={getattr(node, 'importance', 'unknown')}"
                )

        return result