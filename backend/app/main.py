from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import settings, validate_settings
from backend.app.db import init_db
from backend.app.storage.notebooks import ensure_storage_root


def _parse_cors(origins: str) -> list[str]:
    if origins.strip() == "*":
        return ["*"]
    return [o.strip() for o in origins.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_settings()
    ensure_storage_root()
    init_db()
    yield


app = FastAPI(
    title="Physics Data Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

origins = _parse_cors(settings.CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    # If the app imports successfully and DB init ran at startup,
    # this is typically sufficient for local/docker deployments.
    return {"status": "ready"}


app.include_router(api_router, prefix=settings.API_PREFIX)

