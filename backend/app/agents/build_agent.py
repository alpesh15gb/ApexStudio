"""Build Agent — code generation and application building."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class BuildAgent(BaseAgent):
    """Handles code generation, building, and testing."""

    def __init__(self, project_id: str, tool_registry=None):
        super().__init__(project_id, tool_registry)
        self.system_prompt = "You are a senior full-stack developer building applications."

    async def think(self, message: str, context: str | None = None) -> str:
        """
        Process a build request and coordinate code generation.
        """
        self.add_to_history("user", message)

        response = (
            f"I'll start building your application based on your requirements.\n\n"
            f"**Current capabilities:**\n"
            f"- Read/write files in your workspace\n"
            f"- Execute commands\n"
            f"- Build and test applications\n"
            f"- Fix compilation errors\n\n"
            f"The AI agent system will generate:\n"
            f"- Database models and migrations\n"
            f"- FastAPI backend with all APIs\n"
            f"- Flutter frontend with UI\n"
            f"- Authentication and authorization\n\n"
            f"Building will start once the implementation plan is approved."
        )

        self.add_to_history("assistant", response)
        return response
