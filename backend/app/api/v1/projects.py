"""Project management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectPlanResponse,
    ProjectRequirementResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.discovery_service import DiscoveryService
from app.services.planning_service import PlanningService
from app.services.project_service import ProjectService

project_router = APIRouter(prefix="/projects", tags=["projects"])


@project_router.get("", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List projects in a workspace."""
    service = ProjectService(db)
    return await service.list_by_workspace(workspace_id)


@project_router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    service = ProjectService(db)
    project = await service.create(
        workspace_id=workspace_id,
        name=request.name,
        description=request.description,
        app_type=request.app_type,
    )
    return project


@project_router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details."""
    service = ProjectService(db)
    project = await service.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@project_router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project."""
    service = ProjectService(db)
    project = await service.update(
        project_id,
        name=request.name,
        description=request.description,
        app_type=request.app_type,
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@project_router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    confirm: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project. Requires confirm=true."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion requires confirmation. Set confirm=true to proceed.",
        )
    service = ProjectService(db)
    success = await service.delete(project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return {"message": "Project deleted"}


# --- Discovery Endpoints ---


@project_router.get("/{project_id}/discovery/questions")
async def get_discovery_questions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the AI discovery questions for a project."""
    service = DiscoveryService(db)
    return {"questions": await service.get_questions()}


@project_router.get("/{project_id}/discovery/requirements", response_model=ProjectRequirementResponse | None)
async def get_requirements(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get saved requirements for a project."""
    service = DiscoveryService(db)
    return await service.get_requirements(project_id)


@project_router.post("/{project_id}/discovery/requirements")
async def save_requirements(
    project_id: str,
    requirements: ProjectRequirementResponse,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save AI-gathered requirements for a project."""
    service = DiscoveryService(db)
    reqs = await service.save_requirements(project_id=project_id, **requirements.model_dump(exclude_none=True))
    return reqs


# --- Planning Endpoints ---


@project_router.get("/{project_id}/plan", response_model=ProjectPlanResponse | None)
async def get_plan(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the implementation plan for a project."""
    service = PlanningService(db)
    return await service.get_plan(project_id)


@project_router.post("/{project_id}/plan/save")
async def save_plan(
    project_id: str,
    plan: ProjectPlanResponse,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save/update the implementation plan."""
    service = PlanningService(db)
    saved = await service.save_plan(
        project_id=project_id,
        functional_reqs=plan.functional_reqs,
        non_functional_reqs=plan.non_functional_reqs,
        user_stories=plan.user_stories,
        database_schema=plan.database_schema,
        api_spec=plan.api_spec,
        folder_structure=plan.folder_structure,
        ui_navigation=plan.ui_navigation,
        roadmap=plan.roadmap,
        milestones=plan.milestones,
        risks=plan.risks,
    )
    return saved


@project_router.post("/{project_id}/plan/approve")
async def approve_plan(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve the implementation plan and move to ready status."""
    service = PlanningService(db)
    plan = await service.approve_plan(project_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No plan found for this project")
    return {"message": "Plan approved", "approved": True}
