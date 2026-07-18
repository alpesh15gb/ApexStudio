"""AI schemas."""

from __future__ import annotations

from app.schemas import BaseSchema, TimestampSchema, UUIDBaseSchema


class AISessionResponse(UUIDBaseSchema, TimestampSchema):
    project_id: str
    mode: str
    model: str
    status: str
    summary: str | None = None


class ChatMessageRequest(BaseSchema):
    message: str
    session_id: str | None = None


class ChatMessageResponse(BaseSchema):
    session_id: str
    message: str
    role: str


class AgentAction(BaseSchema):
    type: str  # "tool_call", "thought", "code", "result"
    content: str
    tool_name: str | None = None
    tool_input: dict | None = None
    tool_output: str | None = None
