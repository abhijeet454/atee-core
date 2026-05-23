"""
Tool Agent — executes tools requested by the planner.
"""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.tools.registry import get_tool_registry

class ToolAgent(BaseAgent):
    """
    Executes tools and returns their results.
    """
    
    @property
    def name(self) -> str:
        return "tool"
        
    @property
    def description(self) -> str:
        return "Executes tools requested in the plan."
        
    async def execute(self, context: AgentContext) -> AgentResult:
        registry = get_tool_registry()
        plan = context.shared_data.get("plan", {})
        tools_needed = plan.get("tools_needed", [])
        
        if not tools_needed:
            return AgentResult(action_taken=False, next_agent="conversation")
            
        results = []
        for tool_name in tools_needed:
            tool = registry.get(tool_name)
            if tool:
                # Assuming tool.execute() is async and takes context
                # For a real implementation we need to pass parameters to tools, 
                # but we'll simplify for now by passing the whole user input
                try:
                    res = await tool.execute(context.user_input)
                    results.append(f"{tool_name}: {res}")
                except Exception as e:
                    results.append(f"{tool_name}: Error - {e}")
            else:
                results.append(f"{tool_name}: Tool not found")
                
        # Store results for the conversation agent to use
        context.shared_data["tool_results"] = "\n".join(results)
        
        return AgentResult(
            action_taken=True,
            next_agent="conversation",
            metadata={"tools_executed": tools_needed}
        )
