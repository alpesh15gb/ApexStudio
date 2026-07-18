"""Organization service — CRUD and member management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization, OrganizationMember
from app.models.user import User


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, owner_id: str, slug: str | None = None) -> Organization:
        org_slug = slug or name.lower().replace(" ", "-").replace("'", "")[:255]
        org = Organization(name=name, slug=org_slug, owner_id=owner_id)
        self.db.add(org)
        await self.db.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=owner_id,
            role="owner",
            joined_at=datetime.now(timezone.utc),
        )
        self.db.add(member)
        await self.db.flush()
        return org

    async def get_by_id(self, org_id: str) -> Organization | None:
        result = await self.db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> list[Organization]:
        result = await self.db.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update(self, org_id: str, name: str | None = None, logo_url: str | None = None) -> Organization | None:
        org = await self.get_by_id(org_id)
        if not org:
            return None
        if name is not None:
            org.name = name
        if logo_url is not None:
            org.logo_url = logo_url
        await self.db.flush()
        return org

    async def delete(self, org_id: str) -> bool:
        org = await self.get_by_id(org_id)
        if not org:
            return False
        await self.db.delete(org)
        await self.db.flush()
        return True

    async def get_members(self, org_id: str) -> list[dict]:
        result = await self.db.execute(
            select(OrganizationMember, User.email, User.full_name)
            .join(User, OrganizationMember.user_id == User.id)
            .where(OrganizationMember.organization_id == org_id)
        )
        members = []
        for member, email, full_name in result:
            members.append({
                "id": str(member.id),
                "organization_id": str(member.organization_id),
                "user_id": str(member.user_id),
                "role": member.role,
                "email": email,
                "full_name": full_name,
                "invited_at": member.invited_at,
                "joined_at": member.joined_at,
            })
        return members

    async def add_member(self, org_id: str, user_id: str, role: str = "member", invited_by: str | None = None) -> OrganizationMember | None:
        # Check if already member
        result = await self.db.execute(
            select(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        if result.scalar_one_or_none():
            return None

        member = OrganizationMember(
            organization_id=org_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
            invited_at=datetime.now(timezone.utc),
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def remove_member(self, org_id: str, user_id: str) -> bool:
        result = await self.db.execute(
            select(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await self.db.delete(member)
        await self.db.flush()
        return True

    async def get_user_role(self, org_id: str, user_id: str) -> str | None:
        result = await self.db.execute(
            select(OrganizationMember.role)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
