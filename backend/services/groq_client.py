import os
import asyncio
from groq import AsyncGroq
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()

class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama-3.3-70b-versatile"):
        api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment. Get one for free at console.groq.com")
        
        self.client = AsyncGroq(api_key=api_key)
        self.model_name = model_name

    async def generate_content(self, prompt: str, is_json: bool = False, max_retries: int = 3) -> str:
        """
        Call Groq with retry logic and optional JSON enforcement.
        """
        for attempt in range(max_retries + 1):
            try:
                params = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1, # Lower temperature for better structural consistency
                }
                
                if is_json:
                    params["response_format"] = {"type": "json_object"}

                completion = await self.client.chat.completions.create(**params)
                
                res = completion.choices[0].message.content
                if not res:
                    raise ValueError("Groq returned an empty response")
                
                return res
                
            except Exception as e:
                error_msg = str(e)
                if attempt == max_retries:
                    logger.error("groq_call_failed_final", error=error_msg, prompt_preview=prompt[:100])
                    raise
                
                wait_time = (2 ** attempt) + 2
                logger.warn("groq_call_retry", error=error_msg[:100], attempt=attempt + 1, wait_time=wait_time)
                await asyncio.sleep(wait_time)
        
        return ""
