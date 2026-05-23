"""
Orchestrator — manages the cognitive loop of agents.
"""
from __future__ import annotations

from loguru import logger
from typing import Optional

from app.agents.base import AgentContext, AgentResult
from app.agents.conversation import ConversationAgent
from app.agents.planner import PlannerAgent
from app.agents.tool_agent import ToolAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.critic import CriticAgent

class Orchestrator:
    """
    Manages the multi-agent cognitive loop.
    Perceive -> Reason (Planner) -> Act (Tools) -> Synthesize (Conversation) -> Reflect (Critic/Memory)
    """
    
    def __init__(self):
        self.agents = {
            "conversation": ConversationAgent(),
            "planner": PlannerAgent(),
            "tool": ToolAgent(),
            "memory": MemoryAgent(),
            "critic": CriticAgent(),
        }
        
    async def process(self, context: AgentContext) -> str:
        """Run the cognitive loop."""
        
        logger.info(f"Orchestrator starting for session {context.session_id}")
        
        # 1. Memory Agent extracts context
        await self.agents["memory"].execute(context)
        
        # 2. Planner decides approach
        plan_result = await self.agents["planner"].execute(context)
        
        if plan_result.response:
            # Planner gave a direct response
            context.shared_data["draft_response"] = plan_result.response
        else:
            # Follow the plan
            next_agent = plan_result.next_agent or "conversation"
            
            if next_agent == "tool":
                await self.agents["tool"].execute(context)
                next_agent = "conversation"
                
            if next_agent == "conversation":
                conv_result = await self.agents["conversation"].execute(context)
                context.shared_data["draft_response"] = conv_result.response
                
        # 3. Critic evaluates draft
        critic_result = await self.agents["critic"].execute(context)
        if critic_result.needs_refinement:
            logger.warning(f"Critic rejected response: {critic_result.metadata.get('reason')}")
            # Simplified retry with conversation agent using system prompt correction
            context.shared_data["tool_results"] = "SYSTEM: Correct your response. " + critic_result.metadata.get('reason', '')
            conv_result = await self.agents["conversation"].execute(context)
            context.shared_data["draft_response"] = conv_result.response
            
        return context.shared_data.get("draft_response", "I'm sorry, I encountered an error processing that.")
