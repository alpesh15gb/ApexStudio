"""Docker SDK service — manage containers programmatically."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from app.core.config import settings

logger = logging.getLogger(__name__)


class DockerService:
    """Wrapper around Docker SDK for workspace container management."""

    def __init__(self):
        self._client: docker.DockerClient | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.DockerClient(base_url=settings.docker_host)
        return self._client

    async def check_connection(self) -> bool:
        """Verify Docker daemon is reachable."""
        try:
            self.client.ping()
            return True
        except DockerException as e:
            logger.error(f"Docker daemon unreachable: {e}")
            return False

    async def create_network(self, name: str) -> str:
        """Create a Docker network for workspace isolation."""
        try:
            network = self.client.networks.create(name, driver="bridge", check_duplicate=True)
            logger.info(f"Created network: {name}")
            return network.id
        except docker.errors.APIError as e:
            if "already exists" in str(e):
                logger.info(f"Network {name} already exists")
                return self.client.networks.get(name).id
            raise

    async def remove_network(self, name: str) -> None:
        """Remove a Docker network."""
        try:
            network = self.client.networks.get(name)
            network.remove()
            logger.info(f"Removed network: {name}")
        except NotFound:
            logger.warning(f"Network {name} not found")

    async def create_container(
        self,
        image: str,
        name: str,
        command: list[str] | None = None,
        environment: dict[str, str] | None = None,
        volumes: dict[str, dict] | None = None,
        network: str | None = None,
        ports: dict[str, int] | None = None,
        mem_limit: str = "512m",
        cpu_limit: float = 0.5,
        detach: bool = True,
    ) -> Container:
        """Create and start a Docker container."""
        container_kwargs: dict[str, Any] = {
            "image": image,
            "name": name,
            "detach": detach,
            "mem_limit": mem_limit,
            "nano_cpus": int(cpu_limit * 1e9),
        }

        if command:
            container_kwargs["command"] = command
        if environment:
            container_kwargs["environment"] = environment
        if volumes:
            container_kwargs["volumes"] = volumes
        if network:
            container_kwargs["network"] = network
        if ports:
            container_kwargs["ports"] = ports

        try:
            container = self.client.containers.create(**container_kwargs)
            container.start()
            logger.info(f"Created container: {name} (image: {image})")
            return container
        except DockerException as e:
            logger.error(f"Failed to create container {name}: {e}")
            raise

    async def stop_container(self, name_or_id: str) -> bool:
        """Stop a container."""
        try:
            container = self.client.containers.get(name_or_id)
            container.stop(timeout=10)
            logger.info(f"Stopped container: {name_or_id}")
            return True
        except NotFound:
            logger.warning(f"Container {name_or_id} not found")
            return False
        except DockerException as e:
            logger.error(f"Failed to stop container {name_or_id}: {e}")
            return False

    async def remove_container(self, name_or_id: str, force: bool = True) -> bool:
        """Remove a container."""
        try:
            container = self.client.containers.get(name_or_id)
            container.remove(force=force)
            logger.info(f"Removed container: {name_or_id}")
            return True
        except NotFound:
            logger.warning(f"Container {name_or_id} not found")
            return False
        except DockerException as e:
            logger.error(f"Failed to remove container {name_or_id}: {e}")
            return False

    async def get_container_status(self, name_or_id: str) -> str | None:
        """Get container status (running, stopped, etc.)."""
        try:
            container = self.client.containers.get(name_or_id)
            return container.status
        except NotFound:
            return None

    async def get_container_logs(self, name_or_id: str, tail: int = 100) -> str:
        """Get container logs."""
        try:
            container = self.client.containers.get(name_or_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode("utf-8", errors="replace") if logs else ""
        except NotFound:
            return f"Container {name_or_id} not found"
        except DockerException as e:
            return f"Error fetching logs: {e}"

    async def execute_command(self, container_name: str, command: str) -> dict:
        """Execute a command inside a running container."""
        try:
            container = self.client.containers.get(container_name)
            exit_code, output = container.exec_run(
                ["/bin/sh", "-c", command],
                demux=False,
            )
            stdout = output.decode("utf-8", errors="replace") if output else ""
            return {
                "exit_code": exit_code,
                "output": stdout,
                "success": exit_code == 0,
            }
        except NotFound:
            return {"exit_code": -1, "output": f"Container {container_name} not found", "success": False}
        except DockerException as e:
            return {"exit_code": -1, "output": str(e), "success": False}

    async def pull_image(self, image: str) -> bool:
        """Pull a Docker image."""
        try:
            logger.info(f"Pulling image: {image}")
            self.client.images.pull(image)
            return True
        except DockerException as e:
            logger.error(f"Failed to pull image {image}: {e}")
            return False

    async def get_resource_usage(self, container_name: str) -> dict | None:
        """Get CPU/memory stats for a container."""
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - (
                stats["precpu_stats"]["cpu_usage"]["total_usage"]
                if "precpu_stats" in stats
                else 0
            )
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - (
                stats["precpu_stats"]["system_cpu_usage"]
                if "precpu_stats" in stats
                else 0
            )
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                num_cpus = stats["cpu_stats"].get("online_cpus", 1)
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

            memory_stats = stats.get("memory_stats", {})
            mem_usage = memory_stats.get("usage", 0)
            mem_limit = memory_stats.get("limit", 1)
            mem_percent = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_bytes": mem_usage,
                "memory_limit": mem_limit,
                "memory_percent": round(mem_percent, 2),
            }
        except (NotFound, DockerException) as e:
            logger.warning(f"Failed to get resource usage for {container_name}: {e}")
            return None

    async def cleanup_workspace(self, workspace_prefix: str) -> dict:
        """Stop and remove all containers for a workspace."""
        results = {"stopped": [], "removed": [], "errors": []}
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"name": workspace_prefix},
            )
            for container in containers:
                try:
                    container.stop(timeout=10)
                    results["stopped"].append(container.name)
                except DockerException as e:
                    results["errors"].append(f"stop {container.name}: {e}")

                try:
                    container.remove(force=True)
                    results["removed"].append(container.name)
                except DockerException as e:
                    results["errors"].append(f"remove {container.name}: {e}")
        except DockerException as e:
            results["errors"].append(str(e))

        return results
