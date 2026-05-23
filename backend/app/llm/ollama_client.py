"""
Ollama LLM Client — wrapper around the local Ollama API via HTTPX.

Handles streaming and non-streaming completions for offline fallback.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, List, Dict, Optional

import httpx
from loguru import logger

from app.core.config import settings


class OllamaClient:
    """Wrapper around local Ollama API."""

    def __init__(self):
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        logger.info(f"Ollama client initialized (url={self._base_url}, model={self._model})")

    async def check_health(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self._base_url}/api/version", timeout=2.0)
                return resp.status_code == 200
        except Exception:
            return False

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Non-streaming completion."""
        target_model = model or self._model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                    timeout=120.0
                )
                resp.raise_for_status()
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                logger.debug(f"Ollama [{target_model}] → {len(content)} chars")
                return content
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Streaming completion — yields text chunks."""
        target_model = model or self._model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json=payload,
                    timeout=120.0
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                yield chunk
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"[Ollama Error: {e}]"
