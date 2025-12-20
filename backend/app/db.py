from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from backend.app.core.config import settings


def _normalize_db_url(url: str) -> str:
    # Ensure sqlite file paths are usable regardless of current working directory.
    if not url.startswith("sqlite"):
        return url

    if url.startswith("sqlite:////"):
        file_path = "/" + url.removeprefix("sqlite:////")
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        return url

    if url.startswith("sqlite:///"):
        # relative path; resolve relative to repo root (/workspace in this environment)
        rel = url.removeprefix("sqlite:///")
        repo_root = Path(__file__).resolve().parents[2]
        abs_path = (repo_root / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:////{abs_path.as_posix().lstrip('/')}"

    return url


_DB_URL = _normalize_db_url(settings.DB_URL)

engine = create_engine(
    _DB_URL,
    connect_args={"check_same_thread": False} if _DB_URL.startswith("sqlite") else {},
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Session:
    with Session(engine) as session:
        yield session

