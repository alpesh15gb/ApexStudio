"""Billing API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.billing import BillingProfileResponse, CheckoutSessionRequest, CheckoutSessionResponse
from app.services.billing_service import BillingService

billing_router = APIRouter(prefix="/billing", tags=["billing"])


@billing_router.get("/profile/{organization_id}", response_model=BillingProfileResponse)
async def get_billing_profile(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get billing profile for an organization."""
    service = BillingService(db)
    profile = await service.get_or_create_profile(organization_id)
    return profile


@billing_router.get("/limits/{organization_id}")
async def get_limits(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage limits for an organization."""
    service = BillingService(db)
    return await service.get_limits(organization_id)


@billing_router.post("/upgrade/{organization_id}")
async def upgrade_plan(
    organization_id: str,
    plan: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade/downgrade plan."""
    service = BillingService(db)
    try:
        profile = await service.update_plan(organization_id, plan)
        return {"message": f"Plan updated to {plan}", "plan": profile.plan}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@billing_router.post("/cancel/{organization_id}")
async def cancel_subscription(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel subscription."""
    service = BillingService(db)
    await service.cancel_subscription(organization_id)
    return {"message": "Subscription cancelled"}


@billing_router.post("/checkout")
async def create_checkout(
    request: CheckoutSessionRequest,
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session."""
    service = BillingService(db)
    result = await service.create_checkout_session(organization_id, request.price_id)
    return result


@billing_router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.json()
    service = BillingService(db)
    await service.handle_webhook(payload)
    return {"received": True}
