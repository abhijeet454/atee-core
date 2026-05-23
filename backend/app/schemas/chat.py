"""
Jarvis++ Schemas — Pydantic models for API request/response.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Chat ─────────────────────────────────────────────────


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_memory: bool = True


class ChatResponse(BaseModel):
    response: str
    session_id: str
    model_used: str
    memory_context: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StreamChunk(BaseModel):
    """A single chunk in a streaming response."""
    chunk: str
    done: bool = False
    session_id: str = ""
    model_used: str = ""
