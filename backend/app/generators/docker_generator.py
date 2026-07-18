"""Docker generator — generates Docker Compose and Dockerfiles."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.generators.base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class DockerGenerator(BaseGenerator):
    """Generates Docker configuration files."""

    def generate_docker_compose(self, app_name: str = "app") -> Path:
        """Generate docker-compose.yml for the workspace project."""
        content = f"""version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: {app_name}-backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/{app_name}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: {app_name}-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    container_name: {app_name}-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: {app_name}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: {app_name}-redis
    restart: unless-stopped

volumes:
  pgdata:
"""
        return self.write_file("docker-compose.yml", content)
