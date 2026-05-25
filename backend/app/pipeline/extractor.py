"""Learning graph extraction pipeline step."""

import json
import logging
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

# Khởi tạo logger để theo dõi luồng extraction
logger = logging.getLogger(__name__)

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
    """Extract learning graph candidates from chunks using an AI Service with retry mechanisms."""

    def __init__(self, ai_service: AIService | None = None) -> None:
        self.ai_service = ai_service or AIService()

    def extract_chunk(
        self, 
        chunk: Chunk, 
        existing_node_keys: list[str] | None = None,
        max_retries: int = 2
    ) -> ExtractedGraphChunk:
        """
        Thực thi trích xuất với cơ chế Retry. Nếu LLM trả về JSON lỗi,
        hệ thống sẽ tự động gọi lại tối đa `max_retries` lần.
        """
        prompt = build_extraction_prompt(chunk, existing_node_keys)
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Gọi AI Service
                raw = self.ai_service.generate_json(prompt)
                
                # Parse và Validate bằng Pydantic
                parsed = ExtractedGraphChunk.model_validate(raw)
                
                # Normalize Nodes
                nodes = [normalize_extracted_node(node) for node in parsed.nodes]
                node_keys = {node.node_key for node in nodes}
                
                # Normalize & Filter Edges (Chỉ giữ lại Edge nếu 2 Node ở 2 đầu đều hợp lệ)
                valid_edges = []
                for edge in parsed.edges:
                    if not edge.from_node_key or not edge.to_node_key:
                        continue
                        
                    norm_edge = normalize_extracted_edge(edge)
                    if norm_edge.from_node_key in node_keys and norm_edge.to_node_key in node_keys:
                        valid_edges.append(norm_edge)
                
                logger.info(f"Chunk extracted successfully. Nodes: {len(nodes)}, Edges: {len(valid_edges)}")
                return ExtractedGraphChunk(nodes=nodes, edges=valid_edges)

            except (ValidationError, AppError, ValueError) as exc:
                last_exception = exc
                logger.warning(
                    f"Extraction attempt {attempt + 1}/{max_retries + 1} failed for chunk {chunk.id}. "
                    f"Error: {str(exc)}"
                )
                continue # Thử lại ở vòng lặp tiếp theo

        # Nếu vượt quá số lần retry mà vẫn lỗi, raise AppError
        logger.error(f"Failed to extract chunk {chunk.id} after {max_retries + 1} attempts.")
        raise AppError("AI graph response did not match schema after retries.", status_code=502) from last_exception


def normalize_extracted_node(node: ExtractedNode) -> ExtractedNode:
    """Chuẩn hóa khóa và kiểm tra tính hợp lệ của Node."""
    node_key = normalize_node_key(node.node_key or node.label)
    if not node_key:
        node_key = normalize_node_key(node.label)
        
    if not is_allowed_node_type(node.type):
        raise AppError(f"Unsupported node type: {node.type}", status_code=502)
        
    return node.model_copy(update={"node_key": node_key})


def normalize_extracted_edge(edge: ExtractedEdge) -> ExtractedEdge:
    """Chuẩn hóa khóa và kiểm tra tính hợp lệ của Edge."""
    if not is_allowed_edge_type(edge.edge_type):
        raise AppError(f"Unsupported edge type: {edge.edge_type}", status_code=502)
        
    return edge.model_copy(
        update={
            "from_node_key": normalize_node_key(edge.from_node_key),
            "to_node_key": normalize_node_key(edge.to_node_key),
        }
    )


def build_extraction_prompt(chunk: Chunk, existing_node_keys: list[str] | None = None) -> str:
    """
    Build a highly strict, production-ready, domain-agnostic learning graph extraction prompt.
    """
    
    existing_keys_json = json.dumps(existing_node_keys[:40]) if existing_node_keys else "[]"

    return f"""
You are a Master Educational Architect, Expert Knowledge Engineer and Ontologist. 
Your task is to extract a highly precise, unified Knowledge Graph from the provided educational text, regardless of the subject matter.
Return ONLY a valid JSON object. Do NOT wrap the JSON in markdown formatting blocks (e.g., no ```json).

## OUTPUT SCHEMA (JSON)
{{
  "nodes": [
    {{
      "node_key": "Canonical_Capitalized_Name",
      "label": "Human readable label",
      "type": "concept|fact|procedure|formula|example|misconception|learning_objective|exercise",
      "description": "Short explanation deeply grounded in the text",
      "importance": "core|supporting|detail",
      "difficulty": 1,
      "evidence": "EXACT quote from the chunk as proof",
      "confidence": 0.8
    }}
  ],
  "edges": [
    {{
      "from_node_key": "Source_node_key",
      "to_node_key": "Target_node_key",
      "edge_type": "requires|explains|part_of|example_of|applies_to|contrasts_with|causes|leads_to|tested_by|misconception_of",
      "reason": "Why this relation is grounded in the text",
      "confidence": 0.8
    }}
  ]
}}

## CORE DIRECTIVES (Zero-Hallucination Policy)

1. THE ESCAPE HATCH: If the text contains ONLY filler, table of contents, acknowledgments, or uninformative content, return EMPTY arrays for both nodes and edges. DO NOT force extraction.
2. NODE CONSOLIDATION: Do NOT create nodes for isolated facts or attributes. 
   - BAD: Node("Has High Velocity")
   - GOOD: Node("Kinematics") with the velocity rule in its `description`.
3. CANONICAL NAMING: Use the full, canonical, natural-language form for keys (e.g., "Latent Semantic Analysis", NOT "lsa"). Ensure naming fits the subject matter context.
4. BUDGET: Maximum 8 nodes (core ≤ 3, supporting ≤ 3, detail ≤ 2) and 10 edges per chunk.
5. CONFIDENCE LIMIT: Skip nodes < 0.5, skip edges < 0.6.
6. NO DANGLING EDGES: You may ONLY create an edge if BOTH `from_node_key` and `to_node_key` are explicitly defined in the `nodes` array of your current response.

## EXISTING KNOWLEDGE CONTEXT
To prevent duplication, favor using these existing concept keys if they perfectly match the text's meaning:
{existing_keys_json}

## SOURCE MATERIAL
Source Reference: {chunk.source_ref or "Unknown"}
Chunk text to analyze:
<text>
{chunk.text}
</text>
""".strip()


def get_graph_extractor() -> GraphExtractor:
    return GraphExtractor()