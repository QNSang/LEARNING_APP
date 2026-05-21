"""Learning path generation service."""

from collections import defaultdict
from uuid import UUID

from app.core.errors import AppError
from app.db.repositories.graph_repo import GraphRepository
from app.db.repositories.learning_path_repo import LearningPathRepository
from app.models.graph import KnowledgeEdge, KnowledgeNode
from app.models.learning_path import (
    LearningPathCreate,
    LearningPathStepCreate,
    LearningPathWithSteps,
)


class LearningPathService:
    """Create a basic prerequisite-aware learning path."""

    def __init__(
        self,
        graph_repo: GraphRepository | None = None,
        path_repo: LearningPathRepository | None = None,
    ) -> None:
        self.graph_repo = graph_repo or GraphRepository()
        self.path_repo = path_repo or LearningPathRepository()

    def generate(
        self,
        *,
        document_id: UUID,
        user_id: UUID | None = None,
        goal: str | None = None,
    ) -> LearningPathWithSteps:
        graph = self.graph_repo.get_graph(document_id)
        if not graph.nodes:
            raise AppError("Document graph has no nodes.", status_code=400)

        ordered_nodes = order_nodes_for_learning(graph.nodes, graph.edges)
        path = self.path_repo.create(
            LearningPathCreate(
                user_id=user_id,
                document_id=document_id,
                goal=goal,
                title=goal or "Generated learning path",
                summary="A prerequisite-aware path generated from the document graph.",
            )
        )
        steps = self.path_repo.create_steps(
            [
                LearningPathStepCreate(
                    learning_path_id=path.id,
                    node_id=node.id,
                    step_index=index,
                    reason=reason_for_node(node),
                    estimated_minutes=estimated_minutes(node),
                )
                for index, node in enumerate(ordered_nodes)
            ]
        )
        return LearningPathWithSteps(path=path, steps=steps)

    def latest_for_document(
        self,
        *,
        document_id: UUID,
        user_id: UUID | None = None,
    ) -> LearningPathWithSteps | None:
        paths = self.path_repo.list_by_document(document_id, user_id=user_id)
        if not paths:
            return None
        return self.path_repo.get_with_steps(paths[0].id)


def order_nodes_for_learning(
    nodes: list[KnowledgeNode],
    edges: list[KnowledgeEdge],
) -> list[KnowledgeNode]:
    nodes_by_id = {node.id: node for node in nodes}
    prerequisite_count: dict[UUID, int] = defaultdict(int)
    dependents: dict[UUID, list[UUID]] = defaultdict(list)
    for edge in edges:
        if edge.edge_type != "requires":
            continue
        if edge.from_node_id not in nodes_by_id or edge.to_node_id not in nodes_by_id:
            continue
        prerequisite_count[edge.to_node_id] += 1
        dependents[edge.from_node_id].append(edge.to_node_id)

    ready = [
        node
        for node in nodes
        if prerequisite_count[node.id] == 0
    ]
    ready.sort(key=node_sort_key)
    ordered: list[KnowledgeNode] = []
    seen: set[UUID] = set()

    while ready:
        node = ready.pop(0)
        if node.id in seen:
            continue
        ordered.append(node)
        seen.add(node.id)
        for dependent_id in dependents[node.id]:
            prerequisite_count[dependent_id] -= 1
            if prerequisite_count[dependent_id] <= 0 and dependent_id not in seen:
                ready.append(nodes_by_id[dependent_id])
        ready.sort(key=node_sort_key)

    remaining = [node for node in nodes if node.id not in seen]
    remaining.sort(key=node_sort_key)
    return ordered + remaining


def node_sort_key(node: KnowledgeNode) -> tuple[int, int, str]:
    importance_rank = {"core": 0, "supporting": 1, "detail": 2}.get(
        node.importance,
        1,
    )
    difficulty = node.difficulty or 3
    return (importance_rank, difficulty, node.label.lower())


def reason_for_node(node: KnowledgeNode) -> str:
    if node.importance == "core":
        return "Core knowledge needed early in the path."
    if node.type == "example":
        return "Example used to make a concept concrete."
    if node.type == "exercise":
        return "Practice item used to check understanding."
    return "Supporting knowledge connected to the document graph."


def estimated_minutes(node: KnowledgeNode) -> int:
    if node.importance == "core":
        return 12
    if node.importance == "supporting":
        return 8
    return 5


def get_learning_path_service() -> LearningPathService:
    return LearningPathService()
