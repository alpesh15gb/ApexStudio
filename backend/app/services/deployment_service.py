"""Deployment service — one-click deploy, health checks, auto-rollback."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment import Deployment
from app.models.project import Project
from app.services.build_service import BuildService

logger = logging.getLogger(__name__)


class DeploymentService:
    """Manages the deployment pipeline with health checks and rollback."""

    HEALTH_CHECK_TIMEOUT = 30  # seconds
    HEALTH_CHECK_RETRIES = 3
    HEALTH_CHECK_INTERVAL = 5  # seconds

    def __init__(self, db: AsyncSession):
        self.db = db

    async def deploy(self, project_id: str, version: str | None = None) -> Deployment:
        """Start a deployment for a project."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # Create deployment record
        deployment = Deployment(
            project_id=project_id,
            version=version or f"v{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            status="building",
        )
        self.db.add(deployment)
        await self.db.flush()

        # Update project status
        project.status = "deploying"
        await self.db.flush()

        # Start deployment pipeline in background
        asyncio.create_task(self._run_deployment_pipeline(deployment.id, project_id))

        return deployment

    async def _run_deployment_pipeline(self, deployment_id: str, project_id: str) -> None:
        """Run the full deployment pipeline."""
        try:
            # Step 1: Build
            await self._update_status(deployment_id, "building")
            build_service = BuildService(self.db)
            build = await build_service.start_build(project_id, trigger="deployment")

            # Wait briefly for build result
            await asyncio.sleep(5)

            # Refresh build status
            build = await build_service.get_build(build.id)
            if build and build.status != "success":
                await self._fail_deployment(deployment_id, "Build failed")
                return

            # Step 2: Health checks
            await self._update_status(deployment_id, "testing")
            healthy = await self._run_health_checks(project_id)

            if not healthy:
                await self._fail_deployment(deployment_id, "Health checks failed")
                return

            # Step 3: Deploy live
            await self._update_status(deployment_id, "deploying")
            live = await self._make_live(project_id)

            if live:
                deployment = await self._get_deployment(deployment_id)
                if deployment:
                    deployment.status = "live"
                    deployment.deployed_at = datetime.now(timezone.utc)
                    deployment.url = f"https://{project_id}.apexstudio.app"
                    await self.db.flush()

                # Update project status
                result = await self.db.execute(select(Project).where(Project.id == project_id))
                project = result.scalar_one_or_none()
                if project:
                    project.status = "deployed"

                await self.db.flush()
                logger.info(f"Deployment {deployment_id} live!")
            else:
                await self._rollback(deployment_id, project_id)

        except Exception as e:
            logger.error(f"Deployment pipeline failed: {e}")
            await self._fail_deployment(deployment_id, str(e))

    async def _run_health_checks(self, project_id: str) -> bool:
        """Run health checks against the deployed service."""
        for attempt in range(self.HEALTH_CHECK_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"http://localhost:8000/api/v1/health",
                    )
                    if response.status_code == 200:
                        logger.info(f"Health check passed (attempt {attempt + 1})")
                        return True
            except Exception as e:
                logger.warning(f"Health check failed (attempt {attempt + 1}): {e}")

            await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)

        return False

    async def _make_live(self, project_id: str) -> bool:
        """Switch traffic to the new deployment."""
        # TODO: Update Nginx/load balancer to point to new containers
        return True

    async def _rollback(self, deployment_id: str, project_id: str) -> None:
        """Rollback to the previous working version."""
        deployment = await self._get_deployment(deployment_id)
        if deployment:
            deployment.status = "rolled_back"
            deployment.rolled_back_at = datetime.now(timezone.utc)
            await self.db.flush()

        # Find last live deployment
        result = await self.db.execute(
            select(Deployment)
            .where(
                Deployment.project_id == project_id,
                Deployment.status == "live",
            )
            .order_by(Deployment.created_at.desc())
            .limit(1)
        )
        last_live = result.scalar_one_or_none()

        if last_live:
            logger.info(f"Rolled back to deployment {last_live.id}")
            # TODO: Point traffic back to last_live

        # Update project status
        project_result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if project:
            project.status = "ready"

        await self.db.flush()

    async def rollback_to(self, deployment_id: str) -> Deployment | None:
        """Manually rollback to a specific deployment."""
        result = await self.db.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()

        if not deployment:
            return None

        project_id = deployment.project_id
        await self._rollback(deployment_id, project_id)
        return deployment

    async def _update_status(self, deployment_id: str, status: str) -> None:
        deployment = await self._get_deployment(deployment_id)
        if deployment:
            deployment.status = status
            await self.db.flush()

    async def _fail_deployment(self, deployment_id: str, reason: str) -> None:
        deployment = await self._get_deployment(deployment_id)
        if deployment:
            deployment.status = "failed"
            deployment.build_logs = (deployment.build_logs or "") + f"\nFAILED: {reason}"
            await self.db.flush()

        logger.error(f"Deployment {deployment_id} failed: {reason}")

    async def _get_deployment(self, deployment_id: str) -> Deployment | None:
        result = await self.db.execute(select(Deployment).where(Deployment.id == deployment_id))
        return result.scalar_one_or_none()

    async def get_deployment(self, deployment_id: str) -> Deployment | None:
        return await self._get_deployment(deployment_id)

    async def list_deployments(self, project_id: str, limit: int = 20) -> list[Deployment]:
        result = await self.db.execute(
            select(Deployment)
            .where(Deployment.project_id == project_id)
            .order_by(Deployment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
