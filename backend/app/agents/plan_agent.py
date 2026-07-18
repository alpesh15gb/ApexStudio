"""Plan Agent — requirements gathering and architecture planning."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.prompts import PLAN_PROMPT

logger = logging.getLogger(__name__)


class PlanAgent(BaseAgent):
    """Handles requirements gathering and implementation planning."""

    def __init__(self, project_id: str, tool_registry=None):
        super().__init__(project_id, tool_registry)
        self.system_prompt = "You are a senior software architect planning application builds."

    async def think(self, message: str, context: str | None = None) -> str:
        """
        Analyze a user's request and produce architectural planning output.
        In production, this calls the AI model via Omniroute.
        """
        self.add_to_history("user", message)

        # For now, return a structured response template
        # TODO: Integrate with Omniroute for LLM-powered planning
        response = (
            f"I understand you want to build: {message[:200]}\n\n"
            f"As the Plan Agent, I'll help design your application architecture. "
            f"Here's what I'll do:\n\n"
            f"1. **Understand Requirements** — Ask key questions about users and features\n"
            f"2. **Design Database** — Create schema and relationships\n"
            f"3. **Design API** — Plan REST endpoints\n"
            f"4. **Design UI** — Plan navigation and screens\n"
            f"5. **Create Roadmap** — Break into milestones\n\n"
            f"To get started, could you tell me more about:\n"
            f"- Who are your target users?\n"
            f"- What platforms do you need (web, mobile)?\n"
            f"- What are the core features?\n"
            f"- Do you need authentication or payments?"
        )

        self.add_to_history("assistant", response)
        return response
