"""File management schemas."""

from __future__ import annotations

from app.schemas import BaseSchema


class FileTreeItem(BaseSchema):
    name: str
    path: str
    type: str  # "file" or "directory"
    children: list["FileTreeItem"] | None = None
    size: int | None = None
    mime_type: str | None = None


class FileCreateRequest(BaseSchema):
    path: str
    content: str


class FileUpdateRequest(BaseSchema):
    path: str
    content: str


class FileRenameRequest(BaseSchema):
    path: str
    new_path: str


class FileDeleteRequest(BaseSchema):
    path: str


class FileContentResponse(BaseSchema):
    path: str
    content: str
    size: int
    mime_type: str | None = None
