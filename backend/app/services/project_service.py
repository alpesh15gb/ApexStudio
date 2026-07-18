"""Project service — CRUD and status management."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: str,
        name: str,
        description: str | None = None,
        app_type: str | None = None,
    ) -> Project:
        project = Project(
            workspace_id=workspace_id,
            name=name,
            description=description,
            app_type=app_type,
            status="draft",
        )
        self.db.add(project)
        await self.db.flush()
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: str) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.updated_at.desc().nullslast(), Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        app_type: str | None = None,
        status: str | None = None,
    ) -> Project | None:
        project = await self.get_by_id(project_id)
        if not project:
            return None
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if app_type is not None:
            project.app_type = app_type
        if status is not None:
            project.status = status
        await self.db.flush()
        return project

    async def update_status(self, project_id: str, status: str) -> Project | None:
        return await self.update(project_id, status=status)

    async def delete(self, project_id: str) -> bool:
        project = await self.get_by_id(project_id)
        if not project:
            return False
        await self.db.delete(project)
        await self.db.flush()
        return True
