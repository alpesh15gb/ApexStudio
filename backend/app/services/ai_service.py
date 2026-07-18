"""AI Orchestration Service — high-level interface for AI operations."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.agents.memory import AgentMemory
from app.services.omniroute_service import OmnirouteService

logger = logging.getLogger(__name__)


class AIService:
    """
    High-level service for AI operations.
    Provides interface between API layer and agent system.
    """

    def __init__(self, db: AsyncSession, project_id: str):
        self.db = db
        self.project_id = project_id
        self.orchestrator = AgentOrchestrator(db, project_id)
        self.memory = AgentMemory(db, project_id)
        self.omniroute = OmnirouteService()

    async def chat(self, message: str) -> dict:
        """Process a chat message through the agent orchestrator."""
        return await self.orchestrator.process_message(message)

    async def stream_chat(self, message: str):
        """Stream a chat response."""
        system_prompt = await self._build_system_prompt()
        async for chunk in self.omniroute.stream_response(system_prompt, message):
            yield chunk

    async def switch_mode(self, mode: str) -> dict:
        """Switch the agent mode (plan/build/debug)."""
        return await self.orchestrator.switch_mode(mode)

    async def get_status(self) -> dict:
        """Get AI system status."""
        return await self.orchestrator.get_status()

    async def _build_system_prompt(self) -> str:
        """Build a context-aware system prompt."""
        context = await self.memory.get_recent_context()
        return f"""You are Apex Studio, an AI-powered software development platform.
You help users build complete applications by chatting with them.

Current mode: {self.orchestrator.current_mode}
Project ID: {self.project_id}

Recent context:
{context}

Rules:
- You can generate code, design architecture, and debug issues
- The stack is FastAPI (Python) + PostgreSQL + Flutter (Web)
- Be helpful, thorough, and proactive
- If you don't know something, say so
- Keep responses concise but complete
"""
