"""Project schemas."""

from __future__ import annotations

from app.schemas import BaseSchema, TimestampSchema, UUIDBaseSchema


class ProjectCreateRequest(BaseSchema):
    name: str
    description: str | None = None
    app_type: str | None = None


class ProjectUpdateRequest(BaseSchema):
    name: str | None = None
    description: str | None = None
    app_type: str | None = None


class ProjectResponse(UUIDBaseSchema, TimestampSchema):
    workspace_id: str
    name: str
    description: str | None = None
    status: str
    app_type: str | None = None
    metadata: dict | None = None


class ProjectRequirementResponse(BaseSchema):
    target_users: str | None = None
    platforms: list | None = None
    countries: list | None = None
    languages: list | None = None
    auth_type: str | None = None
    payment_providers: list | None = None
    integrations: list | None = None
    branding: dict | None = None


class ProjectPlanResponse(BaseSchema):
    id: str
    project_id: str
    functional_reqs: list | None = None
    non_functional_reqs: list | None = None
    user_stories: list | None = None
    database_schema: dict | None = None
    api_spec: dict | None = None
    folder_structure: dict | None = None
    ui_navigation: list | None = None
    roadmap: list | None = None
    milestones: list | None = None
    risks: list | None = None
    approved: bool
    approved_at: str | None = None
