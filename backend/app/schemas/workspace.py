"""Workspace schemas."""

from __future__ import annotations

from app.schemas import BaseSchema, TimestampSchema, UUIDBaseSchema


class WorkspaceCreateRequest(BaseSchema):
    name: str
    description: str | None = None
    settings: dict | None = None


class WorkspaceUpdateRequest(BaseSchema):
    name: str | None = None
    description: str | None = None
    settings: dict | None = None


class WorkspaceResponse(UUIDBaseSchema, TimestampSchema):
    organization_id: str
    name: str
    description: str | None = None
    settings: dict | None = None


class WorkspaceInstanceResponse(BaseSchema):
    id: str
    project_id: str
    status: str
    container_names: dict | None = None
    network_name: str | None = None
    resource_limits: dict | None = None
    created_at: str
