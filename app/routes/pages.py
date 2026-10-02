"""
ComicCraft - Frontend Page Routes
Serves Jinja2 templates for landing, generation progress, and export completion.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.comic_service import comic_service
from app.utils.validation import SUPPORTED_ART_STYLES, SUPPORTED_GENRES, SUPPORTED_TONES

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Renders the creative comic studio landing page with generator controls."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "genres": SUPPORTED_GENRES,
            "tones": SUPPORTED_TONES,
            "art_styles": SUPPORTED_ART_STYLES,
            "allowed_panels": settings.ALLOWED_PANEL_COUNTS,
        },
    )


@router.get("/generating/{comic_id}", response_class=HTMLResponse)
async def generating_page(request: Request, comic_id: str):
    """Renders the real-time stage progress screen while the AI builds the comic."""
    comic = comic_service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic session not found.")

    return templates.TemplateResponse(
        request=request,
        name="generating.html",
        context={
            "comic_id": comic_id,
            "comic": comic,
        },
    )


@router.get("/export-success/{comic_id}", response_class=HTMLResponse)
async def export_success_page(request: Request, comic_id: str):
    """Renders the comic completion and PDF download showcase."""
    comic = comic_service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic session not found.")

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "comic_id": comic_id,
            "comic": comic,
        },
    )
