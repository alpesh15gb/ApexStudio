"""Alembic environment configuration."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Alembic Config object
config = context.config

# Override DB URL from environment (for Docker networking)
sync_url = os.environ.get("DATABASE_SYNC_URL")
if sync_url:
    config.set_main_option("sqlalchemy.url", sync_url)

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Alembic can detect them
from app.core.database import Base
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.workspace import Workspace
from app.models.project import Project, ProjectRequirement, ProjectPlan
from app.models.billing import BillingProfile, BillingInvoice
from app.models.deployment import Deployment, Build
from app.models.ai import AISession, AIMemory
from app.models.file import ProjectFile
from app.models.workspace import WorkspaceInstance

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
