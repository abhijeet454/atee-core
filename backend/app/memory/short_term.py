"""
Short-Term Memory — in-memory conversation buffer per session.

Keeps the last N turns for each active session with TTL expiry.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Optional

from loguru import logger


class ShortTermMemory:
    """Per-session conversation buffer with TTL-based expiry."""

    def __init__(self, max_turns: int = 20, ttl_seconds: int = 3600):
        self._max_turns = max_turns
        self._ttl = ttl_seconds
        self._sessions: Dict[str, dict] = {}  # session_id → {messages, last_access}

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session buffer."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {"messages": [], "last_access": time.time()}

        session = self._sessions[session_id]
        session["messages"].append({"role": role, "content": content})
        session["last_access"] = time.time()

        # Trim to max turns (keep system messages)
        msgs = session["messages"]
        if len(msgs) > self._max_turns:
            # Keep the first message if it's a system prompt, then trim old ones
            system_msgs = [m for m in msgs if m["role"] == "system"]
            non_system = [m for m in msgs if m["role"] != "system"]
            trimmed = non_system[-(self._max_turns - len(system_msgs)):]
            session["messages"] = system_msgs + trimmed

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get all messages for a session."""
        if session_id not in self._sessions:
            return []
        self._sessions[session_id]["last_access"] = time.time()
        return self._sessions[session_id]["messages"]

    def get_last_n(self, session_id: str, n: int = 5) -> List[Dict[str, str]]:
        """Get the last N messages for a session."""
        messages = self.get_messages(session_id)
        return messages[-n:] if messages else []

    def clear_session(self, session_id: str) -> None:
        """Clear a specific session."""
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        """Remove sessions that have exceeded TTL. Returns count removed."""
        now = time.time()
        expired = [
            sid for sid, data in self._sessions.items()
            if now - data["last_access"] > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)

    @property
    def active_sessions(self) -> int:
        return len(self._sessions)
