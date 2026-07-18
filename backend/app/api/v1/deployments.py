"""Deployment API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.deployment import DeploymentResponse
from app.services.deployment_service import DeploymentService

deployment_router = APIRouter(prefix="/deployments", tags=["deployments"])


@deployment_router.post("/{project_id}/deploy")
async def deploy_project(
    project_id: str,
    version: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deploy a project."""
    service = DeploymentService(db)
    try:
        deployment = await service.deploy(project_id, version=version)
        return {"message": "Deployment started", "deployment_id": str(deployment.id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@deployment_router.get("/{project_id}", response_model=list[DeploymentResponse])
async def list_deployments(
    project_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List deployments for a project."""
    service = DeploymentService(db)
    return await service.list_deployments(project_id, limit=limit)


@deployment_router.get("/detail/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get deployment details."""
    service = DeploymentService(db)
    deployment = await service.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@deployment_router.post("/rollback/{deployment_id}")
async def rollback_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rollback to a specific deployment."""
    service = DeploymentService(db)
    deployment = await service.rollback_to(deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return {"message": "Rollback initiated", "deployment_id": str(deployment.id)}
