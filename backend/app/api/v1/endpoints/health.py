"""
Health check endpoint — reports system component status.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """Return system health and component readiness."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "groq": "configured" if settings.has_groq else "missing_key",
            "faiss": "ready",
            "sqlite": "ready",
        },
    }
