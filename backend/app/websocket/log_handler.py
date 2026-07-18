"""WebSocket log handler — streams build and container logs."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from app.services.docker_service import DockerService
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class LogWebSocketHandler:
    """
    Streams container and build logs to the client in real-time.
    """

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.docker = DockerService()

    async def handle_logs(
        self,
        websocket: WebSocket,
        project_id: str,
        source: str = "backend",  # backend, frontend, build, all
    ) -> None:
        """Stream logs from a workspace container."""
        await websocket.accept()

        try:
            # Get workspace containers
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import select
            from app.models.workspace import WorkspaceInstance

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(WorkspaceInstance).where(WorkspaceInstance.project_id == project_id)
                )
                instance = result.scalar_one_or_none()

            if not instance:
                await websocket.send_json({
                    "type": "error",
                    "content": "No workspace found for this project",
                })
                return

            container_names = instance.container_names or {}

            if source == "all":
                targets = list(container_names.values())
            elif source in container_names:
                targets = [container_names[source]]
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Unknown log source: {source}",
                })
                return

            # Stream logs (polling approach for now)
            last_positions = {name: 0 for name in targets}
            while True:
                for container_name in targets:
                    logs = await self.docker.get_container_logs(container_name, tail=50)

                    if logs:
                        await websocket.send_json({
                            "type": "log",
                            "source": container_name,
                            "content": logs,
                        })

                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Log stream error for project {project_id}: {e}")
        finally:
            try:
                await websocket.close()
            except Exception:
                pass
