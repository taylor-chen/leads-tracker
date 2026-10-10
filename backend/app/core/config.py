from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables (and `.env` if present)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Leads Tracker API"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./leads.db"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    # Comma-separated list of allowed origins.
    cors_origins: str = "http://localhost:3000"

    upload_dir: str = "./uploads"
    max_resume_bytes: int = 5 * 1024 * 1024

    email_backend: Literal["smtp", "console"] = "console"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_ssl: bool = False
    smtp_starttls: bool = False
    email_from: str = "Leads Tracker <no-reply@leads.local>"
    attorney_notification_email: str = "attorney@example.com"

    # Used to build links in outgoing emails.
    frontend_base_url: str = "http://localhost:3000"

    # Optional bootstrap user, created on startup by `python -m app.cli seed`.
    seed_attorney_email: str | None = None
    seed_attorney_password: str | None = None
    seed_attorney_name: str = "Default Attorney"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
