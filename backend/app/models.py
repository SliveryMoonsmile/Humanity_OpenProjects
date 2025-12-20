from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel, UniqueConstraint


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    display_name: str = Field(default="", nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("email"),)


class Notebook(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    owner_id: str = Field(index=True, nullable=False, foreign_key="user.id")

    title: str = Field(nullable=False)
    description: str = Field(default="", nullable=False)

    # If true, any authenticated user can read.
    is_public: bool = Field(default=False, nullable=False)

    # Filesystem path where the `.ipynb` content is stored.
    content_path: Optional[str] = Field(default=None, nullable=True)

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class NotebookShare(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    notebook_id: str = Field(index=True, nullable=False, foreign_key="notebook.id")
    shared_with_user_id: str = Field(index=True, nullable=False, foreign_key="user.id")
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("notebook_id", "shared_with_user_id"),)

class Category(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    slug: str = Field(index=True, nullable=False)
    name: str = Field(nullable=False)
    description: str = Field(default="", nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("slug"),)


class ContentItem(SQLModel, table=True):
    """
    A general-purpose content record for the single-PC platform:

    - type='page'   -> markdown stored in `body_markdown`
    - type='video'  -> file stored at `file_path`
    - type='file'   -> any uploaded file stored at `file_path`
    - type='script' -> source stored in `script_source`
    """

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    category_id: str = Field(index=True, nullable=False, foreign_key="category.id")

    slug: str = Field(index=True, nullable=False)
    title: str = Field(nullable=False)
    type: str = Field(default="page", nullable=False)  # page|video|file|script

    summary: str = Field(default="", nullable=False)

    body_markdown: str = Field(default="", nullable=False)

    # Generic file backing (videos, downloads, etc.)
    file_path: Optional[str] = Field(default=None, nullable=True)
    file_name: Optional[str] = Field(default=None, nullable=True)
    mime_type: Optional[str] = Field(default=None, nullable=True)
    file_size_bytes: Optional[int] = Field(default=None, nullable=True)

    # Script backing
    script_source: str = Field(default="", nullable=False)
    script_runtime: str = Field(default="python3", nullable=False)  # python3|bash

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("category_id", "slug"),)


class ScriptRun(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    content_item_id: str = Field(index=True, nullable=False, foreign_key="contentitem.id")
    started_at: datetime = Field(default_factory=utcnow, nullable=False)
    finished_at: Optional[datetime] = Field(default=None, nullable=True)

    status: str = Field(default="running", nullable=False)  # running|finished|failed
    exit_code: Optional[int] = Field(default=None, nullable=True)

    args_json: str = Field(default="[]", nullable=False)

    stdout_path: Optional[str] = Field(default=None, nullable=True)
    stderr_path: Optional[str] = Field(default=None, nullable=True)


# ---- API schemas (non-table) ----


class UserCreate(SQLModel):
    email: str
    password: str
    display_name: str = ""


class UserPublic(SQLModel):
    id: str
    email: str
    display_name: str
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class NotebookCreate(SQLModel):
    title: str
    description: str = ""
    is_public: bool = False


class NotebookUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class NotebookPublic(SQLModel):
    id: str
    owner_id: str
    title: str
    description: str
    is_public: bool
    has_content: bool
    created_at: datetime
    updated_at: datetime


class ShareRequest(SQLModel):
    user_email: str


class CategoryCreate(SQLModel):
    slug: str
    name: str
    description: str = ""


class CategoryPublic(SQLModel):
    id: str
    slug: str
    name: str
    description: str
    created_at: datetime


class ContentItemCreate(SQLModel):
    category_slug: str
    slug: str
    title: str
    type: str = "page"  # page|video|file|script
    summary: str = ""
    body_markdown: str = ""
    script_source: str = ""
    script_runtime: str = "python3"


class ContentItemPublic(SQLModel):
    id: str
    category_id: str
    slug: str
    title: str
    type: str
    summary: str
    body_markdown: str
    has_file: bool
    file_name: Optional[str]
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    script_runtime: str
    created_at: datetime
    updated_at: datetime


class ScriptRunRequest(SQLModel):
    args: list[str] = []
    detach: bool = False
    timeout_seconds: int = 30


class ScriptRunPublic(SQLModel):
    id: str
    content_item_id: str
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    exit_code: Optional[int]

