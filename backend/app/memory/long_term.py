"""
Long-Term Memory — SQLite-backed structured storage for persistent memories.

Stores conversations, memories with importance scores, emotional tags,
and access tracking for memory decay.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiosqlite
from loguru import logger

from app.core.config import settings
from app.schemas.memory import MemoryEntry


_INIT_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    source TEXT DEFAULT 'conversation',
    importance REAL DEFAULT 0.5,
    emotional_tag TEXT DEFAULT 'neutral',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    access_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    user_message TEXT,
    assistant_response TEXT,
    rating INTEGER,
    correction TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
"""


class LongTermMemory:
    """SQLite-backed persistent memory with importance scoring and decay."""

    def __init__(self):
        self._db_path = settings.sqlite_db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Create database and tables."""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_INIT_SQL)
        await self._db.commit()
        logger.info(f"SQLite database ready at {self._db_path}")

    async def store_memory(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns the memory ID."""
        entry_id = entry.id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await self._db.execute(
            """INSERT OR REPLACE INTO memories
               (id, content, source, importance, emotional_tag, metadata, created_at, last_accessed, access_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_id,
                entry.content,
                entry.source,
                entry.importance,
                entry.emotional_tag,
                str(entry.metadata),
                entry.created_at.isoformat() if entry.created_at else now,
                now,
                entry.access_count,
            ),
        )
        await self._db.commit()
        return entry_id

    async def get_memories(
        self,
        source: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """Retrieve memories filtered by source and importance."""
        query = "SELECT * FROM memories WHERE importance >= ?"
        params: list = [min_importance]

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY importance DESC, last_accessed DESC LIMIT ?"
        params.append(limit)

        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_entry(row) for row in rows]

    async def get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory and update access tracking."""
        cursor = await self._db.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        # Update access tracking
        await self._db.execute(
            """UPDATE memories SET
               last_accessed = ?, access_count = access_count + 1
               WHERE id = ?""",
            (datetime.utcnow().isoformat(), memory_id),
        )
        await self._db.commit()

        return self._row_to_entry(row)

    async def store_conversation_turn(
        self, session_id: str, role: str, content: str
    ) -> None:
        """Log a single conversation turn."""
        await self._db.execute(
            """INSERT INTO conversations (id, session_id, role, content, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), session_id, role, content, datetime.utcnow().isoformat()),
        )
        await self._db.commit()

    async def decay_memories(self, decay_factor: float = 0.95) -> int:
        """Reduce importance of all memories by a factor. Returns count affected."""
        cursor = await self._db.execute(
            "UPDATE memories SET importance = importance * ? WHERE importance > 0.1",
            (decay_factor,),
        )
        await self._db.commit()
        return cursor.rowcount

    async def prune_low_importance(self, threshold: float = 0.1) -> int:
        """Delete memories below importance threshold."""
        cursor = await self._db.execute(
            "DELETE FROM memories WHERE importance < ?", (threshold,)
        )
        await self._db.commit()
        count = cursor.rowcount
        if count:
            logger.info(f"Pruned {count} low-importance memories")
        return count

    async def store_feedback(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        rating: int,
        correction: Optional[str] = None,
    ) -> None:
        """Store user feedback on a response."""
        await self._db.execute(
            """INSERT INTO feedback (id, session_id, user_message, assistant_response, rating, correction, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                session_id,
                user_message,
                assistant_response,
                rating,
                correction,
                datetime.utcnow().isoformat(),
            ),
        )
        await self._db.commit()

    async def get_memory_count(self) -> int:
        cursor = await self._db.execute("SELECT COUNT(*) FROM memories")
        row = await cursor.fetchone()
        return row[0]

    async def shutdown(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            logger.info("SQLite connection closed")

    @staticmethod
    def _row_to_entry(row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            source=row["source"],
            importance=row["importance"],
            emotional_tag=row["emotional_tag"],
            created_at=row["created_at"],
            last_accessed=row["last_accessed"],
            access_count=row["access_count"],
        )
