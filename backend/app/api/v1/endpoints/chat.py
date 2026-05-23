"""
Chat Endpoints — POST for full responses, WebSocket for streaming.

Integrates LLM routing with memory context injection.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.core.dependencies import get_llm_router, get_memory_manager
from app.memory.manager import SYSTEM_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse, StreamChunk

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and receive a full response.

    - Retrieves relevant memories for context
    - Routes to appropriate LLM model based on complexity
    - Stores important information to memory
    """
    llm = get_llm_router()
    memory = get_memory_manager()

    session_id = request.session_id or str(uuid.uuid4())

    # ── 1. Retrieve memory context ───────────────────────
    memory_context = []
    if request.include_memory:
        memory_context = await memory.recall(request.message, top_k=5)

    # ── 2. Build messages with context ───────────────────
    # Add user message to short-term buffer
    memory.add_to_conversation(session_id, "user", request.message)

    # Get conversation history
    history = memory.get_conversation_history(session_id)

    # Enhance system prompt with memory context
    system = SYSTEM_PROMPT
    if memory_context:
        context_str = "\n".join(f"- {m}" for m in memory_context)
        system += f"\n\nRelevant memories from past interactions:\n{context_str}"

    # ── 3. Call LLM ──────────────────────────────────────
    response_text, model_used = await llm.complete(
        messages=history,
        system_prompt=system,
    )

    # ── 4. Store response in conversation buffer ─────────
    memory.add_to_conversation(session_id, "assistant", response_text)

    # ── 5. Persist conversation turns ────────────────────
    await memory.log_conversation_turn(session_id, "user", request.message)
    await memory.log_conversation_turn(session_id, "assistant", response_text)

    # ── 6. Auto-remember important info ──────────────────
    should_store, importance = await memory.should_remember(request.message)
    if should_store:
        await memory.remember(
            content=f"User said: {request.message}",
            source="conversation",
            importance=importance,
        )
        logger.debug(f"Auto-remembered user message (importance={importance})")

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        model_used=model_used,
        memory_context=memory_context,
        timestamp=datetime.utcnow(),
    )


@router.websocket("/stream")
async def chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat responses.

    Client sends JSON: {"message": "...", "session_id": "..."}
    Server streams JSON: {"chunk": "...", "done": false} / {"chunk": "", "done": true, ...}
    """
    await websocket.accept()
    logger.info("WebSocket chat connection opened")

    llm = get_llm_router()
    memory = get_memory_manager()

    try:
        while True:
            # Receive message from client
            raw = await websocket.receive_text()
            data = json.loads(raw)
            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid.uuid4()))

            if not message:
                await websocket.send_json({"error": "Empty message"})
                continue

            # Retrieve memory context
            memory_context = await memory.recall(message, top_k=5)

            # Build messages
            memory.add_to_conversation(session_id, "user", message)
            history = memory.get_conversation_history(session_id)

            system = SYSTEM_PROMPT
            if memory_context:
                context_str = "\n".join(f"- {m}" for m in memory_context)
                system += f"\n\nRelevant memories:\n{context_str}"

            # Stream response
            generator, model_used = await llm.stream(
                messages=history,
                system_prompt=system,
            )

            full_response = ""
            async for chunk in generator:
                full_response += chunk
                await websocket.send_json({
                    "chunk": chunk,
                    "done": False,
                    "session_id": session_id,
                })

            # Send completion signal
            await websocket.send_json({
                "chunk": "",
                "done": True,
                "session_id": session_id,
                "model_used": model_used,
                "memory_context": memory_context,
            })

            # Store in memory
            memory.add_to_conversation(session_id, "assistant", full_response)
            await memory.log_conversation_turn(session_id, "user", message)
            await memory.log_conversation_turn(session_id, "assistant", full_response)

            should_store, importance = await memory.should_remember(message)
            if should_store:
                await memory.remember(
                    content=f"User said: {message}",
                    source="conversation",
                    importance=importance,
                )

    except WebSocketDisconnect:
        logger.info("WebSocket chat connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))
