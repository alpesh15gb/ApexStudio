"""WebSocket connection manager for real-time communication."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections grouped by project.
    Supports broadcasting and targeted messages.
    """

    def __init__(self):
        # project_id -> list of WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}
        # user_id -> list of connections
        self._user_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if project_id not in self._connections:
            self._connections[project_id] = []
        self._connections[project_id].append(websocket)
        logger.info(f"WebSocket connected: project={project_id}, total={len(self._connections[project_id])}")

    async def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        """Remove a WebSocket connection."""
        if project_id in self._connections:
            if websocket in self._connections[project_id]:
                self._connections[project_id].remove(websocket)
            if not self._connections[project_id]:
                del self._connections[project_id]
        logger.info(f"WebSocket disconnected: project={project_id}")

    async def send_to_project(self, project_id: str, message: dict) -> None:
        """Send a message to all connections for a project."""
        if project_id not in self._connections:
            return

        dead_connections = []
        for connection in self._connections[project_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            await self.disconnect(conn, project_id)

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

    def get_project_connections(self, project_id: str) -> list[WebSocket]:
        """Get all connections for a project."""
        return self._connections.get(project_id, [])

    @property
    def active_connections(self) -> int:
        """Get total active connections."""
        return sum(len(conns) for conns in self._connections.values())

    @property
    def active_projects(self) -> list[str]:
        """Get list of projects with active connections."""
        return list(self._connections.keys())
