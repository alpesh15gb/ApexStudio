"""Authentication schemas."""

from __future__ import annotations

from app.schemas import BaseSchema


class LoginRequest(BaseSchema):
    email: str
    password: str


class RegisterRequest(BaseSchema):
    email: str
    full_name: str
    password: str
    organization_name: str | None = None


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class ForgotPasswordRequest(BaseSchema):
    email: str


class ResetPasswordRequest(BaseSchema):
    token: str
    password: str


class VerifyEmailRequest(BaseSchema):
    token: str
