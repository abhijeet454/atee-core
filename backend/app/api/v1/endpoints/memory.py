"""
Memory Endpoints — CRUD operations and search over the memory system.
"""

from __future__ import annotations

from fastapi import APIRouter
from loguru import logger

from app.core.dependencies import get_memory_manager
from app.schemas.memory import MemoryEntry, MemorySearchRequest, MemorySearchResponse

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/remember")
async def remember(entry: MemoryEntry):
    """Manually store a memory."""
    memory = get_memory_manager()
    memory_id = await memory.remember(
        content=entry.content,
        source=entry.source,
        importance=entry.importance,
        emotional_tag=entry.emotional_tag,
        metadata=entry.metadata,
    )
    return {"id": memory_id, "status": "stored"}


@router.post("/recall", response_model=MemorySearchResponse)
async def recall(request: MemorySearchRequest):
    """Search memories by semantic similarity."""
    memory = get_memory_manager()
    results = await memory.recall(request.query, top_k=request.top_k)
    entries = [MemoryEntry(content=r) for r in results]
    return MemorySearchResponse(results=entries, query=request.query)


@router.get("/stats")
async def memory_stats():
    """Get memory system statistics."""
    memory = get_memory_manager()
    return await memory.get_stats()


@router.delete("/{memory_id}")
async def forget(memory_id: str):
    """Delete a specific memory."""
    memory = get_memory_manager()
    deleted = await memory.forget(memory_id)
    return {"id": memory_id, "deleted": deleted}
