from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.routes import auth, notebooks, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(notebooks.router)

