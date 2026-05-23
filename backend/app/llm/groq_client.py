"""
Groq LLM Client — thin wrapper around the Groq SDK.

Handles streaming and non-streaming completions with retry logic.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, List, Dict, Optional

from groq import Groq, APIError, RateLimitError
from loguru import logger

from app.core.config import settings


class GroqClient:
    """Wrapper around the Groq SDK for chat completions."""

    def __init__(self):
        if not settings.has_groq:
            raise ValueError("GROQ_API_KEY is not set. Please configure it in .env")
        self._client = Groq(api_key=settings.groq_api_key)
        logger.info("Groq client initialized")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Non-streaming completion. Runs sync Groq call in a thread."""
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            content = response.choices[0].message.content or ""
            logger.debug(f"Groq [{model}] → {len(content)} chars")
            return content

        except RateLimitError as e:
            logger.warning(f"Groq rate limit hit: {e}. Retrying in 2s...")
            await asyncio.sleep(2)
            return await self.complete(messages, model, temperature, max_tokens)

        except APIError as e:
            logger.error(f"Groq API error: {e}")
            raise

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Streaming completion — yields text chunks."""
        try:
            # Run the blocking stream creation in a thread
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Iterate over the sync stream in a thread-safe way
            def _iter_chunks():
                chunks = []
                for chunk in response:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        chunks.append(delta)
                return chunks

            chunks = await asyncio.to_thread(_iter_chunks)
            for chunk_text in chunks:
                yield chunk_text

        except RateLimitError as e:
            logger.warning(f"Groq rate limit during stream: {e}")
            yield "[Rate limited — please retry]"

        except APIError as e:
            logger.error(f"Groq API error during stream: {e}")
            yield f"[Error: {e}]"

    def list_models(self) -> list:
        """List available models on Groq."""
        try:
            models = self._client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            logger.error(f"Failed to list Groq models: {e}")
            return []
