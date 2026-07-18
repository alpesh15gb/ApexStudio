"""Database engine and session configuration."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Create engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    poolclass=NullPool if settings.is_production else None,
    pool_size=20 if not settings.is_production else None,
    max_overflow=10 if not settings.is_production else None,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Alias for get_session, for FastAPI dependency injection."""
    async for session in get_session():
        yield session
