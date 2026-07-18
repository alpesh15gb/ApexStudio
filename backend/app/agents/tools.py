"""Tool registry — all tools available to AI agents."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from app.core.config import settings
from app.services.docker_service import DockerService

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of tools that agents can use to interact with workspaces."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register all available tools."""
        self.register("read_file", self.read_file)
        self.register("write_file", self.write_file)
        self.register("edit_file", self.edit_file)
        self.register("delete_file", self.delete_file)
        self.register("rename_file", self.rename_file)
        self.register("list_files", self.list_files)
        self.register("execute_command", self.execute_command)
        self.register("run_build", self.run_build)
        self.register("run_tests", self.run_tests)
        self.register("read_logs", self.read_logs)
        self.register("list_containers", self.list_containers)

    def register(self, name: str, func: Callable) -> None:
        """Register a tool by name."""
        self._tools[name] = func
        logger.debug(f"Registered tool: {name}")

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    async def execute(self, name: str, **kwargs) -> Any:
        """Execute a registered tool."""
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}

        try:
            logger.info(f"Executing tool: {name} with kwargs={kwargs}")
            result = await self._tools[name](**kwargs)
            return result
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return {"error": str(e)}

    # --- Tool Implementations ---

    async def read_file(self, path: str, project_id: str | None = None) -> str:
        """Read a file from the workspace."""
        full_path = self._resolve_path(path, project_id)
        if not full_path.exists():
            return f"File not found: {path}"
        return full_path.read_text(encoding="utf-8", errors="replace")

    async def write_file(self, path: str, content: str, project_id: str | None = None) -> dict:
        """Write content to a file."""
        full_path = self._resolve_path(path, project_id)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(full_path), "size": len(content)}

    async def edit_file(self, path: str, old_string: str, new_string: str, project_id: str | None = None) -> dict:
        """Replace text in a file."""
        full_path = self._resolve_path(path, project_id)
        if not full_path.exists():
            return {"error": f"File not found: {path}"}

        content = full_path.read_text(encoding="utf-8")
        if old_string not in content:
            return {"error": f"String not found in file: {old_string[:50]}"}

        new_content = content.replace(old_string, new_string, 1)
        full_path.write_text(new_content, encoding="utf-8")
        return {"success": True, "path": str(full_path)}

    async def delete_file(self, path: str, project_id: str | None = None) -> dict:
        """Delete a file."""
        full_path = self._resolve_path(path, project_id)
        if not full_path.exists():
            return {"error": f"File not found: {path}"}

        full_path.unlink()
        return {"success": True, "path": str(full_path)}

    async def rename_file(self, path: str, new_path: str, project_id: str | None = None) -> dict:
        """Rename/move a file."""
        full_path = self._resolve_path(path, project_id)
        full_new_path = self._resolve_path(new_path, project_id)

        if not full_path.exists():
            return {"error": f"File not found: {path}"}

        full_new_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.rename(full_new_path)
        return {"success": True, "from": str(full_path), "to": str(full_new_path)}

    async def list_files(self, path: str = "", project_id: str | None = None) -> list:
        """List files in a directory."""
        full_path = self._resolve_path(path, project_id)
        if not full_path.exists() or not full_path.is_dir():
            return {"error": f"Directory not found: {path}"}

        items = []
        for item in sorted(full_path.iterdir()):
            items.append({
                "name": item.name,
                "path": str(item.relative_to(settings.workspace_path)),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return items

    async def execute_command(self, command: str, container_name: str | None = None) -> dict:
        """Execute a command (in container or locally)."""
        if container_name:
            docker = DockerService()
            return await docker.execute_command(container_name, command)

        # Local execution fallback
        import asyncio
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(settings.workspace_path),
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=60)
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            return {
                "exit_code": process.returncode or 0,
                "output": output,
                "success": process.returncode == 0,
            }
        except asyncio.TimeoutError:
            return {"exit_code": -1, "output": "Command timed out (60s)", "success": False}
        except Exception as e:
            return {"exit_code": -1, "output": str(e), "success": False}

    async def run_build(self, project_id: str) -> dict:
        """Run build command for a project."""
        cmd = f"cd {settings.workspace_base_path}/{project_id} && docker-compose build 2>&1"
        return await self.execute_command(cmd)

    async def run_tests(self, project_id: str) -> dict:
        """Run tests for a project."""
        cmd = f"cd {settings.workspace_base_path}/{project_id}/backend && python -m pytest 2>&1"
        return await self.execute_command(cmd)

    async def read_logs(self, container_name: str, tail: int = 100) -> str:
        """Read logs from a container."""
        docker = DockerService()
        return await docker.get_container_logs(container_name, tail=tail)

    async def list_containers(self, project_id: str) -> list:
        """List containers for a project workspace."""
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.models.workspace import WorkspaceInstance

        # TODO: Proper DB session injection
        return {"note": "Use workspace status endpoint instead"}

    def _resolve_path(self, path: str, project_id: str | None = None) -> Path:
        """Resolve a user-provided path to an absolute workspace path."""
        base = settings.workspace_path
        if project_id:
            base = base / project_id
        # Prevent path traversal
        full = (base / path).resolve()
        if not str(full).startswith(str(base)):
            raise PermissionError(f"Path traversal detected: {path}")
        return full
