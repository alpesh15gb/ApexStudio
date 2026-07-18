"""Debug Agent — error diagnosis and resolution."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DebugAgent(BaseAgent):
    """Handles debugging, log analysis, and error fixing."""

    def __init__(self, project_id: str, tool_registry=None):
        super().__init__(project_id, tool_registry)
        self.system_prompt = "You are a senior debugging engineer fixing application issues."

    async def think(self, message: str, context: str | None = None) -> str:
        """
        Analyze an error and determine the fix approach.
        """
        self.add_to_history("user", message)

        response = (
            f"I'll help debug this issue. Here's my approach:\n\n"
            f"1. **Analyze** — Read the error and logs\n"
            f"2. **Hypothesize** — Identify root causes\n"
            f"3. **Fix** — Apply targeted fixes\n"
            f"4. **Verify** — Confirm the issue is resolved\n\n"
            f"Debugging capabilities:\n"
            f"- Read container and build logs\n"
            f"- Execute commands to inspect the environment\n"
            f"- Edit files to apply fixes\n"
            f"- Rebuild and verify the fix\n\n"
            f"Please describe the issue you're experiencing."
        )

        self.add_to_history("assistant", response)
        return response
