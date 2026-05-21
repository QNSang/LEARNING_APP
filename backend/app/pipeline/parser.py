"""Document parsing pipeline step."""

from pathlib import Path
from typing import Literal

import fitz
from pydantic import BaseModel, Field

from app.core.errors import AppError


SupportedSource = Literal["pdf", "txt"]


class ParsedPage(BaseModel):
    page_num: int = Field(ge=1)
    content: str
    source: SupportedSource
    file_name: str
    source_ref: str


def parse_document(file_path: Path) -> list[ParsedPage]:
    """Parse a supported document into page-like text units."""

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    if suffix == ".txt":
        return parse_txt(file_path)

    raise AppError(
        "Unsupported file type. Phase 3 supports PDF and TXT.",
        status_code=400,
    )


def parse_txt(file_path: Path) -> list[ParsedPage]:
    text = file_path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise AppError("Document has no readable text.", status_code=400)

    return [
        ParsedPage(
            page_num=1,
            content=text,
            source="txt",
            file_name=file_path.name,
            source_ref=f"{file_path.name} - text",
        )
    ]


def parse_pdf(file_path: Path) -> list[ParsedPage]:
    pages: list[ParsedPage] = []
    with fitz.open(file_path) as document:
        for index, page in enumerate(document, start=1):
            content = page.get_text("text").strip()
            if not content:
                continue
            pages.append(
                ParsedPage(
                    page_num=index,
                    content=content,
                    source="pdf",
                    file_name=file_path.name,
                    source_ref=f"{file_path.name} - page {index}",
                )
            )

    if not pages:
        raise AppError("Document has no readable text.", status_code=400)

    return pages
