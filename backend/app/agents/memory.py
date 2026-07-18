"""AI Memory — persistent conversation and decision storage per project."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIMemory, AISession

logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Manages AI agent memory for a project.
    Stores conversations, decisions, and context.
    """

    def __init__(self, db: AsyncSession, project_id: str):
        self.db = db
        self.project_id = project_id

    async def create_session(self, mode: str = "build", model: str = "claude-sonnet-5") -> AISession:
        """Create a new AI session for the project."""
        session = AISession(
            project_id=self.project_id,
            mode=mode,
            model=model,
            status="active",
        )
        self.db.add(session)
        await self.db.flush()

        # Add system greeting to memory
        await self.add_memory(
            session_id=session.id,
            role="system",
            content=f"Starting {mode} session for project {self.project_id}",
        )
        return session

    async def add_memory(
        self,
        content: str,
        role: str = "assistant",
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> AIMemory:
        """Add a memory entry."""
        memory = AIMemory(
            project_id=self.project_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.db.add(memory)
        await self.db.flush()
        return memory

    async def get_session_history(self, session_id: str, limit: int = 100) -> list[AIMemory]:
        """Get conversation history for a session."""
        result = await self.db.execute(
            select(AIMemory)
            .where(
                AIMemory.session_id == session_id,
                AIMemory.project_id == self.project_id,
            )
            .order_by(AIMemory.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_context(self, limit: int = 20) -> str:
        """Get recent context as a formatted string for the AI."""
        result = await self.db.execute(
            select(AIMemory)
            .where(AIMemory.project_id == self.project_id)
            .order_by(AIMemory.created_at.desc())
            .limit(limit)
        )
        memories = list(result.scalars().all())

        if not memories:
            return "No previous context."

        context_lines = []
        for m in reversed(memories):
            timestamp = m.created_at.strftime("%H:%M:%S") if m.created_at else ""
            context_lines.append(f"[{timestamp}] {m.role}: {m.content[:500]}")

        return "\n".join(context_lines)

    async def close_session(self, session_id: str, summary: str | None = None) -> None:
        """Mark a session as completed."""
        result = await self.db.execute(
            select(AISession).where(AISession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.status = "completed"
            session.summary = summary or "Session completed"
            await self.db.flush()

    async def get_active_session(self) -> AISession | None:
        """Get the most recent active session."""
        result = await self.db.execute(
            select(AISession)
            .where(
                AISession.project_id == self.project_id,
                AISession.status == "active",
            )
            .order_by(AISession.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
