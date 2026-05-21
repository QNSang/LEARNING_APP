"""Knowledge node deduplication pipeline step."""

from collections import defaultdict
from uuid import UUID

from pydantic import BaseModel

from app.db.repositories.graph_repo import GraphRepository
from app.pipeline.validator import normalize_node_key


class DeduplicationResult(BaseModel):
    merged_nodes: int = 0
    rewired_edges: int = 0
    rewired_citations: int = 0


class GraphDeduplicator:
    """Merge obvious duplicate nodes inside one document graph."""

    def __init__(self, graph_repo: GraphRepository | None = None) -> None:
        self.graph_repo = graph_repo or GraphRepository()

    def deduplicate(self, document_id: UUID) -> DeduplicationResult:
        graph = self.graph_repo.get_graph(document_id)
        groups: dict[str, list] = defaultdict(list)
        for node in graph.nodes:
            key = normalize_node_key(node.term or node.label or node.node_key)
            groups[key or node.node_key].append(node)

        result = DeduplicationResult()
        for nodes in groups.values():
            if len(nodes) < 2:
                continue

            canonical = nodes[0]
            duplicate_ids = {node.id for node in nodes[1:]}
            canonical_chunk_ids = {
                citation.chunk_id
                for citation in graph.citations
                if citation.node_id == canonical.id
            }

            for citation in graph.citations:
                if citation.node_id in duplicate_ids:
                    if citation.chunk_id in canonical_chunk_ids:
                        self.graph_repo.delete_citation(citation.id)
                        continue
                    updated = self.graph_repo.update_citation_node(
                        citation.id,
                        canonical.id,
                    )
                    if updated is not None:
                        canonical_chunk_ids.add(updated.chunk_id)
                        result.rewired_citations += 1

            for edge in graph.edges:
                from_node_id = canonical.id if edge.from_node_id in duplicate_ids else None
                to_node_id = canonical.id if edge.to_node_id in duplicate_ids else None
                if from_node_id or to_node_id:
                    updated = self.graph_repo.update_edge_endpoint(
                        edge.id,
                        from_node_id=from_node_id,
                        to_node_id=to_node_id,
                    )
                    if updated is not None:
                        result.rewired_edges += 1

            for duplicate in nodes[1:]:
                self.graph_repo.delete_node(duplicate.id)
                result.merged_nodes += 1

        return result
