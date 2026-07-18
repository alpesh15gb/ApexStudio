"""Workspace service — CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, organization_id: str, name: str, description: str | None = None, settings: dict | None = None
    ) -> Workspace:
        workspace = Workspace(
            organization_id=organization_id,
            name=name,
            description=description,
            settings=settings or {},
        )
        self.db.add(workspace)
        await self.db.flush()
        return workspace

    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        result = await self.db.execute(select(Workspace).where(Workspace.id == workspace_id))
        return result.scalar_one_or_none()

    async def list_by_organization(self, org_id: str) -> list[Workspace]:
        result = await self.db.execute(
            select(Workspace).where(Workspace.organization_id == org_id).order_by(Workspace.created_at)
        )
        return list(result.scalars().all())

    async def update(
        self, workspace_id: str, name: str | None = None, description: str | None = None, settings: dict | None = None
    ) -> Workspace | None:
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return None
        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        if settings is not None:
            workspace.settings = settings
        await self.db.flush()
        return workspace

    async def delete(self, workspace_id: str) -> bool:
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return False
        await self.db.delete(workspace)
        await self.db.flush()
        return True
