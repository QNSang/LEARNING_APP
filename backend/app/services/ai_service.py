"""LLM provider router with cache, retry, and fallback."""

import json
from typing import Any

from app.core.config import get_settings
from app.core.errors import AppError


class AIService:
    """Small Gemini-backed AI service used by the extraction pipeline."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_json(self, prompt: str) -> dict[str, Any]:
        """Generate a JSON object from Gemini and parse it strictly."""

        response = self._generate_content(
            prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        )
        text = response.text or ""

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AppError("Gemini returned invalid JSON.", status_code=502) from exc

        if not isinstance(parsed, dict):
            raise AppError("Gemini JSON response must be an object.", status_code=502)
        return parsed

    def generate_text(self, prompt: str) -> str:
        """Generate plain text from Gemini."""

        response = self._generate_content(
            prompt,
            config={
                "temperature": 0.2,
            },
        )
        text = (response.text or "").strip()
        if not text:
            raise AppError("Gemini returned an empty answer.", status_code=502)
        return text

    def _generate_content(self, prompt: str, config: dict[str, Any]) -> Any:
        if not self.settings.gemini_api_key:
            raise AppError("GEMINI_API_KEY is not configured.", status_code=503)

        try:
            from google import genai
        except ImportError as exc:
            raise AppError("google-genai is not installed.", status_code=500) from exc

        client = genai.Client(api_key=self.settings.gemini_api_key)
        return client.models.generate_content(
            model=self.settings.extraction_model,
            contents=prompt,
            config=config,
        )


def get_ai_service() -> AIService:
    return AIService()
