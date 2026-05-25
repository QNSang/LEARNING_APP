"""Learning graph extraction pipeline step."""

from pydantic import BaseModel, Field, ValidationError

from app.core.errors import AppError
from app.models.chunk import Chunk
from app.models.graph import EdgeType, NodeImportance, NodeType
from app.pipeline.validator import (
    is_allowed_edge_type,
    is_allowed_node_type,
    normalize_node_key,
)
from app.services.ai_service import AIService


class ExtractedNode(BaseModel):
    node_key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    type: NodeType
    description: str | None = None
    importance: NodeImportance = "supporting"
    difficulty: int | None = Field(default=None, ge=1, le=5)
    evidence: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class ExtractedEdge(BaseModel):
    from_node_key: str = Field(min_length=1)
    to_node_key: str = Field(min_length=1)
    edge_type: EdgeType
    reason: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class ExtractedGraphChunk(BaseModel):
    nodes: list[ExtractedNode] = Field(default_factory=list)
    edges: list[ExtractedEdge] = Field(default_factory=list)


class GraphExtractor:
    """Extract learning graph candidates from chunks using Gemini."""

    def __init__(self, ai_service: AIService | None = None) -> None:
        self.ai_service = ai_service or AIService()

    def extract_chunk(self, chunk: Chunk) -> ExtractedGraphChunk:
        raw = self.ai_service.generate_json(build_extraction_prompt(chunk))
        try:
            parsed = ExtractedGraphChunk.model_validate(raw)
        except ValidationError as exc:
            raise AppError("Gemini graph response did not match schema.", 502) from exc

        nodes = [normalize_extracted_node(node) for node in parsed.nodes]
        node_keys = {node.node_key for node in nodes}
        edges = [
            normalize_extracted_edge(edge)
            for edge in parsed.edges
            if edge.from_node_key and edge.to_node_key
        ]
        edges = [
            edge
            for edge in edges
            if edge.from_node_key in node_keys and edge.to_node_key in node_keys
        ]
        return ExtractedGraphChunk(nodes=nodes, edges=edges)


def normalize_extracted_node(node: ExtractedNode) -> ExtractedNode:
    node_key = normalize_node_key(node.node_key or node.label)
    if not node_key:
        node_key = normalize_node_key(node.label)
    if not is_allowed_node_type(node.type):
        raise AppError(f"Unsupported node type: {node.type}", status_code=502)
    return node.model_copy(update={"node_key": node_key})


def normalize_extracted_edge(edge: ExtractedEdge) -> ExtractedEdge:
    if not is_allowed_edge_type(edge.edge_type):
        raise AppError(f"Unsupported edge type: {edge.edge_type}", status_code=502)
    return edge.model_copy(
        update={
            "from_node_key": normalize_node_key(edge.from_node_key),
            "to_node_key": normalize_node_key(edge.to_node_key),
        }
    )


def build_extraction_prompt(chunk: Chunk, existing_node_keys: list[str] | None = None) -> str:
    """Build a strict learning graph extraction prompt for one chunk."""

    return f"""
You extract a learning graph from source text.
Return only valid JSON with this shape:
{{
  "nodes": [
    {{
      "node_key": "stable_snake_case_key",
      "label": "Human readable label",
      "type": "concept|fact|procedure|formula|example|misconception|learning_objective|exercise",
      "description": "short explanation grounded in the text",
      "importance": "core|supporting|detail",
      "difficulty": 1,
      "evidence": "short quote or paraphrase from the chunk",
      "confidence": 0.8
    }}
  ],
  "edges": [
    {{
      "from_node_key": "source_node_key",
      "to_node_key": "target_node_key",
      "edge_type": "requires|explains|part_of|example_of|applies_to|contrasts_with|causes|leads_to|tested_by|misconception_of",
      "reason": "why this relation is grounded in the text",
      "confidence": 0.8
    }}
  ]
}}

Rules:

- BEFORE creating a node, ask yourself:
  * Can this concept exist independently of its parent?
  * Is it referenced by more than one other concept?
  * Does it have its own prerequisites or applications?
  If NO to all → put it in the parent node's description, NOT a new node.

- NEVER create nodes for:
  * Properties or characteristics of a concept ("has binary values", "fixed size")
  * Simple illustrative examples with no standalone meaning
  * Facts that only make sense attached to one specific parent

- BUDGET: core ≤ 3, supporting ≤ 3, detail ≤ 2 per chunk.
- KEYS: use full form as canonical key (latent_semantic_analysis not lsa).
- CONFIDENCE: skip nodes < 0.5, skip edges < 0.6.
- Use only the allowed type strings.
- Extract at most 8 nodes and 10 edges.
- Every node must include evidence from the chunk.
- Only create edges between nodes returned in this JSON.
- Prefer learning relationships: requires, explains, part_of, example_of, tested_by.
- EXISTING KEYS: reuse exact key if concept already exists: {", ".join(existing_node_keys[:40]) if existing_node_keys else "none yet"}

Source reference: {chunk.source_ref or "unknown source"}
Chunk text:
\"\"\"
{chunk.text}
\"\"\"
""".strip()


def get_graph_extractor() -> GraphExtractor:
    return GraphExtractor()
