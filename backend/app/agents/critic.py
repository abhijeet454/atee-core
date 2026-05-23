"""
Critic Agent — evaluates draft responses for quality and safety.
"""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentContext, AgentResult

class CriticAgent(BaseAgent):
    """
    Evaluates responses and requests refinement if needed.
    """
    
    @property
    def name(self) -> str:
        return "critic"
        
    @property
    def description(self) -> str:
        return "Evaluates responses for quality, safety, and constraints."
        
    async def execute(self, context: AgentContext) -> AgentResult:
        # Simplistic rule-based critic
        draft_response = context.shared_data.get("draft_response", "")
        
        if not draft_response:
            return AgentResult(action_taken=False)
            
        # Example constraint: Don't claim to be human
        lower_resp = draft_response.lower()
        if "i am human" in lower_resp or "i am a person" in lower_resp:
            return AgentResult(
                action_taken=True,
                needs_refinement=True,
                metadata={"reason": "Identity claim violation"}
            )
            
        return AgentResult(action_taken=True, needs_refinement=False)
