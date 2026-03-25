import os
import asyncio
from typing import Optional
from google import genai
from google.genai import types
import structlog

logger = structlog.get_logger()


class GeminiClient:

    def __init__(self,
                 api_key: Optional[str] = None,
                 model_name: str = "gemini-2.5-flash"):

        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate_content(
        self,
        prompt: str,
        is_json: bool = False,
        max_retries: int = 5
    ) -> str:

        config = None
        if is_json:
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )

                if not response.candidates:
                    raise ValueError("Empty Gemini response")

                return response.text

            except Exception as e:
                error_msg = str(e).lower()

                retryable = any(
                    k in error_msg for k in
                    ["429", "timeout", "unavailable", "500"]
                )

                if not retryable or attempt == max_retries:
                    logger.error("gemini_failed", error=error_msg)
                    raise

                wait_time = 90 if "429" in error_msg else 2 ** attempt
                logger.warning("retrying", wait=wait_time)

                await asyncio.sleep(wait_time)