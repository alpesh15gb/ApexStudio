"""Billing schemas."""

from __future__ import annotations

from app.schemas import BaseSchema, TimestampSchema, UUIDBaseSchema


class BillingProfileResponse(UUIDBaseSchema, TimestampSchema):
    organization_id: str
    plan: str
    stripe_customer_id: str | None = None
    status: str
    trial_ends_at: str | None = None
    current_period_end: str | None = None


class CheckoutSessionRequest(BaseSchema):
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseSchema):
    url: str
    session_id: str
