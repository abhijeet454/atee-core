"""
Planner Agent — breaks down complex tasks into steps.
"""
from __future__ import annotations

import json
from loguru import logger

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.core.dependencies import get_llm_router

PLANNER_PROMPT = """You are the Planner Agent for Jarvis++.
Your job is to analyze the user's input and decide how to handle it.
You must output a JSON object exactly like this:
{
    "requires_tools": boolean,
    "tools_needed": ["list", "of", "tool", "names"],
    "plan": ["Step 1", "Step 2"],
    "direct_response": "If no tools are needed, you can provide a direct response here, else null."
}
"""

class PlannerAgent(BaseAgent):
    """
    Analyzes complex user intents and forms a plan.
    """
    
    @property
    def name(self) -> str:
        return "planner"
        
    @property
    def description(self) -> str:
        return "Plans multi-step tasks and determines if tools are needed."
        
    async def execute(self, context: AgentContext) -> AgentResult:
        llm = get_llm_router()
        
        response, _ = await llm.complete(
            messages=[{"role": "user", "content": context.user_input}],
            system_prompt=PLANNER_PROMPT,
        )
        
        try:
            # Extract JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != -1:
                plan_data = json.loads(response[start:end])
            else:
                plan_data = json.loads(response)
                
            context.shared_data["plan"] = plan_data
            
            if plan_data.get("requires_tools"):
                logger.info(f"Planner decided tools are needed: {plan_data.get('tools_needed')}")
                return AgentResult(
                    action_taken=True,
                    next_agent="tool",
                    metadata={"plan": plan_data}
                )
            else:
                # No tools needed, delegate to conversation or return direct response
                if plan_data.get("direct_response"):
                    return AgentResult(
                        response=plan_data["direct_response"],
                        action_taken=True,
                        metadata={"plan": plan_data}
                    )
                return AgentResult(
                    action_taken=False,
                    next_agent="conversation"
                )
                
        except Exception as e:
            logger.error(f"Planner failed to parse JSON: {e}")
            # Fallback to conversation
            return AgentResult(
                action_taken=False,
                next_agent="conversation"
            )
