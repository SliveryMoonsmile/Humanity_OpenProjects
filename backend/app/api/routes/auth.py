from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from backend.app.api.deps import SessionDep
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models import Token, User, UserCreate, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, session: SessionDep) -> UserPublic:
    existing = session.exec(select(User).where(User.email == payload.email)).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or "",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublic.model_validate(user)


@router.post("/token", response_model=Token)
def token(session: SessionDep, form: OAuth2PasswordRequestForm = Depends()) -> Token:
    # OAuth2PasswordRequestForm uses "username" field; we treat it as email.
    email = form.username.strip().lower()
    user = session.exec(select(User).where(User.email == email)).one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    jwt_token = create_access_token(subject=user.id)
    return Token(access_token=jwt_token)

