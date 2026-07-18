"""Application lifecycle events."""

from __future__ import annotations

import logging
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

    # Startup: verify DB connection
    from app.core.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        logger.info("Database connection verified")
    except Exception as e:
        logger.warning("Database not reachable at startup: %s", e)

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.app_name)
    await engine.dispose()
    logger.info("Database connections closed")
