"""
ATEE — FastAPI Application Entry Point.

Local-first AI companion with multi-agent orchestration,
hybrid LLM routing, advanced RAG memory, and voice I/O.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize and teardown resources."""
    # ── Startup ──────────────────────────────────────────
    setup_logging()
    logger.info(f"🚀 Starting {settings.app_name}")
    settings.ensure_data_dirs()

    # Initialize LLM Router
    from app.llm.router import LLMRouter
    from app.core.dependencies import set_llm_router

    llm_router = LLMRouter()
    set_llm_router(llm_router)
    logger.info("✅ LLM Router initialized (Groq)")

    # Initialize Memory Manager
    from app.memory.manager import MemoryManager
    from app.core.dependencies import set_memory_manager

    memory_manager = MemoryManager()
    await memory_manager.initialize()
    set_memory_manager(memory_manager)
    logger.info("✅ Memory Manager initialized (FAISS + SQLite)")

    logger.info(f"🧠 {settings.app_name} is ready!")

    yield

    # ── Shutdown ─────────────────────────────────────────
    logger.info("Saving memory state...")
    await memory_manager.shutdown()
    logger.info(f"👋 {settings.app_name} shut down gracefully.")


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Local-first AI personal assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────
    from app.api.v1.router import router as v1_router

    app.include_router(v1_router)

    return app


app = create_app()
