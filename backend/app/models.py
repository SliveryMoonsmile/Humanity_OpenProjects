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

