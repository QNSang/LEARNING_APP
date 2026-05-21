"""Shared repository helpers."""

from typing import Any

from pydantic import BaseModel

from app.core.errors import AppError


def to_record(model: BaseModel, *, exclude_none: bool = True) -> dict[str, Any]:
    """Convert a Pydantic model into a JSON-safe database record."""

    return model.model_dump(mode="json", exclude_none=exclude_none)


def first_or_none(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the first Supabase row from a response payload."""

    return rows[0] if rows else None


def execute_query(query: Any) -> Any:
    """Execute a Supabase query and normalize connection failures."""

    try:
        return query.execute()
    except AppError:
        raise
    except Exception as exc:
        raise AppError("Database request failed.", status_code=503) from exc
