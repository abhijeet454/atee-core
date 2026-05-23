"""
Conversation Agent — handles natural dialogue and standard queries.
"""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.core.dependencies import get_llm_router
from app.memory.manager import SYSTEM_PROMPT


class ConversationAgent(BaseAgent):
    """
    Agent responsible for standard conversational interactions.
    Uses context from memory and emotion state.
    """
    
    @property
    def name(self) -> str:
        return "conversation"
        
    @property
    def description(self) -> str:
        return "Handles general chat, greetings, and queries not requiring tools."
        
    async def execute(self, context: AgentContext) -> AgentResult:
        llm = get_llm_router()
        
        # Build system prompt with context
        system = SYSTEM_PROMPT
        system += f"\n\nCurrent Emotion State: {context.emotion_state}"
        
        if context.memory_context:
            context_str = "\n".join(f"- {m}" for m in context.memory_context)
            system += f"\n\nRelevant memories:\n{context_str}"
            
        if context.shared_data.get("tool_results"):
            tool_results = context.shared_data["tool_results"]
            system += f"\n\nTool Results:\n{tool_results}"
            
        # Get completion
        response, model_used = await llm.complete(
            messages=context.history,
            system_prompt=system,
        )
        
        return AgentResult(
            response=response,
            action_taken=True,
            metadata={"model": model_used, "agent": self.name}
        )
