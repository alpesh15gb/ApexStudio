"""Workspace API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.services.workspace_service import WorkspaceService

workspace_router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@workspace_router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    organization_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List workspaces, optionally filtered by organization."""
    service = WorkspaceService(db)
    if organization_id:
        return await service.list_by_organization(organization_id)
    return []


@workspace_router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: WorkspaceCreateRequest,
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workspace in an organization."""
    service = WorkspaceService(db)
    return await service.create(
        organization_id=organization_id,
        name=request.name,
        description=request.description,
        settings=request.settings,
    )


@workspace_router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workspace details."""
    service = WorkspaceService(db)
    workspace = await service.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@workspace_router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    request: WorkspaceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace."""
    service = WorkspaceService(db)
    workspace = await service.update(
        workspace_id,
        name=request.name,
        description=request.description,
        settings=request.settings,
    )
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@workspace_router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete workspace."""
    service = WorkspaceService(db)
    success = await service.delete(workspace_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return {"message": "Workspace deleted"}
