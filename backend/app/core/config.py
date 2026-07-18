"""Application configuration via environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Apex Studio"
    app_env: str = "development"
    app_secret_key: str = "change-this-to-a-random-secret-key"
    app_debug: bool = True
    app_log_level: str = "DEBUG"
    app_cors_origins: str = "http://localhost:8080,http://localhost:3000"

    # URLs
    app_api_url: str = "http://localhost:8000"
    app_frontend_url: str = "http://localhost:8080"
    app_preview_domain: str = "localhost"

    # Database
    database_url: str = "postgresql+asyncpg://apex:apex@localhost:5432/apex_studio"
    database_sync_url: str = "postgresql://apex:apex@localhost:5432/apex_studio"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = "change-this-to-a-jwt-secret-key"

    # Docker
    docker_host: str = "unix:///var/run/docker.sock"
    docker_network_name: str = "apex_network"
    workspace_base_path: str = "./workspaces"

    # S3 / Object Storage
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "apex-studio"
    s3_region: str = "us-east-1"
    s3_secure: bool = False

    # AI / Omniroute
    omniroute_api_key: str = ""
    omniroute_base_url: str = "https://api.omniroute.ai/v1"
    omniroute_default_model: str = "claude-sonnet-5"
    omniroute_fallback_model: str = "gpt-4o"

    # SMTP / Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "noreply@apexstudio.com"

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_free: Optional[str] = None
    stripe_price_pro: Optional[str] = None
    stripe_price_enterprise: Optional[str] = None

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace_base_path).resolve()

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()
