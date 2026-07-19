"""Initial database schema.

Revision ID: 001
Revises:
Create Date: 2026-07-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Organizations ---
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Organization Members ---
    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "member", name="org_role"), nullable=False, default="member"),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Workspaces ---
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("settings", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Projects ---
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("draft", "discovering", "planning", "building", "ready", "deploying", "deployed", "failed", name="project_status"), nullable=False, default="draft"),
        sa.Column("app_type", sa.String(100), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Project Requirements ---
    op.create_table(
        "project_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("target_users", sa.Text(), nullable=True),
        sa.Column("platforms", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("countries", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("languages", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("auth_type", sa.String(100), nullable=True),
        sa.Column("payment_providers", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("integrations", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("branding", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Project Plans ---
    op.create_table(
        "project_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("functional_reqs", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("non_functional_reqs", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("user_stories", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("database_schema", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("api_spec", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("folder_structure", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("ui_navigation", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("roadmap", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("milestones", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("risks", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("approved", sa.Boolean(), default=False, nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Workspace Instances ---
    op.create_table(
        "workspace_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.Enum("creating", "running", "stopping", "stopped", "failed", name="ws_instance_status"), nullable=False, default="creating"),
        sa.Column("container_names", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("docker_compose_content", sa.Text(), nullable=True),
        sa.Column("network_name", sa.String(255), nullable=True),
        sa.Column("volumes", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("resource_limits", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Deployments ---
    op.create_table(
        "deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("status", sa.Enum("building", "testing", "deploying", "live", "failed", "rolled_back", name="deployment_status"), nullable=False, default="building"),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("health_check_path", sa.String(255), nullable=True),
        sa.Column("build_logs", sa.Text(), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Builds ---
    op.create_table(
        "builds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("trigger", sa.Enum("manual", "auto", "deployment", name="build_trigger"), nullable=False, default="manual"),
        sa.Column("status", sa.Enum("pending", "running", "success", "failed", "cancelled", name="build_status"), nullable=False, default="pending"),
        sa.Column("commit_hash", sa.String(255), nullable=True),
        sa.Column("branch", sa.String(255), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("errors", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- AI Sessions ---
    op.create_table(
        "ai_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("mode", sa.Enum("plan", "build", "debug", name="ai_mode"), nullable=False, default="build"),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("status", sa.Enum("active", "paused", "completed", "failed", name="ai_session_status"), nullable=False, default="active"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("token_usage", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- AI Memories ---
    op.create_table(
        "ai_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_sessions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("role", sa.Enum("user", "assistant", "system", "tool", name="memory_role"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Project Files ---
    op.create_table(
        "project_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("path", sa.String(1000), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("hash", sa.String(64), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Billing Profiles ---
    op.create_table(
        "billing_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("plan", sa.Enum("free", "pro", "enterprise", name="billing_plan"), nullable=False, default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("status", sa.Enum("active", "past_due", "canceled", "trialing", name="billing_status"), nullable=False, default="active"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_data", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )

    # --- Billing Invoices ---
    op.create_table(
        "billing_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), default="usd", nullable=False),
        sa.Column("status", sa.Enum("draft", "open", "paid", "void", "uncollectible", name="invoice_status"), nullable=False, default="draft"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Indexes ---
    op.create_index("ix_project_files_project_path", "project_files", ["project_id", "path"])
    op.create_index("ix_ai_memories_project_session", "ai_memories", ["project_id", "session_id"])
    op.create_index("ix_deployments_project_created", "deployments", ["project_id", sa.text("created_at DESC")])
    op.create_index("ix_builds_project_created", "builds", ["project_id", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_table("billing_invoices")
    op.drop_table("billing_profiles")
    op.drop_table("project_files")
    op.drop_table("ai_memories")
    op.drop_table("ai_sessions")
    op.drop_table("builds")
    op.drop_table("deployments")
    op.drop_table("workspace_instances")
    op.drop_table("project_plans")
    op.drop_table("project_requirements")
    op.drop_table("projects")
    op.drop_table("workspaces")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS invoice_status")
    op.execute("DROP TYPE IF EXISTS billing_status")
    op.execute("DROP TYPE IF EXISTS billing_plan")
    op.execute("DROP TYPE IF EXISTS memory_role")
    op.execute("DROP TYPE IF EXISTS ai_session_status")
    op.execute("DROP TYPE IF EXISTS ai_mode")
    op.execute("DROP TYPE IF EXISTS build_status")
    op.execute("DROP TYPE IF EXISTS build_trigger")
    op.execute("DROP TYPE IF EXISTS deployment_status")
    op.execute("DROP TYPE IF EXISTS ws_instance_status")
    op.execute("DROP TYPE IF EXISTS project_status")
    op.execute("DROP TYPE IF EXISTS org_role")
