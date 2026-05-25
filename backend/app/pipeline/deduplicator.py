"""Knowledge node deduplication pipeline step."""

from collections import defaultdict
from uuid import UUID

from pydantic import BaseModel

from app.db.repositories.graph_repo import GraphRepository
from app.pipeline.validator import normalize_node_key


IMPORTANCE_SCORE = {"core": 3, "supporting": 2, "detail": 1}


class DeduplicationResult(BaseModel):
    merged_nodes: int = 0
    rewired_edges: int = 0
    rewired_citations: int = 0


class GraphDeduplicator:
    """Merge duplicate nodes inside one document graph."""

    def __init__(self, graph_repo: GraphRepository | None = None) -> None:
        self.graph_repo = graph_repo or GraphRepository()

    def _pick_canonical(self, nodes: list) -> object:
        return max(
            nodes,
            key=lambda n: (
                IMPORTANCE_SCORE.get(n.importance, 0),
                len(n.description or ""),
                len(n.term or ""),
                len(n.label or ""),
            ),
        )

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

            canonical = self._pick_canonical(nodes)
            duplicates = [n for n in nodes if n.id != canonical.id]
            duplicate_ids = {n.id for n in duplicates}

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

            edge_targets = []
            for edge in graph.edges:
                new_from = canonical.id if edge.from_node_id in duplicate_ids else edge.from_node_id
                new_to = canonical.id if edge.to_node_id in duplicate_ids else edge.to_node_id
                changed = new_from != edge.from_node_id or new_to != edge.to_node_id
                key = None
                if new_from != new_to:
                    key = (edge.document_id, new_from, new_to, edge.edge_type)
                edge_targets.append((edge, new_from, new_to, changed, key))

            keep_edge_ids = {}
            keep_edge_is_changed = {}
            for edge, _, _, changed, key in edge_targets:
                if key is None:
                    continue
                if key not in keep_edge_ids or (
                    keep_edge_is_changed[key] and not changed
                ):
                    keep_edge_ids[key] = edge.id
                    keep_edge_is_changed[key] = changed

            for edge, new_from, new_to, changed, key in edge_targets:
                if key is None:
                    self.graph_repo.delete_edge(edge.id)
                    continue

                if keep_edge_ids[key] != edge.id:
                    self.graph_repo.delete_edge(edge.id)
                    continue

                if changed:
                    updated = self.graph_repo.update_edge_endpoint(
                        edge.id,
                        from_node_id=new_from if new_from != edge.from_node_id else None,
                        to_node_id=new_to if new_to != edge.to_node_id else None,
                    )
                    if updated is not None:
                        result.rewired_edges += 1

            for duplicate in duplicates:
                self.graph_repo.delete_node(duplicate.id)
                result.merged_nodes += 1

        return result
