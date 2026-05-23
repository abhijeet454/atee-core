"""
ATEE Configuration — centralized settings from environment variables.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file and environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    app_name: str = "ATEE"
    log_level: str = "DEBUG"
    cors_origins: str = '["http://localhost:3000"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.cors_origins)

    # ── LLM: Groq ───────────────────────────────────────
    groq_api_key: str = ""
    groq_fast_model: str = "llama-3.1-8b-instant"
    groq_power_model: str = "llama-3.3-70b-versatile"

    # ── LLM: Ollama (local fallback) ────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b"

    # ── Database ────────────────────────────────────────
    sqlite_db_path: str = "./data/atee.db"

    # ── Memory / Embeddings ─────────────────────────────
    faiss_index_path: str = "./data/faiss_index"
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Derived helpers ─────────────────────────────────
    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    def ensure_data_dirs(self) -> None:
        """Create data directories if they don't exist."""
        Path(self.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)


# Singleton — import this everywhere
settings = Settings()
