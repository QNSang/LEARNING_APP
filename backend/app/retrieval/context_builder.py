"""Tutor context builder."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.retrieval.hybrid_retriever import HybridRetriever, RetrievalHit


class TutorSource(BaseModel):
    chunk_id: UUID
    node_id: UUID
    node_label: str
    source_ref: str | None = None
    evidence: str | None = None
    score: float = Field(ge=0)


class TutorContext(BaseModel):
    document_id: UUID
    question: str
    context_text: str
    sources: list[TutorSource]


class TutorContextBuilder:
    """Build grounded tutor context from retrieval hits."""

    def __init__(self, retriever: HybridRetriever | None = None) -> None:
        self.retriever = retriever or HybridRetriever()

    def build(
        self,
        *,
        document_id: UUID,
        question: str,
        limit: int = 6,
    ) -> TutorContext:
        hits = self.retriever.retrieve(
            document_id=document_id,
            query=question,
            limit=limit,
        )
        sources = [source_from_hit(hit) for hit in hits]
        context_text = "\n\n".join(format_hit(index, hit) for index, hit in enumerate(hits, start=1))
        return TutorContext(
            document_id=document_id,
            question=question,
            context_text=context_text,
            sources=sources,
        )


def source_from_hit(hit: RetrievalHit) -> TutorSource:
    return TutorSource(
        chunk_id=hit.chunk.id,
        node_id=hit.node.id,
        node_label=hit.node.label,
        source_ref=hit.citation.source_ref or hit.chunk.source_ref,
        evidence=hit.citation.evidence,
        score=round(hit.score, 3),
    )


def format_hit(index: int, hit: RetrievalHit) -> str:
    return "\n".join(
        [
            f"[Source {index}]",
            f"Node: {hit.node.label} ({hit.node.type})",
            f"Source ref: {hit.citation.source_ref or hit.chunk.source_ref or 'unknown'}",
            f"Evidence: {hit.citation.evidence or 'No evidence stored.'}",
            f"Chunk: {hit.chunk.text[:1400]}",
        ]
    )


def get_tutor_context_builder() -> TutorContextBuilder:
    return TutorContextBuilder()
