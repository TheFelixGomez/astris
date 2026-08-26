from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application and framework configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core Application
    app_name: str = "Astris Application"
    app_env: str = "local"
    app_debug: bool = True
    app_key: str = ""

    # Database
    database_url: str = "sqlite:///database/app.db"
    db_echo: bool = False
    auto_create_tables: bool = True

    # Sessions & Security
    session_cookie_name: str = "astris_session"
    session_max_age: int | None = 14 * 24 * 60 * 60  # 14 days
    session_https_only: bool = False
    session_same_site: Literal["lax", "strict", "none"] = "lax"

    # CORS & CSRF
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    enable_csrf: bool = True
    csrf_exempt_paths: list[str] = []


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()


# Global settings singleton
settings = get_settings()
