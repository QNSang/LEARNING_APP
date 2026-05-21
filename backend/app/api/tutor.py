"""GraphRAG tutor API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.retrieval.context_builder import (
    TutorContextBuilder,
    TutorSource,
    get_tutor_context_builder,
)
from app.services.ai_service import AIService, get_ai_service


router = APIRouter(prefix="/tutor", tags=["tutor"])


class TutorChatRequest(BaseModel):
    document_id: UUID
    question: str = Field(min_length=1)


class TutorChatResponse(BaseModel):
    answer: str
    sources: list[TutorSource]


@router.post("/chat", response_model=TutorChatResponse)
async def chat_with_tutor(
    payload: TutorChatRequest,
    context_builder: TutorContextBuilder = Depends(get_tutor_context_builder),
    ai_service: AIService = Depends(get_ai_service),
) -> TutorChatResponse:
    """Answer a question using only cited document context."""

    context = context_builder.build(
        document_id=payload.document_id,
        question=payload.question,
    )
    if not context.sources:
        return TutorChatResponse(
            answer=(
                "I could not find enough grounded context in this document to "
                "answer that question with citations."
            ),
            sources=[],
        )

    answer = ai_service.generate_text(build_tutor_prompt(context.question, context.context_text))
    return TutorChatResponse(answer=answer, sources=context.sources)


def build_tutor_prompt(question: str, context_text: str) -> str:
    return f"""
You are an AI learning tutor. Answer the student using only the provided sources.

Rules:
- Ground every factual claim in the sources.
- If the sources are insufficient, say what is missing.
- Be concise and instructional.
- Mention source numbers inline when useful, for example [Source 1].
- Do not invent facts beyond the provided context.

Question:
{question}

Sources:
{context_text}
""".strip()
