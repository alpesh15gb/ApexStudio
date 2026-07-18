"""Workspace runtime API endpoints — start/stop/restart/logs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.workspace import WorkspaceInstanceResponse
from app.services.workspace_orchestrator import WorkspaceOrchestrator
from app.services.project_service import ProjectService

ws_runtime_router = APIRouter(prefix="/workspace-runtime", tags=["workspace-runtime"])


@ws_runtime_router.post("/{project_id}/start")
async def start_workspace(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start the workspace for a project."""
    orchestrator = WorkspaceOrchestrator(db)
    project_service = ProjectService(db)

    project = await project_service.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    instance = await orchestrator.provision_workspace(project)
    return {"message": "Workspace started", "status": instance.status}


@ws_runtime_router.post("/{project_id}/stop")
async def stop_workspace(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop the workspace for a project."""
    orchestrator = WorkspaceOrchestrator(db)
    success = await orchestrator.stop_workspace(project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return {"message": "Workspace stopped"}


@ws_runtime_router.post("/{project_id}/restart")
async def restart_workspace(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restart the workspace for a project."""
    orchestrator = WorkspaceOrchestrator(db)
    success = await orchestrator.restart_workspace(project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return {"message": "Workspace restarted"}


@ws_runtime_router.get("/{project_id}/status")
async def get_workspace_status(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workspace status including container states."""
    orchestrator = WorkspaceOrchestrator(db)
    status_data = await orchestrator.get_workspace_status(project_id)
    if not status_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return status_data


@ws_runtime_router.get("/{project_id}/logs")
async def get_workspace_logs(
    project_id: str,
    tail: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workspace logs from all containers."""
    orchestrator = WorkspaceOrchestrator(db)
    logs = await orchestrator.get_workspace_logs(project_id, tail=tail)
    return logs


@ws_runtime_router.delete("/{project_id}")
async def destroy_workspace(
    project_id: str,
    confirm: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Destroy workspace (requires confirmation)."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Destruction requires confirmation. Set confirm=true to proceed.",
        )
    orchestrator = WorkspaceOrchestrator(db)
    if not await orchestrator.get_workspace_status(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    await orchestrator.destroy_workspace(project_id)
    return {"message": "Workspace destroyed"}
