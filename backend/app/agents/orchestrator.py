"""Agent Orchestrator — routes messages, manages agents, coordinates tools."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.agents.build_agent import BuildAgent
from app.agents.debug_agent import DebugAgent
from app.agents.memory import AgentMemory
from app.agents.plan_agent import PlanAgent
from app.agents.tools import ToolRegistry

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Routes user messages to the correct agent,
    manages mode transitions, and coordinates agent activity.
    """

    MODE_PLAN = "plan"
    MODE_BUILD = "build"
    MODE_DEBUG = "debug"

    def __init__(self, db: AsyncSession, project_id: str):
        self.db = db
        self.project_id = project_id
        self.current_mode: str = self.MODE_PLAN
        self.memory = AgentMemory(db, project_id)
        self.tools = ToolRegistry()

        # Agents (lazy init)
        self._plan_agent: PlanAgent | None = None
        self._build_agent: BuildAgent | None = None
        self._debug_agent: DebugAgent | None = None

    @property
    def plan_agent(self) -> PlanAgent:
        if self._plan_agent is None:
            self._plan_agent = PlanAgent(self.project_id, self.tools)
        return self._plan_agent

    @property
    def build_agent(self) -> BuildAgent:
        if self._build_agent is None:
            self._build_agent = BuildAgent(self.project_id, self.tools)
        return self._build_agent

    @property
    def debug_agent(self) -> DebugAgent:
        if self._debug_agent is None:
            self._debug_agent = DebugAgent(self.project_id, self.tools)
        return self._debug_agent

    async def process_message(self, message: str) -> dict:
        """
        Process a user message and return the agent's response.
        Determines mode, routes to agent, returns structured result.
        """
        detected_mode = self._detect_mode(message)
        self.current_mode = detected_mode

        # Get context from memory
        context = await self.memory.get_recent_context()

        # Route to appropriate agent
        if self.current_mode == self.MODE_PLAN:
            agent = self.plan_agent
            result = await agent.think(message, context)
        elif self.current_mode == self.MODE_BUILD:
            agent = self.build_agent
            result = await agent.think(message, context)
        elif self.current_mode == self.MODE_DEBUG:
            agent = self.debug_agent
            result = await agent.think(message, context)

        # Store in memory
        await self.memory.add_memory(
            content=message[:1000],
            role="user",
        )

        response_text = result if isinstance(result, str) else str(result.get("response", ""))
        await self.memory.add_memory(
            content=response_text[:2000],
            role="assistant",
        )

        return {
            "mode": self.current_mode,
            "response": result,
            "project_id": self.project_id,
        }

    def _detect_mode(self, message: str) -> str:
        """
        Detect the appropriate mode from a user message using keyword analysis.
        """
        msg_lower = message.lower()

        # Debug indicators
        debug_keywords = [
            "error", "bug", "broken", "not working", "fails", "crash",
            "exception", "wrong", "incorrect", "issue", "problem",
        ]
        if any(kw in msg_lower for kw in debug_keywords):
            return self.MODE_DEBUG

        # Plan indicators
        plan_keywords = [
            "plan", "design", "architecture", "think about", "what should",
            "how should", "requirement", "feature", "idea", "i want to build",
            "new project", "start",
        ]
        if any(kw in msg_lower for kw in plan_keywords):
            return self.MODE_PLAN

        # Default to build
        return self.MODE_BUILD

    async def switch_mode(self, mode: str) -> dict:
        """Explicitly switch the agent mode."""
        if mode not in [self.MODE_PLAN, self.MODE_BUILD, self.MODE_DEBUG]:
            return {"error": f"Invalid mode: {mode}. Use plan, build, or debug."}

        old_mode = self.current_mode
        self.current_mode = mode
        logger.info(f"Mode switch: {old_mode} -> {mode}")

        # Clear agent history on mode switch
        agent_map = {
            self.MODE_PLAN: self.plan_agent,
            self.MODE_BUILD: self.build_agent,
            self.MODE_DEBUG: self.debug_agent,
        }
        if mode in agent_map:
            agent_map[mode].clear_history()

        return {"message": f"Switched from {old_mode} mode to {mode} mode"}

    async def get_status(self) -> dict:
        """Get the current orchestrator status."""
        return {
            "project_id": self.project_id,
            "current_mode": self.current_mode,
            "memory_count": len(self.memory.get_recent_context()),
        }
