"""Base agent class — shared agent infrastructure."""

from __future__ import annotations

import logging
from typing import Any, Callable

from app.agents.tools import ToolRegistry

logger = logging.getLogger(__name__)


class BaseAgent:
    """Abstract base for all AI agents (Plan, Build, Debug)."""

    def __init__(self, project_id: str, tool_registry: ToolRegistry | None = None):
        self.project_id = project_id
        self.tools = tool_registry or ToolRegistry()
        self.system_prompt: str = ""
        self.conversation_history: list[dict] = []

    async def think(self, message: str, context: dict | None = None) -> str:
        """
        Process a message and decide what to do.
        Override in subclasses.
        """
        raise NotImplementedError

    async def act(self, action: str, params: dict | None = None) -> Any:
        """
        Execute an action using available tools.
        """
        tool_name = self._parse_tool_call(action)
        if tool_name and self.tools.has_tool(tool_name):
            return await self.tools.execute(tool_name, **(params or {}))
        return {"error": f"Unknown tool: {tool_name}"}

    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def get_history(self, limit: int = 50) -> list[dict]:
        """Get recent conversation history."""
        return self.conversation_history[-limit:]

    def _parse_tool_call(self, action: str) -> str | None:
        """Extract tool name from an action string."""
        # Format: "tool_name(arg1=value1, arg2=value2)"
        if "(" in action:
            return action.split("(")[0].strip()
        return action.strip() if action else None

    async def run_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        return await self.tools.execute(tool_name, **kwargs)

    def clear_history(self) -> None:
        """Reset conversation history."""
        self.conversation_history = []
