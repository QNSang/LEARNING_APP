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
    extraction_model: str = Field(default="gemini-2.0-flash")
    upload_dir: Path = Field(default=Path("uploads"))
    chunk_size_chars: int = Field(default=3200, gt=0)
    chunk_overlap_chars: int = Field(default=400, ge=0)
    use_neo4j: bool = Field(default=False)
    neo4j_uri: str | None = Field(default=None)
    neo4j_user: str | None = Field(default=None)
    neo4j_password: str | None = Field(default=None)
    neo4j_database: str | None = Field(default=None)

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
        extraction_model=getenv("EXTRACTION_MODEL", "gemini-2.0-flash"),
        upload_dir=Path(getenv("UPLOAD_DIR", "uploads")),
        chunk_size_chars=int(getenv("CHUNK_SIZE_CHARS", "3200")),
        chunk_overlap_chars=int(getenv("CHUNK_OVERLAP_CHARS", "400")),
        use_neo4j=getenv("USE_NEO4J", "false").lower() in {"1", "true", "yes"},
        neo4j_uri=getenv("NEO4J_URI"),
        neo4j_user=getenv("NEO4J_USER"),
        neo4j_password=getenv("NEO4J_PASSWORD"),
        neo4j_database=getenv("NEO4J_DATABASE"),
    )
