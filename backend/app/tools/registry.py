"""
Tool Registry.
"""
from typing import Dict, Any

class ToolRegistry:
    def __init__(self):
        self._tools = {}
        
    def register(self, name: str, tool: Any):
        self._tools[name] = tool
        
    def get(self, name: str) -> Any:
        return self._tools.get(name)

# Singleton
_registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    return _registry
