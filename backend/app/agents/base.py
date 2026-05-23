"""
Agent Framework Base Classes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentContext:
    """Shared context passed between agents in the cognitive loop."""
    session_id: str
    user_input: str
    history: List[Dict[str, str]] = field(default_factory=list)
    memory_context: List[str] = field(default_factory=list)
    emotion_state: str = "neutral"
    shared_data: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class AgentResult:
    """Result returned by an agent."""
    response: Optional[str] = None
    action_taken: bool = False
    next_agent: Optional[str] = None
    needs_refinement: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the agent."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what the agent does."""
        pass
        
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's primary function."""
        pass
