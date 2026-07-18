"""Authentication service — registration, login, token management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.workspace import Workspace
from app.services.email_service import EmailService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str | None = None,
    ) -> tuple[User, Organization, str, str]:
        """Register a new user, create their organization and default workspace."""
        # Check existing user
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("A user with this email already exists")

        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()

        # Create organization
        org_name = organization_name or f"{full_name}'s Organization"
        org_slug = org_name.lower().replace(" ", "-").replace("'", "")[:255]
        org = Organization(
            name=org_name,
            slug=org_slug,
            owner_id=user.id,
        )
        self.db.add(org)
        await self.db.flush()

        # Add user as owner member
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="owner",
            joined_at=datetime.now(timezone.utc),
        )
        self.db.add(member)

        # Create default workspace
        workspace = Workspace(
            organization_id=org.id,
            name="Default Workspace",
            description="Your default workspace",
        )
        self.db.add(workspace)
        await self.db.flush()

        # Generate tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        return user, org, access_token, refresh_token

    async def login(
        self, email: str, password: str
    ) -> tuple[User, str, str] | None:
        """Authenticate user and return tokens."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            raise ValueError("Account is deactivated")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return user, access_token, refresh_token

    async def refresh_token(self, refresh_token: str) -> tuple[str, str] | None:
        """Issue a new access token using a valid refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Verify user still exists
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            return None

        new_access = create_access_token(subject=str(user.id))
        new_refresh = create_refresh_token(subject=str(user.id))
        return new_access, new_refresh

    async def verify_email(self, token: str) -> bool:
        """Verify user email address."""
        payload = decode_token(token)
        if not payload or payload.get("type") != "email_verify":
            return False

        user_id = payload.get("sub")
        if not user_id:
            return False

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.email_verified_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def forgot_password(self, email: str) -> bool:
        """Send password reset email."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return False  # Don't reveal if user exists

        reset_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(hours=1),
        )
        # TODO: Send email with reset link
        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using a valid reset token."""
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return False

        user_id = payload.get("sub")
        if not user_id:
            return False

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.password_hash = get_password_hash(new_password)
        await self.db.flush()
        return True
