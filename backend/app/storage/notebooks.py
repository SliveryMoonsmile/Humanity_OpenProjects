from __future__ import annotations

import os
from pathlib import Path

from backend.app.core.config import settings


def ensure_storage_root() -> None:
    Path(settings.NOTEBOOK_STORAGE_DIR).mkdir(parents=True, exist_ok=True)


def notebook_content_path(*, owner_id: str, notebook_id: str) -> str:
    # Keep paths deterministic and contained under storage dir.
    root = Path(settings.NOTEBOOK_STORAGE_DIR).resolve()
    owner_dir = (root / owner_id).resolve()
    if root not in owner_dir.parents and owner_dir != root:
        raise ValueError("Invalid owner_id path")

    owner_dir.mkdir(parents=True, exist_ok=True)
    p = owner_dir / f"{notebook_id}.ipynb"
    return str(p)


def safe_unlink(path: str | None) -> None:
    if not path:
        return
    try:
        os.remove(path)
    except FileNotFoundError:
        return

