"""WebSocket terminal handler — live command execution in workspace."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from typing import Any

from fastapi import WebSocket

from app.core.config import settings
from app.services.docker_service import DockerService
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class TerminalWebSocketHandler:
    """
    Handles WebSocket terminal connections.
    Allows executing commands in workspace containers and streaming output.
    """

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.docker = DockerService()

    async def handle_terminal(
        self,
        websocket: WebSocket,
        project_id: str,
        container_name: str | None = None,
    ) -> None:
        """Handle terminal WebSocket connection."""
        await websocket.accept()

        try:
            while True:
                data = await websocket.receive_text()
                command_data = json.loads(data)

                command = command_data.get("command", "")
                if not command:
                    continue

                if command.strip().lower() == "exit":
                    await websocket.send_json({"type": "exit", "content": "Terminal closed"})
                    break

                # Execute command in container (or locally if no container)
                if container_name:
                    result = await self.docker.execute_command(container_name, command)
                    output = result["output"]
                else:
                    # Local execution fallback
                    try:
                        process = await asyncio.create_subprocess_shell(
                            command,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.STDOUT,
                            cwd=settings.workspace_base_path,
                        )
                        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
                        output = stdout.decode("utf-8", errors="replace") if stdout else ""
                    except asyncio.TimeoutError:
                        output = "Command timed out (30s limit)\n"
                    except Exception as e:
                        output = f"Error: {e}\n"

                # Send output back
                await websocket.send_json({
                    "type": "output",
                    "content": output,
                })

        except Exception as e:
            logger.error(f"Terminal error for project {project_id}: {e}")
            try:
                await websocket.send_json({"type": "error", "content": str(e)})
            except Exception:
                pass
