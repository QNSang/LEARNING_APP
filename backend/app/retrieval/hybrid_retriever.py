"""Hybrid retrieval mode."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.db.repositories.chunk_repo import ChunkRepository
from app.db.repositories.graph_repo import GraphRepository
from app.models.chunk import Chunk
from app.models.graph import KnowledgeNode, NodeChunkRef


class RetrievalHit(BaseModel):
    node: KnowledgeNode
    citation: NodeChunkRef
    chunk: Chunk
    score: float = Field(ge=0)


class HybridRetriever:
    """MVP retrieval using graph citations plus keyword scoring."""

    def __init__(
        self,
        graph_repo: GraphRepository | None = None,
        chunk_repo: ChunkRepository | None = None,
    ) -> None:
        self.graph_repo = graph_repo or GraphRepository()
        self.chunk_repo = chunk_repo or ChunkRepository()

    def retrieve(
        self,
        *,
        document_id: UUID,
        query: str,
        limit: int = 6,
    ) -> list[RetrievalHit]:
        graph = self.graph_repo.get_graph(document_id)
        chunks = self.chunk_repo.get_many(
            list({citation.chunk_id for citation in graph.citations})
        )
        chunks_by_id = {chunk.id: chunk for chunk in chunks}
        nodes_by_id = {node.id: node for node in graph.nodes}
        query_terms = tokenize(query)

        hits: list[RetrievalHit] = []
        for citation in graph.citations:
            node = nodes_by_id.get(citation.node_id)
            chunk = chunks_by_id.get(citation.chunk_id)
            if node is None or chunk is None:
                continue

            haystack = " ".join(
                [
                    node.label,
                    node.description or "",
                    citation.evidence or "",
                    chunk.text,
                ]
            )
            score = keyword_score(query_terms, haystack)
            if score <= 0:
                continue
            hits.append(
                RetrievalHit(
                    node=node,
                    citation=citation,
                    chunk=chunk,
                    score=score,
                )
            )

        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:limit]


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in "".join(
            char.lower() if char.isalnum() else " " for char in value
        ).split()
        if len(token) >= 3
    }


def keyword_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0
    text_terms = tokenize(text)
    overlap = query_terms & text_terms
    if not overlap:
        return 0
    return len(overlap) / len(query_terms)


def get_hybrid_retriever() -> HybridRetriever:
    return HybridRetriever()
