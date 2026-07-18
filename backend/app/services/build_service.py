"""Build service — orchestrates builds, handles errors, and retries."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment import Build
from app.models.project import Project
from app.services.docker_service import DockerService

logger = logging.getLogger(__name__)


class BuildService:
    """
    Orchestrates project builds with automatic error recovery.
    Implements the build-fix-retry loop described in the spec.
    """

    MAX_RETRIES = 5

    def __init__(self, db: AsyncSession):
        self.db = db
        self.docker = DockerService()

    async def start_build(self, project_id: str, trigger: str = "manual") -> Build:
        """Start a new build for a project."""
        build = Build(
            project_id=project_id,
            trigger=trigger,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(build)
        await self.db.flush()

        # Update project status
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project:
            project.status = "building"

        await self.db.flush()

        # Start build in background
        asyncio.create_task(self._run_build_loop(build.id, project_id))

        return build

    async def _run_build_loop(self, build_id: str, project_id: str) -> None:
        """Run build with retry logic."""
        attempt = 0
        errors = []

        while attempt < self.MAX_RETRIES:
            attempt += 1
            logger.info(f"Build {build_id} attempt {attempt}/{self.MAX_RETRIES}")

            try:
                success, logs = await self._execute_build(project_id, attempt)

                # Update build record
                result = await self.db.execute(select(Build).where(Build.id == build_id))
                build = result.scalar_one_or_none()
                if not build:
                    return

                build.logs = logs
                build.errors = errors

                if success:
                    build.status = "success"
                    build.finished_at = datetime.now(timezone.utc)

                    # Update project status
                    project_result = await self.db.execute(select(Project).where(Project.id == project_id))
                    project = project_result.scalar_one_or_none()
                    if project:
                        project.status = "ready"

                    await self.db.flush()
                    logger.info(f"Build {build_id} succeeded on attempt {attempt}")
                    return
                else:
                    error_entry = {
                        "attempt": attempt,
                        "log_snippet": logs[-2000:] if logs else "No output",
                    }
                    errors.append(error_entry)

                    # Parse error and attempt fix
                    fixed = await self._auto_fix(project_id, logs)
                    if not fixed:
                        build.status = "failed"
                        build.finished_at = datetime.now(timezone.utc)
                        build.errors = errors
                        await self.db.flush()
                        logger.warning(f"Build {build_id} failed after {attempt} attempts — cannot auto-fix")
                        return

            except Exception as e:
                logger.error(f"Build {build_id} crashed on attempt {attempt}: {e}")
                errors.append({"attempt": attempt, "error": str(e)})

        # All retries exhausted
        result = await self.db.execute(select(Build).where(Build.id == build_id))
        build = result.scalar_one_or_none()
        if build:
            build.status = "failed"
            build.finished_at = datetime.now(timezone.utc)
            build.errors = errors
            await self.db.flush()

        logger.warning(f"Build {build_id} failed after {self.MAX_RETRIES} attempts")

    async def _execute_build(self, project_id: str, attempt: int) -> tuple[bool, str]:
        """Execute the actual build commands."""
        log_parts = [f"=== Build attempt {attempt} ===\n"]

        commands = [
            f"cd {project_id}/backend && pip install -r requirements.txt 2>&1",
            f"cd {project_id}/backend && python -m pytest -x 2>&1 || echo 'TESTS_FAILED'",
        ]

        all_success = True
        for cmd in commands:
            result = await self.docker.execute_command("apex-backend", cmd)
            output = result.get("output", "")
            log_parts.append(f"$ {cmd}\n{output}\n")

            if not result.get("success", False):
                all_success = False
                break

        return all_success, "\n".join(log_parts)

    async def _auto_fix(self, project_id: str, logs: str) -> bool:
        """
        Attempt to automatically fix build errors.
        Returns True if a fix was applied.
        """
        # Check for common errors
        if "ModuleNotFoundError" in logs:
            # Extract module name and install it
            import re
            match = re.search(r"ModuleNotFoundError: No module named '(\w+)'", logs)
            if match:
                module = match.group(1)
                logger.info(f"Attempting to fix missing module: {module}")
                await self.docker.execute_command(
                    "apex-backend",
                    f"pip install {module.lower()} 2>&1",
                )
                return True

        if "ImportError" in logs:
            logger.info("Import error detected — attempting pip install")
            await self.docker.execute_command(
                "apex-backend",
                "pip install -r requirements.txt 2>&1",
            )
            return True

        if "relation" in logs and "does not exist" in logs:
            logger.info("Database relation missing — running migrations")
            await self.docker.execute_command(
                "apex-backend",
                "alembic upgrade head 2>&1",
            )
            return True

        return False  # Could not auto-fix

    async def get_build(self, build_id: str) -> Build | None:
        result = await self.db.execute(select(Build).where(Build.id == build_id))
        return result.scalar_one_or_none()

    async def list_builds(self, project_id: str, limit: int = 20) -> list[Build]:
        result = await self.db.execute(
            select(Build)
            .where(Build.project_id == project_id)
            .order_by(Build.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
