"""Common/shared schemas."""

from __future__ import annotations

from app.schemas import BaseSchema


class SuccessResponse(BaseSchema):
    message: str = "Operation completed successfully"
    data: dict | None = None


class ErrorResponse(BaseSchema):
    error: ErrorDetail


class ErrorDetail(BaseSchema):
    message: str
    code: int
    details: dict | None = None


class PaginatedResponse(BaseSchema):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseSchema):
    status: str
    version: str
    environment: str
