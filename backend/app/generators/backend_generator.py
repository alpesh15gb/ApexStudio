"""Backend code generator — generates FastAPI application code."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.generators.base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class BackendGenerator(BaseGenerator):
    """Generates FastAPI backend code from an architectural plan."""

    def generate_project_structure(self) -> list[Path]:
        """Generate the basic backend project structure."""
        created = []

        # Root files
        created.append(self.write_file("backend/requirements.txt", self._get_requirements()))
        created.append(self.write_file("backend/Dockerfile", self._get_dockerfile()))

        # App package
        created.append(self.write_file("backend/app/__init__.py", ""))
        created.append(self.write_file("backend/app/main.py", self._get_main_py()))
        created.append(self.write_file("backend/app/core/__init__.py", ""))

        # Core modules
        created.append(self.write_file("backend/app/core/config.py", self._get_config_py()))
        created.append(self.write_file("backend/app/core/database.py", self._get_database_py()))
        created.append(self.write_file("backend/app/core/security.py", self._get_security_py()))

        # Models
        created.append(self.write_file("backend/app/models/__init__.py", ""))
        created.append(self.write_file("backend/app/models/user.py", self._get_user_model()))

        # API
        created.append(self.write_file("backend/app/api/__init__.py", ""))
        created.append(self.write_file("backend/app/api/v1/__init__.py", ""))
        created.append(self.write_file("backend/app/api/v1/router.py", self._get_router_py()))

        # Alembic
        created.append(self.write_file("backend/alembic.ini", ""))
        created.append(self.write_file("backend/alembic/env.py", ""))
        created.append(self.write_file("backend/alembic/script.py.mako", ""))

        logger.info(f"Generated backend structure: {len(created)} files")
        return created

    def _get_requirements(self) -> str:
        return """fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.9.0
pydantic-settings==2.5.0
python-multipart==0.0.9
redis==5.1.1
httpx==0.27.2
"""

    def _get_dockerfile(self) -> str:
        return """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    def _get_main_py(self) -> str:
        return '''"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="My App", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
'''

    def _get_config_py(self) -> str:
        return '''"""Application configuration."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My App"
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"

settings = Settings()
'''

    def _get_database_py(self) -> str:
        return '''"""Database configuration."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
'''

    def _get_security_py(self) -> str:
        return '''"""Security utilities."""
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
'''

    def _get_user_model(self) -> str:
        return '''"""User model."""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
'''

    def _get_router_py(self) -> str:
        return '''"""API router."""
from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/health")
async def health():
    return {"status": "ok"}
'''
