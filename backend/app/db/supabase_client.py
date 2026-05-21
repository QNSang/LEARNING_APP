"""Supabase client factory for the rebuilt backend layout."""

from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.errors import AppError


@lru_cache
def get_supabase_client() -> Any:
    """Return a cached Supabase client.

    The import is intentionally lazy so local API health checks can run before
    database dependencies or credentials are configured.
    """

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise AppError("Supabase is not configured.", status_code=503)

    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_key)
