"""WebSocket chat handler — AI conversation streaming."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class ChatWebSocketHandler:
    """
    Handles WebSocket chat connections for AI conversations.
    Messages are streamed from the AI agent to the client.
    """

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def handle_chat(
        self,
        websocket: WebSocket,
        project_id: str,
        user_id: str,
    ) -> None:
        """Main chat handler — receives messages, sends AI responses."""
        await self.manager.connect(websocket, project_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                message = message_data.get("message", "")
                session_id = message_data.get("session_id")

                if not message:
                    continue

                # Acknowledge receipt
                await self.manager.send_personal_message(
                    websocket,
                    {"type": "ack", "message": "Processing..."},
                )

                # Send AI response (placeholder — will be wired to agents)
                await self._stream_ai_response(websocket, project_id, user_id, message, session_id)

        except Exception as e:
            logger.error(f"Chat handler error for project {project_id}: {e}")
        finally:
            await self.manager.disconnect(websocket, project_id)

    async def _stream_ai_response(
        self,
        websocket: WebSocket,
        project_id: str,
        user_id: str,
        message: str,
        session_id: str | None,
    ) -> None:
        """Stream AI agent response to the client."""
        # TODO: Wire to actual AI agent orchestrator
        # For now, send placeholder response
        await self.manager.send_personal_message(
            websocket,
            {
                "type": "thought",
                "session_id": session_id,
                "content": "Analyzing your request...",
            },
        )

        await self.manager.send_personal_message(
            websocket,
            {
                "type": "response",
                "session_id": session_id,
                "content": (
                    "I understand your request. The AI agent system is being initialized. "
                    "I'll be able to build your application shortly."
                ),
            },
        )

        await self.manager.send_personal_message(
            websocket,
            {
                "type": "action",
                "session_id": session_id,
                "action": "completed",
                "content": "Ready for your next instruction.",
            },
        )
