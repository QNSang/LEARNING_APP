"""Chunk creation pipeline step."""

from pydantic import BaseModel, Field

from app.core.errors import AppError
from app.pipeline.parser import ParsedPage


class PreparedChunk(BaseModel):
    chunk_index: int = Field(ge=0)
    text: str
    token_count: int | None = Field(default=None, ge=0)
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    source_ref: str | None = None


def create_chunks(
    pages: list[ParsedPage],
    *,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
) -> list[PreparedChunk]:
    """Create overlapping text chunks while preserving source references."""

    if chunk_overlap_chars >= chunk_size_chars:
        raise AppError("Chunk overlap must be smaller than chunk size.", status_code=500)

    chunks: list[PreparedChunk] = []
    for page in pages:
        start = 0
        text = page.content
        while start < len(text):
            end = min(start + chunk_size_chars, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    PreparedChunk(
                        chunk_index=len(chunks),
                        text=chunk_text,
                        token_count=estimate_token_count(chunk_text),
                        page_start=page.page_num,
                        page_end=page.page_num,
                        source_ref=page.source_ref,
                    )
                )
            if end >= len(text):
                break
            start = end - chunk_overlap_chars

    if not chunks:
        raise AppError("No chunks were created from the document.", status_code=400)

    return chunks


def estimate_token_count(text: str) -> int:
    """Cheap token estimate used until the tokenizer step is introduced."""

    return max(1, len(text.split()))
