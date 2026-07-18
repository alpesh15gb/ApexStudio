"""Deployment schemas."""

from __future__ import annotations

from app.schemas import BaseSchema, TimestampSchema, UUIDBaseSchema


class DeploymentResponse(UUIDBaseSchema, TimestampSchema):
    project_id: str
    version: str
    status: str
    url: str | None = None
    health_check_path: str | None = None
    build_logs: str | None = None
    deployed_at: str | None = None


class BuildResponse(BaseSchema):
    id: str
    project_id: str
    trigger: str
    status: str
    commit_hash: str | None = None
    logs: str | None = None
    errors: list | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str
