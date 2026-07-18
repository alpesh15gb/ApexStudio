"""Build API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.deployment import BuildResponse
from app.services.build_service import BuildService

build_router = APIRouter(prefix="/builds", tags=["builds"])


@build_router.post("/{project_id}/start")
async def start_build(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new build for a project."""
    service = BuildService(db)
    build = await service.start_build(project_id, trigger="manual")
    return {"message": "Build started", "build_id": str(build.id)}


@build_router.get("/{project_id}", response_model=list[BuildResponse])
async def list_builds(
    project_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List builds for a project."""
    service = BuildService(db)
    return await service.list_builds(project_id, limit=limit)


@build_router.get("/detail/{build_id}")
async def get_build(
    build_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get build details."""
    service = BuildService(db)
    build = await service.get_build(build_id)
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")
    return build
