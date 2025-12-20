from __future__ import annotations

import os
from pathlib import Path

from backend.app.core.config import settings


def ensure_platform_storage() -> None:
    Path(settings.NOTEBOOK_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    Path("./data/platform/files").mkdir(parents=True, exist_ok=True)
    Path("./data/platform/runs").mkdir(parents=True, exist_ok=True)
    Path("./data/platform/scripts").mkdir(parents=True, exist_ok=True)


def content_file_path(*, content_item_id: str, original_filename: str) -> str:
    safe_name = Path(original_filename).name or "upload.bin"
    return str(Path("./data/platform/files") / f"{content_item_id}__{safe_name}")


def script_source_path(*, content_item_id: str, runtime: str) -> str:
    ext = "py" if runtime == "python3" else "sh"
    return str(Path("./data/platform/scripts") / f"{content_item_id}.{ext}")


def run_log_paths(*, run_id: str) -> tuple[str, str]:
    out = str(Path("./data/platform/runs") / f"{run_id}.stdout.log")
    err = str(Path("./data/platform/runs") / f"{run_id}.stderr.log")
    return out, err


def safe_unlink(path: str | None) -> None:
    if not path:
        return
    try:
        os.remove(path)
    except FileNotFoundError:
        return

