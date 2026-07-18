"""User schemas."""

from __future__ import annotations

from datetime import datetime

from app.schemas import BaseSchema, TimestampSchema, UUIDBaseSchema


class UserResponse(UUIDBaseSchema, TimestampSchema):
    email: str
    full_name: str
    avatar_url: str | None = None
    is_active: bool
    email_verified_at: datetime | None = None


class UserUpdateRequest(BaseSchema):
    full_name: str | None = None
    avatar_url: str | None = None
