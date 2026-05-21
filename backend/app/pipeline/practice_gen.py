"""Practice generation pipeline step."""

from uuid import UUID

from pydantic import BaseModel

from app.db.repositories.graph_repo import GraphRepository
from app.db.repositories.practice_repo import PracticeRepository
from app.models.graph import KnowledgeNode, NodeChunkRef
from app.models.practice import PracticeItem, PracticeItemCreate


class PracticeGenerationResult(BaseModel):
    document_id: UUID
    created_count: int
    items: list[PracticeItem]


class PracticeGenerator:
    """Generate simple grounded practice items from graph nodes."""

    def __init__(
        self,
        graph_repo: GraphRepository | None = None,
        practice_repo: PracticeRepository | None = None,
    ) -> None:
        self.graph_repo = graph_repo or GraphRepository()
        self.practice_repo = practice_repo or PracticeRepository()

    def generate_for_document(self, document_id: UUID) -> PracticeGenerationResult:
        graph = self.graph_repo.get_graph(document_id)
        existing = self.practice_repo.list_by_document(document_id)
        existing_node_ids = {item.node_id for item in existing}
        citations_by_node = first_citation_by_node(graph.citations)

        payloads: list[PracticeItemCreate] = []
        for node in graph.nodes:
            if node.id in existing_node_ids:
                continue
            citation = citations_by_node.get(node.id)
            payloads.extend(practice_payloads_for_node(document_id, node, citation))

        items = self.practice_repo.create_items(payloads)
        return PracticeGenerationResult(
            document_id=document_id,
            created_count=len(items),
            items=items,
        )


def first_citation_by_node(citations: list[NodeChunkRef]) -> dict[UUID, NodeChunkRef]:
    result: dict[UUID, NodeChunkRef] = {}
    for citation in citations:
        result.setdefault(citation.node_id, citation)
    return result


def practice_payloads_for_node(
    document_id: UUID,
    node: KnowledgeNode,
    citation: NodeChunkRef | None,
) -> list[PracticeItemCreate]:
    answer = node.description or citation.evidence or node.label
    source_ref = citation.source_ref if citation else None
    difficulty = node.difficulty or default_difficulty(node.importance)
    items = [
        PracticeItemCreate(
            node_id=node.id,
            document_id=document_id,
            type="flashcard",
            question=f"What is {node.label}?",
            answer=answer,
            explanation=citation.evidence if citation else node.description,
            source_ref=source_ref,
            difficulty=difficulty,
        ),
        PracticeItemCreate(
            node_id=node.id,
            document_id=document_id,
            type="explain",
            question=f"Explain {node.label} in your own words.",
            answer=answer,
            explanation="Compare your explanation with the source evidence.",
            source_ref=source_ref,
            difficulty=difficulty,
        ),
    ]
    if node.type in {"procedure", "formula", "concept"}:
        items.append(
            PracticeItemCreate(
                node_id=node.id,
                document_id=document_id,
                type="short_answer",
                question=f"Why is {node.label} important in this material?",
                answer=answer,
                explanation=citation.evidence if citation else node.description,
                source_ref=source_ref,
                difficulty=difficulty,
            )
        )
    return items


def default_difficulty(importance: str) -> int:
    if importance == "core":
        return 3
    if importance == "supporting":
        return 2
    return 1


def get_practice_generator() -> PracticeGenerator:
    return PracticeGenerator()
