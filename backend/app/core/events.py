"""Application lifecycle events."""

from __future__ import annotations

import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info(
        "Starting %s in %s mode",
        settings.app_name,
        settings.app_env,
    )

    # Startup: run DB migrations
    try:
        logger.info("Running database migrations...")
        proc = await asyncio.create_subprocess_exec(
            "alembic", "upgrade", "head",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        if proc.returncode == 0:
            logger.info("Migrations complete")
        else:
            output = stdout.decode() if stdout else ""
            logger.error("Migration failed: %s", output)
    except FileNotFoundError:
        logger.warning("alembic not found — skipping migrations")
    except Exception as e:
        logger.warning("Migration error (non-fatal): %s", e)

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.app_name)
    from app.core.database import engine
    await engine.dispose()
    logger.info("Database connections closed")
