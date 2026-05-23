"""
API v1 Router — aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, chat, memory, voice

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(chat.router)
router.include_router(memory.router)
router.include_router(voice.router)
