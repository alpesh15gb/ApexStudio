"""Planning service — AI generates and manages implementation plans."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectPlan


class PlanningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_plan(self, project_id: str) -> ProjectPlan | None:
        """Get the implementation plan for a project."""
        result = await self.db.execute(
            select(ProjectPlan).where(ProjectPlan.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def save_plan(
        self,
        project_id: str,
        functional_reqs: list | None = None,
        non_functional_reqs: list | None = None,
        user_stories: list | None = None,
        database_schema: dict | None = None,
        api_spec: dict | None = None,
        folder_structure: dict | None = None,
        ui_navigation: list | None = None,
        roadmap: list | None = None,
        milestones: list | None = None,
        risks: list | None = None,
    ) -> ProjectPlan:
        """Save or update an implementation plan."""
        existing = await self.get_plan(project_id)

        if existing:
            if functional_reqs is not None:
                existing.functional_reqs = functional_reqs
            if non_functional_reqs is not None:
                existing.non_functional_reqs = non_functional_reqs
            if user_stories is not None:
                existing.user_stories = user_stories
            if database_schema is not None:
                existing.database_schema = database_schema
            if api_spec is not None:
                existing.api_spec = api_spec
            if folder_structure is not None:
                existing.folder_structure = folder_structure
            if ui_navigation is not None:
                existing.ui_navigation = ui_navigation
            if roadmap is not None:
                existing.roadmap = roadmap
            if milestones is not None:
                existing.milestones = milestones
            if risks is not None:
                existing.risks = risks
            existing.approved = False
            existing.approved_at = None
            await self.db.flush()
            return existing

        plan = ProjectPlan(
            project_id=project_id,
            functional_reqs=functional_reqs or [],
            non_functional_reqs=non_functional_reqs or [],
            user_stories=user_stories or [],
            database_schema=database_schema or {},
            api_spec=api_spec or {},
            folder_structure=folder_structure or {},
            ui_navigation=ui_navigation or [],
            roadmap=roadmap or [],
            milestones=milestones or [],
            risks=risks or [],
        )
        self.db.add(plan)

        # Update project status
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project:
            project.status = "planning"

        await self.db.flush()
        return plan

    async def approve_plan(self, project_id: str) -> ProjectPlan | None:
        """Mark a plan as approved and update project status."""
        plan = await self.get_plan(project_id)
        if not plan:
            return None

        plan.approved = True
        plan.approved_at = datetime.now(timezone.utc)

        # Update project status to building-ready
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project:
            project.status = "ready"

        await self.db.flush()
        return plan
