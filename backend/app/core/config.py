from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DATA_DIR = _REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PDP_", case_sensitive=False)

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    JWT_ALG: str = "HS256"

    # Storage/DB
    DB_URL: str = f"sqlite:////{(_DEFAULT_DATA_DIR / 'app.sqlite3').as_posix().lstrip('/')}"
    NOTEBOOK_STORAGE_DIR: str = str(_DEFAULT_DATA_DIR / "notebooks")

    # API
    CORS_ORIGINS: str = "*"  # comma-separated OR '*' for local dev


settings = Settings()  # type: ignore[call-arg]

