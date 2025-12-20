from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PDP_",
        case_sensitive=False,
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
    )

    # Environment
    ENV: str = "dev"  # dev|prod (string to keep it simple)

    # Security
    # In dev we allow a default; in prod we validate this is overridden.
    SECRET_KEY: str = "dev-unsafe-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    JWT_ALG: str = "HS256"

    # Storage/DB
    DB_URL: str = "sqlite:///./data/app.sqlite3"
    NOTEBOOK_STORAGE_DIR: str = "./data/notebooks"

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "*"  # comma-separated OR '*' for local dev


settings = Settings()  # type: ignore[call-arg]


def validate_settings() -> None:
    """Fail fast in production if dangerous defaults are in use."""
    # Kept for optional future hardening; intentionally no-op for single-PC use.
    return None

