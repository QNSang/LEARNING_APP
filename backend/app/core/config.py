"""Application settings loaded from environment variables."""

from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv()


class Settings(BaseModel):
    """Runtime settings for the API application."""

    app_name: str = Field(default="AI Learning OS")
    environment: str = Field(default="development")
    api_prefix: str = Field(default="/api")
    frontend_origin: str = Field(default="http://localhost:3000")
    supabase_url: str | None = Field(default=None)
    supabase_key: str | None = Field(default=None)
    supabase_service_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    upload_dir: Path = Field(default=Path("uploads"))
    chunk_size_chars: int = Field(default=3200, gt=0)
    chunk_overlap_chars: int = Field(default=400, ge=0)

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origin.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings(
        app_name=getenv("APP_NAME", "AI Learning OS"),
        environment=getenv("ENVIRONMENT", "development"),
        api_prefix=getenv("API_PREFIX", "/api"),
        frontend_origin=getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
        supabase_url=getenv("SUPABASE_URL"),
        supabase_key=getenv("SUPABASE_KEY") or getenv("SUPABASE_SERVICE_KEY"),
        supabase_service_key=getenv("SUPABASE_SERVICE_KEY"),
        gemini_api_key=getenv("GEMINI_API_KEY"),
        upload_dir=Path(getenv("UPLOAD_DIR", "uploads")),
        chunk_size_chars=int(getenv("CHUNK_SIZE_CHARS", "3200")),
        chunk_overlap_chars=int(getenv("CHUNK_OVERLAP_CHARS", "400")),
    )
