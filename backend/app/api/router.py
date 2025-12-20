from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.routes import auth, content, media, notebooks, scripts, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(notebooks.router)
api_router.include_router(content.router)
api_router.include_router(media.router)
api_router.include_router(scripts.router)

