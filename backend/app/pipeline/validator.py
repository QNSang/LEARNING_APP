"""Graph validation pipeline step."""

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
