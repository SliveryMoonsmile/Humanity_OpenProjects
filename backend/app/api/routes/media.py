from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Iterator

import aiofiles
from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import select

from backend.app.api.deps import SessionDep
from backend.app.models import ContentItem
from backend.app.storage.platform import content_file_path

router = APIRouter(prefix="/media", tags=["media"])


@router.put("/items/{item_id}/file", status_code=status.HTTP_200_OK)
async def upload_item_file(session: SessionDep, item_id: str, file: UploadFile = File(...)) -> dict[str, str]:
    item = session.get(ContentItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    filename = file.filename or "upload.bin"
    dest = content_file_path(content_item_id=item.id, original_filename=filename)
    async with aiofiles.open(dest, "wb") as f:
        total = 0
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            await f.write(chunk)

    mt = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    item.file_path = dest
    item.file_name = Path(filename).name
    item.mime_type = mt
    item.file_size_bytes = total
    session.add(item)
    session.commit()
    return {"status": "ok", "item_id": item.id}


@router.get("/items/{item_id}/download")
def download_item_file(session: SessionDep, item_id: str) -> FileResponse:
    item = session.get(ContentItem, item_id)
    if not item or not item.file_path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=item.file_path,
        media_type=item.mime_type or "application/octet-stream",
        filename=item.file_name or Path(item.file_path).name,
    )


def _iter_file_range(path: str, start: int, end: int, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    with open(path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data


@router.get("/items/{item_id}/stream")
def stream_video(session: SessionDep, item_id: str, request: Request) -> Response:
    """
    Basic HTTP Range streaming (enables scrubbing in browser <video>).
    Works best when the item is type='video' and has an uploaded file.
    """
    item = session.get(ContentItem, item_id)
    if not item or not item.file_path:
        raise HTTPException(status_code=404, detail="Video not found")

    path = item.file_path
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video file missing")

    file_size = os.path.getsize(path)
    range_header = request.headers.get("range") or request.headers.get("Range")
    media_type = item.mime_type or "video/mp4"

    if not range_header:
        return FileResponse(path=path, media_type=media_type, filename=item.file_name or Path(path).name)

    # Example: "bytes=0-1023"
    try:
        unit, rng = range_header.strip().split("=", 1)
        if unit != "bytes":
            raise ValueError
        start_s, end_s = rng.split("-", 1)
        start = int(start_s) if start_s else 0
        end = int(end_s) if end_s else file_size - 1
    except Exception as e:
        raise HTTPException(status_code=416, detail="Invalid Range header") from e

    start = max(0, start)
    end = min(file_size - 1, end)
    if start > end:
        raise HTTPException(status_code=416, detail="Invalid range")

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
    }
    return StreamingResponse(
        _iter_file_range(path, start, end),
        status_code=206,
        headers=headers,
        media_type=media_type,
    )

