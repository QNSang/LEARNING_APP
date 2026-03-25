from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class KnowledgeNode(BaseModel):
    id: str = Field(..., description="snake_case, unique ID. e.g., 'gradient_descent'")
    label: str = Field(..., description="Display name. e.g., 'Gradient Descent'")
    type: Literal["concept", "procedure", "fact"]
    chunk_index: int = Field(..., description="Order of appearance in document (0, 1, 2...)")
    source_ref: str = Field(..., description="Source citation. e.g., 'Page 2', 'Slide 15'")
    importance: Literal["core", "supporting", "detail"]

class KnowledgeEdge(BaseModel):
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    type: Literal["requires", "part_of", "explains", "related_to"]

    class Config:
        populate_by_name = True

class KnowledgeGraph(BaseModel):
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]

class NodeExplanation(BaseModel):
    intuition: str
    applications: List[str]
    position: str

class EssayGrade(BaseModel):
    accuracy: int
    completeness: int
    own_words: int
    example_quality: int

class EssayGradingResult(BaseModel):
    scores: EssayGrade
    total: int
    feedback: str
    errors: List[str]
    missing_concepts: List[str]
