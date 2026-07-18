"""Project, requirements, and plan models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace, WorkspaceInstance
    from app.models.deployment import Deployment, Build


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "discovering",
            "planning",
            "building",
            "ready",
            "deploying",
            "deployed",
            "failed",
            name="project_status",
        ),
        nullable=False,
        default="draft",
    )
    app_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="projects")
    requirements: Mapped[List["ProjectRequirement"]] = relationship(
        "ProjectRequirement", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    plan: Mapped[List["ProjectPlan"]] = relationship(
        "ProjectPlan", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    workspace_instance: Mapped["WorkspaceInstance"] = relationship(
        "WorkspaceInstance", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment", back_populates="project", cascade="all, delete-orphan"
    )
    builds: Mapped[List["Build"]] = relationship(
        "Build", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    target_users: Mapped[str | None] = mapped_column(Text, nullable=True)
    platforms: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    countries: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    languages: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    auth_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_providers: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    integrations: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    branding: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="requirements")


class ProjectPlan(Base):
    __tablename__ = "project_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    functional_reqs: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    non_functional_reqs: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    user_stories: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    database_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    api_spec: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    folder_structure: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    ui_navigation: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    roadmap: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    milestones: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    risks: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="plan")
