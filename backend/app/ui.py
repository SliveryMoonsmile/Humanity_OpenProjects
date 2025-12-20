from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
from sqlmodel import col, select

from backend.app.api.deps import SessionDep
from backend.app.models import Category, ContentItem

templates = Jinja2Templates(directory="backend/templates")

router = APIRouter(prefix="/ui", tags=["ui"], include_in_schema=False)


@router.get("", response_class=HTMLResponse)
def ui_index(request: Request, session: SessionDep):
    cats = session.exec(select(Category).order_by(col(Category.created_at).desc())).all()
    return templates.TemplateResponse("index.html", {"request": request, "categories": cats})


@router.get("/c/{category_slug}", response_class=HTMLResponse)
def ui_category(request: Request, session: SessionDep, category_slug: str):
    cat = session.exec(select(Category).where(Category.slug == category_slug)).one_or_none()
    if not cat:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    items = session.exec(
        select(ContentItem).where(ContentItem.category_id == cat.id).order_by(col(ContentItem.created_at).desc())
    ).all()
    return templates.TemplateResponse("category.html", {"request": request, "category": cat, "items": items})


@router.get("/i/{item_id}", response_class=HTMLResponse)
def ui_item(request: Request, session: SessionDep, item_id: str):
    item = session.get(ContentItem, item_id)
    if not item:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    html = ""
    if item.type == "page":
        html = markdown(item.body_markdown or "", extensions=["fenced_code", "tables"])

    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "item": item,
            "page_html": html,
        },
    )

