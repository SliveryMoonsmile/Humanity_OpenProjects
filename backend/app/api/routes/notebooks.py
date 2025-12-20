from __future__ import annotations

from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import col, select

from backend.app.api.deps import CurrentUser, SessionDep
from backend.app.models import Notebook, NotebookCreate, NotebookPublic, NotebookShare, NotebookUpdate, ShareRequest, User
from backend.app.storage.notebooks import is_path_under_storage_root, notebook_content_path, safe_unlink

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_public(n: Notebook) -> NotebookPublic:
    return NotebookPublic(
        id=n.id,
        owner_id=n.owner_id,
        title=n.title,
        description=n.description,
        is_public=n.is_public,
        has_content=bool(n.content_path),
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


def _can_read(*, session: SessionDep, user: User, notebook: Notebook) -> bool:
    if notebook.owner_id == user.id:
        return True
    if notebook.is_public:
        return True
    share = session.exec(
        select(NotebookShare).where(
            NotebookShare.notebook_id == notebook.id,
            NotebookShare.shared_with_user_id == user.id,
        )
    ).one_or_none()
    return share is not None


@router.get("", response_model=list[NotebookPublic])
def list_notebooks(
    session: SessionDep,
    user: CurrentUser,
    scope: str = Query(default="accessible", pattern="^(accessible|mine|shared|public)$"),
) -> list[NotebookPublic]:
    if scope == "mine":
        rows = session.exec(select(Notebook).where(Notebook.owner_id == user.id).order_by(col(Notebook.created_at).desc()))
        return [_to_public(n) for n in rows]

    if scope == "public":
        rows = session.exec(select(Notebook).where(Notebook.is_public == True).order_by(col(Notebook.created_at).desc()))  # noqa: E712
        return [_to_public(n) for n in rows]

    if scope == "shared":
        shared_ids = session.exec(
            select(NotebookShare.notebook_id).where(NotebookShare.shared_with_user_id == user.id)
        ).all()
        if not shared_ids:
            return []
        rows = session.exec(select(Notebook).where(Notebook.id.in_(shared_ids)).order_by(col(Notebook.created_at).desc()))
        return [_to_public(n) for n in rows]

    # accessible: mine OR shared OR public
    shared_ids = session.exec(select(NotebookShare.notebook_id).where(NotebookShare.shared_with_user_id == user.id)).all()
    query = select(Notebook).where(
        (Notebook.owner_id == user.id) | (Notebook.is_public == True) | (Notebook.id.in_(shared_ids))  # noqa: E712
    )
    rows = session.exec(query.order_by(col(Notebook.created_at).desc()))
    return [_to_public(n) for n in rows]


@router.post("", response_model=NotebookPublic, status_code=status.HTTP_201_CREATED)
def create_notebook(session: SessionDep, user: CurrentUser, payload: NotebookCreate) -> NotebookPublic:
    nb = Notebook(
        owner_id=user.id,
        title=payload.title,
        description=payload.description,
        is_public=payload.is_public,
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    session.add(nb)
    session.commit()
    session.refresh(nb)
    return _to_public(nb)


@router.get("/{notebook_id}", response_model=NotebookPublic)
def get_notebook(session: SessionDep, user: CurrentUser, notebook_id: str) -> NotebookPublic:
    nb = session.get(Notebook, notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if not _can_read(session=session, user=user, notebook=nb):
        raise HTTPException(status_code=403, detail="Not allowed")
    return _to_public(nb)


@router.patch("/{notebook_id}", response_model=NotebookPublic)
def update_notebook(session: SessionDep, user: CurrentUser, notebook_id: str, payload: NotebookUpdate) -> NotebookPublic:
    nb = session.get(Notebook, notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if nb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can update")

    if payload.title is not None:
        nb.title = payload.title
    if payload.description is not None:
        nb.description = payload.description
    if payload.is_public is not None:
        nb.is_public = payload.is_public
    nb.updated_at = _utcnow()

    session.add(nb)
    session.commit()
    session.refresh(nb)
    return _to_public(nb)


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notebook(session: SessionDep, user: CurrentUser, notebook_id: str) -> Response:
    nb = session.get(Notebook, notebook_id)
    if not nb:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if nb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can delete")

    # delete shares
    shares = session.exec(select(NotebookShare).where(NotebookShare.notebook_id == nb.id)).all()
    for s in shares:
        session.delete(s)
    # delete content
    safe_unlink(nb.content_path)
    session.delete(nb)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{notebook_id}/content", response_model=NotebookPublic)
async def upload_notebook_content(
    session: SessionDep,
    user: CurrentUser,
    notebook_id: str,
    file: UploadFile = File(...),
) -> NotebookPublic:
    nb = session.get(Notebook, notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if nb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can upload content")

    if file.filename and not file.filename.lower().endswith(".ipynb"):
        raise HTTPException(status_code=400, detail="Only .ipynb files are accepted")

    dest = notebook_content_path(owner_id=user.id, notebook_id=nb.id)
    async with aiofiles.open(dest, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            await f.write(chunk)

    nb.content_path = dest
    nb.updated_at = _utcnow()
    session.add(nb)
    session.commit()
    session.refresh(nb)
    return _to_public(nb)


@router.get("/{notebook_id}/content")
def download_notebook_content(session: SessionDep, user: CurrentUser, notebook_id: str) -> FileResponse:
    nb = session.get(Notebook, notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if not _can_read(session=session, user=user, notebook=nb):
        raise HTTPException(status_code=403, detail="Not allowed")
    if not nb.content_path:
        raise HTTPException(status_code=404, detail="Notebook content not uploaded")
    if not is_path_under_storage_root(nb.content_path):
        raise HTTPException(status_code=500, detail="Notebook content path is invalid")
    return FileResponse(path=nb.content_path, media_type="application/json", filename=f"{nb.id}.ipynb")


@router.post("/{notebook_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def share_notebook(session: SessionDep, user: CurrentUser, notebook_id: str, payload: ShareRequest) -> Response:
    nb = session.get(Notebook, notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if nb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can share")

    target_email = payload.user_email.strip().lower()
    target = session.exec(select(User).where(User.email == target_email)).one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")

    # idempotent-ish: unique constraint will prevent duplicates
    existing = session.exec(
        select(NotebookShare).where(
            NotebookShare.notebook_id == nb.id,
            NotebookShare.shared_with_user_id == target.id,
        )
    ).one_or_none()
    if existing:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    session.add(NotebookShare(notebook_id=nb.id, shared_with_user_id=target.id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

