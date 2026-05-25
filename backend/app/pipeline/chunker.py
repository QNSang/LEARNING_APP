"""Chunk creation pipeline step."""

import re

from pydantic import BaseModel, Field

from app.core.errors import AppError
from app.pipeline.parser import ParsedPage


OVERLAP_SENTENCE_COUNT = 2
SENTENCE_END_RE = re.compile(r"(?<=[.!?;:。！？；：])\s+")


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
    """Create sentence-aware chunks while preserving source references."""

    if chunk_size_chars <= 0:
        raise AppError("Chunk size must be positive.", status_code=500)

    chunks: list[PreparedChunk] = []
    for page in pages:
        text = clean_text(page.content)
        if not text:
            continue

        page_chunks = chunk_page_text(
            text,
            chunk_size_chars=chunk_size_chars,
            overlap_sentence_count=OVERLAP_SENTENCE_COUNT,
        )
        for chunk_text in page_chunks:
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

    if not chunks:
        raise AppError("No chunks were created from the document.", status_code=400)

    return chunks


def clean_text(text: str) -> str:
    """Normalize raw parser output before chunking."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    lines = [line.strip() for line in normalized.split("\n")]
    cleaned_lines: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue
        cleaned_lines.append(line)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()


def split_paragraphs(text: str) -> list[str]:
    """Split text on blank lines while keeping paragraph text compact."""

    return [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]


def split_sentences(text: str) -> list[str]:
    """Split text into sentences with a lightweight punctuation heuristic."""

    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [sentence.strip() for sentence in SENTENCE_END_RE.split(normalized) if sentence.strip()]


def chunk_page_text(
    text: str,
    *,
    chunk_size_chars: int,
    overlap_sentence_count: int,
) -> list[str]:
    """Create chunks for one page without cutting across sentence boundaries."""

    chunks: list[str] = []
    current_units: list[str] = []

    def flush_current(*, keep_overlap: bool = True) -> None:
        nonlocal current_units
        chunk_text = join_units(current_units)
        if chunk_text:
            chunks.append(chunk_text)
        current_units = (
            get_overlap_units(current_units, overlap_sentence_count)
            if keep_overlap
            else []
        )

    for paragraph in split_paragraphs(text):
        paragraph_units = [paragraph]
        if len(paragraph) > chunk_size_chars:
            paragraph_units = split_sentences(paragraph) or [paragraph]

        for unit in paragraph_units:
            if len(unit) > chunk_size_chars:
                if current_units:
                    flush_current(keep_overlap=False)
                chunks.append(unit)
                current_units = []
                continue

            candidate_units = [*current_units, unit] if current_units else [unit]
            candidate_text = join_units(candidate_units)
            if current_units and len(candidate_text) > chunk_size_chars:
                flush_current()
                candidate_units = [*current_units, unit] if current_units else [unit]

            current_units = candidate_units

    if join_units(current_units):
        chunks.append(join_units(current_units))

    return deduplicate_adjacent_chunks(chunks)


def get_overlap_units(units: list[str], overlap_sentence_count: int) -> list[str]:
    """Return the trailing sentences used as context for the next chunk."""

    if overlap_sentence_count <= 0:
        return []

    sentences: list[str] = []
    for unit in units:
        sentences.extend(split_sentences(unit) or [unit])
    return sentences[-overlap_sentence_count:]


def join_units(units: list[str]) -> str:
    """Join paragraphs or sentences into chunk text."""

    return "\n\n".join(unit.strip() for unit in units if unit.strip()).strip()


def deduplicate_adjacent_chunks(chunks: list[str]) -> list[str]:
    """Drop accidental duplicate chunks caused by overlap-only flushes."""

    deduplicated: list[str] = []
    for chunk in chunks:
        if not deduplicated or deduplicated[-1] != chunk:
            deduplicated.append(chunk)
    return deduplicated


def estimate_token_count(text: str) -> int:
    """Cheap token estimate used until the tokenizer step is introduced."""

    return max(1, len(text.split()))
