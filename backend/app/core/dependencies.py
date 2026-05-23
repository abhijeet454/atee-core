"""
Jarvis++ Dependency Injection — shared resources for FastAPI endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.llm.router import LLMRouter
    from app.memory.manager import MemoryManager

# These get initialized in the app lifespan
_llm_router: LLMRouter | None = None
_memory_manager: MemoryManager | None = None


def set_llm_router(router: "LLMRouter") -> None:
    global _llm_router
    _llm_router = router


def set_memory_manager(manager: "MemoryManager") -> None:
    global _memory_manager
    _memory_manager = manager


def get_llm_router() -> "LLMRouter":
    assert _llm_router is not None, "LLMRouter not initialized"
    return _llm_router


def get_memory_manager() -> "MemoryManager":
    assert _memory_manager is not None, "MemoryManager not initialized"
    return _memory_manager
