"""Organization schemas."""

from __future__ import annotations

from datetime import datetime

from app.schemas import BaseSchema, TimestampSchema, UUIDBaseSchema


class OrganizationCreateRequest(BaseSchema):
    name: str
    slug: str | None = None


class OrganizationUpdateRequest(BaseSchema):
    name: str | None = None
    logo_url: str | None = None


class OrganizationResponse(UUIDBaseSchema, TimestampSchema):
    name: str
    slug: str
    owner_id: str
    logo_url: str | None = None


class OrganizationMemberResponse(BaseSchema):
    id: str
    organization_id: str
    user_id: str
    role: str
    email: str | None = None
    full_name: str | None = None
    invited_at: datetime | None = None
    joined_at: datetime | None = None


class InviteMemberRequest(BaseSchema):
    email: str
    role: str = "member"
