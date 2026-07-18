"""Workspace orchestrator — manages per-project Docker Compose lifecycle."""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.project import Project
from app.models.workspace import WorkspaceInstance
from app.services.docker_service import DockerService

logger = logging.getLogger(__name__)


class WorkspaceOrchestrator:
    """
    Creates and manages isolated Docker environments per project.

    Each workspace gets:
    - Its own Docker network
    - Its own containers (backend, frontend, db, redis)
    - Its own volumes
    - Resource limits
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.docker = DockerService()

    async def provision_workspace(
        self,
        project: Project,
        backend_image: str = "apex-workspace-backend:latest",
        frontend_image: str = "apex-workspace-frontend:latest",
    ) -> WorkspaceInstance:
        """Create a full workspace environment for a project."""
        project_slug = project.name.lower().replace(" ", "-")[:50]
        ws_id = str(project.id).split("-")[0]
        prefix = f"apex-{ws_id}"

        # Create or get existing instance
        result = await self.db.execute(
            select(WorkspaceInstance).where(WorkspaceInstance.project_id == project.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.status == "running":
                return existing
            await self._cleanup_instance(existing)

        # Create network
        network_name = f"{prefix}-net"
        network_id = await self.docker.create_network(network_name)

        workspace_path = Path(settings.workspace_base_path) / str(project.id)
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Prepare volume binds
        volumes = {
            str(workspace_path / "backend"): {"bind": "/app/backend", "mode": "rw"},
            str(workspace_path / "frontend"): {"bind": "/app/frontend", "mode": "rw"},
        }

        container_names = {}

        # Create workspace instance record
        instance = WorkspaceInstance(
            project_id=project.id,
            status="creating",
            network_name=network_name,
            container_names=container_names,
            volumes={
                "workspace_path": str(workspace_path),
                "backend": str(workspace_path / "backend"),
                "frontend": str(workspace_path / "frontend"),
            },
            resource_limits={
                "cpu": 0.5,
                "memory": "512m",
                "disk": "1g",
            },
        )
        self.db.add(instance)
        await self.db.flush()

        # Create workspace backend container
        try:
            backend_container = await self.docker.create_container(
                image=backend_image,
                name=f"{prefix}-backend",
                network=network_name,
                volumes=volumes,
                environment={
                    "APP_ENV": "development",
                    "PROJECT_ID": str(project.id),
                    "DATABASE_URL": f"postgresql+asyncpg://workspace:workspace@{prefix}-db:5432/workspace",
                    "REDIS_URL": f"redis://{prefix}-redis:6379/0",
                },
                mem_limit="512m",
                cpu_limit=0.5,
                ports={8000: None},  # Dynamic port
            )
            container_names["backend"] = backend_container.name
            backend_port = list(backend_container.attrs["NetworkSettings"]["Ports"].values())[0][0]["HostPort"]

            # Create workspace frontend container
            frontend_container = await self.docker.create_container(
                image=frontend_image,
                name=f"{prefix}-frontend",
                network=network_name,
                volumes=volumes,
                environment={
                    "API_URL": f"http://backend:{backend_port}",
                },
                mem_limit="256m",
                cpu_limit=0.25,
                ports={80: None},  # Dynamic port
            )
            container_names["frontend"] = frontend_container.name

            # Update instance with container info
            instance.container_names = container_names
            instance.status = "running"
            await self.db.flush()

            logger.info(f"Workspace provisioned for project {project.id}: {container_names}")

        except Exception as e:
            instance.status = "failed"
            instance.metadata = {"error": str(e)}
            await self.db.flush()
            logger.error(f"Failed to provision workspace for {project.id}: {e}")
            raise

        return instance

    async def stop_workspace(self, project_id: str) -> bool:
        """Stop all containers for a project workspace."""
        instance = await self._get_instance(project_id)
        if not instance:
            return False

        container_names = instance.container_names or {}
        for name in container_names.values():
            await self.docker.stop_container(name)

        instance.status = "stopped"
        await self.db.flush()
        logger.info(f"Workspace stopped for project {project_id}")
        return True

    async def start_workspace(self, project_id: str) -> bool:
        """Start all containers for a project workspace."""
        instance = await self._get_instance(project_id)
        if not instance:
            return False

        # Re-create containers
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return False

        await self.provision_workspace(project)
        return True

    async def restart_workspace(self, project_id: str) -> bool:
        """Restart all containers."""
        await self.stop_workspace(project_id)
        return await self.start_workspace(project_id)

    async def get_workspace_status(self, project_id: str) -> dict | None:
        """Get status of all containers in a workspace."""
        instance = await self._get_instance(project_id)
        if not instance:
            return None

        container_names = instance.container_names or {}
        statuses = {}
        for role, name in container_names.items():
            status = await self.docker.get_container_status(name)
            usage = await self.docker.get_resource_usage(name)
            statuses[role] = {
                "container_name": name,
                "status": status,
                "resources": usage,
            }

        return {
            "instance_id": str(instance.id),
            "project_id": project_id,
            "workspace_status": instance.status,
            "containers": statuses,
        }

    async def get_workspace_logs(self, project_id: str, tail: int = 100) -> dict[str, str]:
        """Get logs from all containers."""
        instance = await self._get_instance(project_id)
        if not instance:
            return {"error": "Workspace not found"}

        container_names = instance.container_names or {}
        logs = {}
        for role, name in container_names.items():
            logs[role] = await self.docker.get_container_logs(name, tail=tail)

        return logs

    async def destroy_workspace(self, project_id: str) -> bool:
        """Completely remove a workspace and its resources."""
        instance = await self._get_instance(project_id)
        if not instance:
            return False

        await self._cleanup_instance(instance)

        if instance.network_name:
            await self.docker.remove_network(instance.network_name)

        await self.db.delete(instance)
        await self.db.flush()
        logger.info(f"Workspace destroyed for project {project_id}")
        return True

    async def _get_instance(self, project_id: str) -> WorkspaceInstance | None:
        result = await self.db.execute(
            select(WorkspaceInstance).where(WorkspaceInstance.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def _cleanup_instance(self, instance: WorkspaceInstance) -> None:
        """Stop and remove all containers."""
        container_names = instance.container_names or {}
        for name in container_names.values():
            await self.docker.stop_container(name)
            await self.docker.remove_container(name)

        instance.status = "stopped"
        await self.db.flush()
