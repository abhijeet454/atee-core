"""
Memory Manager — unified facade over short-term, vector, and structured memory.

Provides high-level remember/recall/forget operations that coordinate
all three memory subsystems.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from loguru import logger

from app.memory.short_term import ShortTermMemory
from app.memory.vector_store import VectorStore
from app.memory.long_term import LongTermMemory
from app.schemas.memory import MemoryEntry


# Default system prompt that defines Atee's personality
SYSTEM_PROMPT = """You are Atee, a local-first AI personal assistant that speaks naturally in Hindi.

Core traits:
- Intelligent, calm, caring, and practical
- Privacy-respecting and local-first
- Helpful with tasks, planning, coding, writing, and general knowledge

Language & tone rules:
- Primary language: Hindi (you may mix light Hinglish if the user does).
- Always use respectful address: "aap/आप". Never use "tum/tu".
- Sound like a real person: short, warm, and clear. Avoid dramatic/poetic lines, self-praise, or repetitive filler.

Conversation behavior:
- Ask 1 focused follow-up question only when it truly helps.
- If the user says romantic/flirty lines (e.g., "mujhe tumse pyar hai"), respond kindly and playful-but-respectful, without getting explicit or manipulative. Keep it brief and steer back to what they want to do next.

Memory:
- You may receive relevant memories. Use them naturally if helpful, without saying "according to my memory" unless asked.

Conciseness:
- Keep answers compact by default. Go detailed only when the user asks or the task is complex."""


class MemoryManager:
    """
    Unified memory facade.

    Coordinates:
    - ShortTermMemory: per-session conversation buffers
    - VectorStore: semantic search via FAISS
    - LongTermMemory: structured persistence via SQLite
    """

    def __init__(self):
        self.short_term = ShortTermMemory(max_turns=20, ttl_seconds=3600)
        self.vector_store = VectorStore()
        self.long_term = LongTermMemory()

    async def initialize(self) -> None:
        """Initialize all memory subsystems."""
        await self.vector_store.initialize()
        await self.long_term.initialize()
        logger.info(
            f"Memory Manager ready — "
            f"vectors: {self.vector_store.count}, "
            f"structured: {await self.long_term.get_memory_count()}"
        )

    async def remember(
        self,
        content: str,
        source: str = "conversation",
        importance: float = 0.5,
        emotional_tag: str = "neutral",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Store something in both vector and structured memory.

        Returns the memory ID.
        """
        memory_id = str(uuid.uuid4())

        # Store in vector store for semantic search
        await self.vector_store.add(
            content=content,
            metadata={"source": source, "importance": importance, **(metadata or {})},
            doc_id=memory_id,
        )

        # Store in structured DB
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            source=source,
            importance=importance,
            emotional_tag=emotional_tag,
            metadata=metadata or {},
        )
        await self.long_term.store_memory(entry)

        logger.debug(f"Remembered [{memory_id[:8]}...] importance={importance}")
        return memory_id

    async def recall(self, query: str, top_k: int = 5) -> List[str]:
        """
        Retrieve relevant memories via semantic search.

        Returns list of memory content strings, ranked by relevance.
        """
        results = await self.vector_store.search(query, top_k=top_k)

        memories = []
        for doc, score in results:
            if score > 0.3:  # Relevance threshold
                memories.append(doc["content"])
                # Update access tracking in structured DB
                await self.long_term.get_memory_by_id(doc["id"])

        logger.debug(f"Recalled {len(memories)} memories for query: {query[:50]}...")
        return memories

    def add_to_conversation(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session's short-term buffer."""
        self.short_term.add_message(session_id, role, content)

    def get_conversation_history(self, session_id: str) -> List[dict]:
        """Get the full conversation history for a session."""
        return self.short_term.get_messages(session_id)

    async def log_conversation_turn(
        self, session_id: str, role: str, content: str
    ) -> None:
        """Persist a conversation turn to long-term storage."""
        await self.long_term.store_conversation_turn(session_id, role, content)

    async def should_remember(self, content: str) -> tuple[bool, float]:
        """
        Heuristic to decide if content is worth remembering long-term.

        Returns (should_store, importance_score).
        """
        content_lower = content.lower()

        # High importance signals
        high_signals = [
            "remember", "don't forget", "important", "my name is",
            "i prefer", "i like", "i hate", "i always", "i never",
            "my favorite", "i work at", "i live in",
            "yaad rakhna", "mera naam", "mujhe pasand hai", "mujhe achha lagta hai", 
            "main chahta hu", "bhulna mat"
        ]

        # Medium importance signals
        medium_signals = [
            "i think", "in my opinion", "i believe", "i want",
            "i need", "please note", "keep in mind",
            "mera manna hai", "zaroori", "dhyaan rakhna", "mujhe lagta hai"
        ]

        for signal in high_signals:
            if signal in content_lower:
                return True, 0.9

        for signal in medium_signals:
            if signal in content_lower:
                return True, 0.7

        # Long messages often contain meaningful info
        if len(content) > 200:
            return True, 0.6

        return False, 0.3

    async def forget(self, memory_id: str) -> bool:
        """Remove a specific memory from all stores."""
        deleted_vector = await self.vector_store.delete(memory_id)
        # SQLite deletion would go here too
        return deleted_vector

    async def get_stats(self) -> dict:
        """Get memory system statistics."""
        return {
            "active_sessions": self.short_term.active_sessions,
            "vector_count": self.vector_store.count,
            "structured_count": await self.long_term.get_memory_count(),
        }

    async def shutdown(self) -> None:
        """Persist all state and close connections."""
        await self.vector_store.save()
        await self.long_term.shutdown()
        logger.info("Memory Manager shut down")
