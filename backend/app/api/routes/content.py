from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlmodel import col, select

from backend.app.api.deps import SessionDep
from backend.app.models import Category, CategoryCreate, CategoryPublic, ContentItem, ContentItemCreate, ContentItemPublic

router = APIRouter(prefix="/content", tags=["content"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _cat_public(c: Category) -> CategoryPublic:
    return CategoryPublic.model_validate(c)


def _item_public(i: ContentItem) -> ContentItemPublic:
    return ContentItemPublic(
        id=i.id,
        category_id=i.category_id,
        slug=i.slug,
        title=i.title,
        type=i.type,
        summary=i.summary,
        body_markdown=i.body_markdown,
        has_file=bool(i.file_path),
        file_name=i.file_name,
        mime_type=i.mime_type,
        file_size_bytes=i.file_size_bytes,
        script_runtime=i.script_runtime,
        created_at=i.created_at,
        updated_at=i.updated_at,
    )


@router.get("/categories", response_model=list[CategoryPublic])
def list_categories(session: SessionDep) -> list[CategoryPublic]:
    rows = session.exec(select(Category).order_by(col(Category.created_at).desc())).all()
    return [_cat_public(c) for c in rows]


@router.post("/categories", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(session: SessionDep, payload: CategoryCreate) -> CategoryPublic:
    slug = payload.slug.strip().lower()
    existing = session.exec(select(Category).where(Category.slug == slug)).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Category slug already exists")

    c = Category(slug=slug, name=payload.name.strip(), description=payload.description or "")
    session.add(c)
    session.commit()
    session.refresh(c)
    return _cat_public(c)


@router.get("/categories/{category_slug}/items", response_model=list[ContentItemPublic])
def list_items(session: SessionDep, category_slug: str) -> list[ContentItemPublic]:
    cat = session.exec(select(Category).where(Category.slug == category_slug.strip().lower())).one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    rows = session.exec(
        select(ContentItem).where(ContentItem.category_id == cat.id).order_by(col(ContentItem.created_at).desc())
    ).all()
    return [_item_public(i) for i in rows]


@router.post("/items", response_model=ContentItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(session: SessionDep, payload: ContentItemCreate) -> ContentItemPublic:
    cat = session.exec(select(Category).where(Category.slug == payload.category_slug.strip().lower())).one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    slug = payload.slug.strip().lower()
    existing = session.exec(
        select(ContentItem).where(ContentItem.category_id == cat.id, ContentItem.slug == slug)
    ).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Item slug already exists in category")

    item_type = (payload.type or "page").strip().lower()
    if item_type not in {"page", "video", "file", "script"}:
        raise HTTPException(status_code=400, detail="Invalid item type")

    i = ContentItem(
        category_id=cat.id,
        slug=slug,
        title=payload.title.strip(),
        type=item_type,
        summary=payload.summary or "",
        body_markdown=payload.body_markdown or "",
        script_source=payload.script_source or "",
        script_runtime=(payload.script_runtime or "python3").strip(),
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    session.add(i)
    session.commit()
    session.refresh(i)
    return _item_public(i)


@router.get("/items/{item_id}", response_model=ContentItemPublic)
def get_item(session: SessionDep, item_id: str) -> ContentItemPublic:
    i = session.get(ContentItem, item_id)
    if not i:
        raise HTTPException(status_code=404, detail="Item not found")
    return _item_public(i)

