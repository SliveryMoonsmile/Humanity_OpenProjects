from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.deps import CurrentUser
from backend.app.models import UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)

