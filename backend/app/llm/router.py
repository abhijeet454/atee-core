"""
LLM Router — routes requests to the appropriate model based on complexity.

Strategy:
  - Simple/fast queries → Groq small model (llama-3.1-8b-instant)
  - Complex reasoning   → Groq power model (llama-3.3-70b-versatile)
"""

from __future__ import annotations

from enum import Enum
from typing import AsyncGenerator, List, Dict, Optional

from loguru import logger

from app.core.config import settings
from app.llm.groq_client import GroqClient
from app.llm.ollama_client import OllamaClient


class Complexity(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"


# Keywords / patterns that suggest a complex query
_COMPLEX_SIGNALS = [
    "explain", "analyze", "compare", "debate", "write an essay",
    "step by step", "in detail", "pros and cons", "trade-offs",
    "implement", "design", "architect", "refactor", "debug",
    "summarize this document", "create a plan", "help me think",
    "what are the implications", "how would you approach",
]


class LLMRouter:
    """Routes LLM requests to the best-fit model based on query complexity."""

    def __init__(self):
        self._has_groq = settings.has_groq
        if self._has_groq:
            self._groq = GroqClient()
        self._ollama = OllamaClient()
        self._fast_model = settings.groq_fast_model
        self._power_model = settings.groq_power_model
        self._local_model = settings.ollama_model
        logger.info(
            f"LLM Router ready — groq_enabled: {self._has_groq}, local: {self._local_model}"
        )

    def classify_complexity(self, message: str) -> Complexity:
        """Classify whether a query needs the fast or power model."""
        msg_lower = message.lower()

        # Long messages likely need deeper reasoning
        if len(message) > 500:
            return Complexity.COMPLEX

        # Check for complex signal keywords
        for signal in _COMPLEX_SIGNALS:
            if signal in msg_lower:
                return Complexity.COMPLEX

        # Multi-sentence queries with question marks
        question_count = msg_lower.count("?")
        if question_count >= 2:
            return Complexity.COMPLEX

        return Complexity.SIMPLE

    def _select_model(self, complexity: Complexity) -> str:
        """Select the appropriate model based on complexity."""
        if complexity == Complexity.COMPLEX:
            return self._power_model
        return self._fast_model

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        force_model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> tuple[str, str]:
        """
        Route and complete a chat request.

        Returns:
            (response_text, model_used)
        """
        # Determine complexity from the last user message
        user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                user_msg = m["content"]
                break

        complexity = self.classify_complexity(user_msg)
        model = force_model or self._select_model(complexity)

        # Build full message list with system prompt
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        if not self._has_groq:
            logger.info(f"Routing → local Ollama ({self._local_model})")
            response = await self._ollama.complete(
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response, self._local_model

        logger.info(f"Routing → {model} (complexity={complexity.value})")

        try:
            response = await self._groq.complete(
                messages=full_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response, model
        except Exception as e:
            logger.warning(f"Groq failed: {e}. Falling back to Ollama.")
            response = await self._ollama.complete(
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response, self._local_model

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        force_model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> tuple[AsyncGenerator[str, None], str]:
        """
        Route and stream a chat response.

        Returns:
            (async_generator_of_chunks, model_used)
        """
        user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                user_msg = m["content"]
                break

        complexity = self.classify_complexity(user_msg)
        model = force_model or self._select_model(complexity)

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        if not self._has_groq:
            logger.info(f"Streaming → local Ollama ({self._local_model})")
            generator = self._ollama.stream(
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return generator, self._local_model

        logger.info(f"Streaming → {model} (complexity={complexity.value})")

        try:
            # We don't try-catch inside the stream directly here easily for fallback, 
            # but we can check if it initializes. If it fails mid-stream, the groq client 
            # will yield an error string. We'll catch initial connection errors if any.
            generator = self._groq.stream(
                messages=full_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return generator, model
        except Exception as e:
            logger.warning(f"Groq stream failed: {e}. Falling back to Ollama.")
            generator = self._ollama.stream(
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return generator, self._local_model
