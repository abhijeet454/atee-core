"""
Jarvis++ Schemas — Memory models.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    id: Optional[str] = None
    content: str
    source: str = "conversation"  # conversation, user, system
    importance: float = 0.5  # 0.0 to 1.0
    emotional_tag: str = "neutral"
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0


class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = 5


class MemorySearchResponse(BaseModel):
    results: List[MemoryEntry]
    query: str
