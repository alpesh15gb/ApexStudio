"""Pydantic schemas base."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None


class UUIDBaseSchema(BaseSchema):
    id: UUID
