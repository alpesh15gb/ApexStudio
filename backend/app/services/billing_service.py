"""Billing service — Stripe integration, plan management, usage tracking."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.billing import BillingInvoice, BillingProfile

logger = logging.getLogger(__name__)


class BillingService:
    """Manages billing profiles, subscriptions, and invoices via Stripe."""

    FREE_LIMITS = {"projects": 3, "builds_per_month": 30, "storage_gb": 1, "ai_tokens": 500000}
    PRO_LIMITS = {"projects": 20, "builds_per_month": 500, "storage_gb": 10, "ai_tokens": 5000000}
    ENTERPRISE_LIMITS = {"projects": 100, "builds_per_month": -1, "storage_gb": 100, "ai_tokens": -1}

    PLAN_LIMITS = {
        "free": FREE_LIMITS,
        "pro": PRO_LIMITS,
        "enterprise": ENTERPRISE_LIMITS,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, organization_id: str) -> BillingProfile:
        """Get or create a billing profile for an organization."""
        result = await self.db.execute(
            select(BillingProfile).where(BillingProfile.organization_id == organization_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = BillingProfile(
                organization_id=organization_id,
                plan="free",
                status="active",
            )
            self.db.add(profile)
            await self.db.flush()

        return profile

    async def get_profile(self, organization_id: str) -> BillingProfile | None:
        result = await self.db.execute(
            select(BillingProfile).where(BillingProfile.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def update_plan(self, organization_id: str, plan: str) -> BillingProfile | None:
        if plan not in self.PLAN_LIMITS:
            raise ValueError(f"Invalid plan: {plan}")

        profile = await self.get_or_create_profile(organization_id)
        profile.plan = plan
        await self.db.flush()
        return profile

    async def cancel_subscription(self, organization_id: str) -> BillingProfile | None:
        profile = await self.get_or_create_profile(organization_id)
        profile.plan = "free"
        profile.status = "canceled"
        await self.db.flush()
        return profile

    async def get_limits(self, organization_id: str) -> dict:
        profile = await self.get_or_create_profile(organization_id)
        return self.PLAN_LIMITS.get(profile.plan, self.FREE_LIMITS)

    async def track_usage(self, organization_id: str, metric: str, amount: int = 1) -> None:
        """Track usage metrics for billing."""
        profile = await self.get_or_create_profile(organization_id)
        usage = profile.usage_data or {}
        usage[metric] = usage.get(metric, 0) + amount
        profile.usage_data = usage
        await self.db.flush()

    async def check_usage_limit(self, organization_id: str, metric: str) -> bool:
        """Check if usage is within plan limits."""
        limits = await self.get_limits(organization_id)
        max_allowed = limits.get(metric, -1)

        if max_allowed == -1:
            return True  # Unlimited

        profile = await self.get_or_create_profile(organization_id)
        usage = profile.usage_data or {}
        current = usage.get(metric, 0)

        return current < max_allowed

    # --- Stripe integration (stubs) ---

    async def create_checkout_session(self, organization_id: str, price_id: str) -> dict:
        """Create a Stripe checkout session."""
        if not settings.stripe_secret_key:
            return {"url": "#", "session_id": "stub"}
        # TODO: Implement Stripe checkout
        return {"url": "#", "session_id": "stub"}

    async def handle_webhook(self, payload: dict) -> bool:
        """Handle Stripe webhook events."""
        event_type = payload.get("type", "")
        logger.info(f"Stripe webhook: {event_type}")
        # TODO: Handle subscription updates, invoices, etc.
        return True

    async def get_invoices(self, organization_id: str) -> list[BillingInvoice]:
        result = await self.db.execute(
            select(BillingInvoice)
            .where(BillingInvoice.organization_id == organization_id)
            .order_by(BillingInvoice.created_at.desc())
        )
        return list(result.scalars().all())
