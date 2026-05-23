"""
Memory Agent — decides what to remember and forget.
"""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.core.dependencies import get_memory_manager


class MemoryAgent(BaseAgent):
    """
    Evaluates conversations and extracts important facts to remember.
    """
    
    @property
    def name(self) -> str:
        return "memory"
        
    @property
    def description(self) -> str:
        return "Manages long-term memory extraction."
        
    async def execute(self, context: AgentContext) -> AgentResult:
        memory = get_memory_manager()
        
        # We can use the heuristic from manager or an LLM call here.
        # For simplicity, we use the heuristic already built into manager.
        should_store, importance = await memory.should_remember(context.user_input)
        
        if should_store:
            await memory.remember(
                content=f"User said: {context.user_input}",
                source="conversation",
                importance=importance,
            )
            return AgentResult(
                action_taken=True,
                metadata={"remembered": True, "importance": importance}
            )
            
        return AgentResult(action_taken=False)
