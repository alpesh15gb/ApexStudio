"""Organization API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.organization import (
    InviteMemberRequest,
    OrganizationCreateRequest,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdateRequest,
)
from app.services.organization_service import OrganizationService
from app.services.user_service import UserService

org_router = APIRouter(prefix="/organizations", tags=["organizations"])


@org_router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List organizations the current user belongs to."""
    service = OrganizationService(db)
    return await service.list_for_user(user_id=str(current_user.id))


@org_router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new organization."""
    service = OrganizationService(db)
    org = await service.create(
        name=request.name,
        slug=request.slug,
        owner_id=str(current_user.id),
    )
    return org


@org_router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details."""
    service = OrganizationService(db)
    org = await service.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@org_router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    request: OrganizationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update organization."""
    service = OrganizationService(db)
    org = await service.update(org_id, name=request.name, logo_url=request.logo_url)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@org_router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete organization."""
    service = OrganizationService(db)

    # Only owner can delete
    org = await service.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if str(org.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete the organization")

    await service.delete(org_id)
    return {"message": "Organization deleted"}


@org_router.get("/{org_id}/members", response_model=list[OrganizationMemberResponse])
async def list_members(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List organization members."""
    service = OrganizationService(db)
    return await service.get_members(org_id)


@org_router.post("/{org_id}/members", response_model=OrganizationMemberResponse)
async def invite_member(
    org_id: str,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a member to the organization."""
    org_service = OrganizationService(db)
    user_service = UserService(db)

    user = await user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    member = await org_service.add_member(
        org_id=org_id,
        user_id=str(user.id),
        role=request.role,
        invited_by=str(current_user.id),
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    members = await org_service.get_members(org_id)
    for m in members:
        if m["user_id"] == str(user.id):
            return m
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@org_router.delete("/{org_id}/members/{user_id}")
async def remove_member(
    org_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the organization."""
    service = OrganizationService(db)

    # Cannot remove self as owner
    if user_id == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove yourself")

    success = await service.remove_member(org_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return {"message": "Member removed"}
