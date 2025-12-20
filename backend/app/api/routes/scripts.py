from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, HTTPException, status

from backend.app.api.deps import SessionDep
from backend.app.models import ContentItem, ScriptRun, ScriptRunPublic, ScriptRunRequest
from backend.app.storage.platform import run_log_paths, script_source_path

router = APIRouter(prefix="/scripts", tags=["scripts"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/items/{item_id}/runs", response_model=ScriptRunPublic, status_code=status.HTTP_201_CREATED)
async def run_script(session: SessionDep, item_id: str, payload: ScriptRunRequest) -> ScriptRunPublic:
    item = session.get(ContentItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.type != "script":
        raise HTTPException(status_code=400, detail="Item is not a script")

    runtime = (item.script_runtime or "python3").strip()
    if runtime not in {"python3", "bash"}:
        raise HTTPException(status_code=400, detail="Unsupported script runtime")

    run = ScriptRun(content_item_id=item.id, started_at=_utcnow(), status="running", args_json=json.dumps(payload.args))
    session.add(run)
    session.commit()
    session.refresh(run)

    # Write script to disk (so we can run it)
    src_path = script_source_path(content_item_id=item.id, runtime=runtime)
    async with aiofiles.open(src_path, "w", encoding="utf-8") as f:
        await f.write(item.script_source or "")

    stdout_path, stderr_path = run_log_paths(run_id=run.id)
    run.stdout_path = stdout_path
    run.stderr_path = stderr_path
    session.add(run)
    session.commit()

    cmd = [runtime, src_path, *payload.args]
    proc = subprocess.Popen(
        cmd,
        stdout=open(stdout_path, "wb"),
        stderr=open(stderr_path, "wb"),
        cwd="./data/platform",
    )

    if payload.detach:
        # Keep it simple: detached run stays "running" until user polls and we see it finished.
        return ScriptRunPublic(
            id=run.id,
            content_item_id=run.content_item_id,
            started_at=run.started_at,
            finished_at=run.finished_at,
            status=run.status,
            exit_code=run.exit_code,
        )

    try:
        exit_code = proc.wait(timeout=max(1, int(payload.timeout_seconds)))
    except subprocess.TimeoutExpired:
        proc.kill()
        exit_code = -9

    run.exit_code = exit_code
    run.finished_at = _utcnow()
    run.status = "finished" if exit_code == 0 else "failed"
    session.add(run)
    session.commit()
    session.refresh(run)

    return ScriptRunPublic(
        id=run.id,
        content_item_id=run.content_item_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=run.status,
        exit_code=run.exit_code,
    )


@router.get("/runs/{run_id}", response_model=ScriptRunPublic)
def get_run(session: SessionDep, run_id: str) -> ScriptRunPublic:
    run = session.get(ScriptRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return ScriptRunPublic(
        id=run.id,
        content_item_id=run.content_item_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=run.status,
        exit_code=run.exit_code,
    )


@router.get("/runs/{run_id}/logs")
async def get_run_logs(session: SessionDep, run_id: str, max_bytes: int = 200_000) -> dict[str, str]:
    run = session.get(ScriptRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def _read(path: str | None) -> str:
        if not path:
            return ""
        try:
            async with aiofiles.open(path, "rb") as f:
                data = await f.read(max_bytes)
            return data.decode("utf-8", errors="replace")
        except FileNotFoundError:
            return ""

    return {"stdout": await _read(run.stdout_path), "stderr": await _read(run.stderr_path)}

