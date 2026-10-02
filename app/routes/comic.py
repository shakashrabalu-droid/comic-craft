"""
ComicCraft - Comic Generation and Preview Routes
Handles initiation, stage polling, interactive previews, and panel regeneration.
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models.comic import GenerationState
from app.models.requests import ComicStatusResponse, CreateComicRequest, RegeneratePanelRequest
from app.services.comic_service import comic_service
from app.services.layout_service import layout_service
from app.utils.logger import logger
from app.utils.validation import ValidationError

router = APIRouter(tags=["Comic"])
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.post("/generate")
async def generate_comic_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    story_idea: Optional[str] = Form(None),
    genre: Optional[str] = Form("Superhero"),
    main_character: Optional[str] = Form(None),
    supporting_characters: Optional[str] = Form(None),
    setting: Optional[str] = Form(None),
    tone: Optional[str] = Form("Epic / Action-Packed"),
    art_style: Optional[str] = Form("Classic Comic Book (90s Marvel/DC)"),
    panel_count: Optional[int] = Form(4),
    target_audience: Optional[str] = Form("All Ages"),
):
    """
    Initiates comic generation pipeline from HTML Form or JSON.
    """
    is_json = request.headers.get("content-type", "").startswith("application/json")

    if is_json:
        try:
            body = await request.json()
            req = CreateComicRequest(**body)
        except Exception as e:
            logger.warning(f"Invalid JSON request body: {e}")
            raise HTTPException(status_code=422, detail=f"Invalid request payload: {e}")
    else:
        if not story_idea:
            raise HTTPException(status_code=422, detail="Story idea is required.")
        req = CreateComicRequest(
            story_idea=story_idea,
            genre=genre,
            main_character=main_character,
            supporting_characters=supporting_characters,
            setting=setting,
            tone=tone,
            art_style=art_style,
            panel_count=panel_count or 4,
            target_audience=target_audience,
        )

    try:
        comic = comic_service.initiate_comic(req)
    except ValidationError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    # Launch generation pipeline in background
    background_tasks.add_task(comic_service.execute_pipeline, comic.comic_id, req.story_idea)

    redirect_target = f"/generating/{comic.comic_id}"

    if is_json:
        return JSONResponse(
            {
                "success": True,
                "comic_id": comic.comic_id,
                "status": comic.status.value,
                "redirect_url": redirect_target,
            }
        )

    return RedirectResponse(url=redirect_target, status_code=303)


@router.get("/comic/{comic_id}", response_class=HTMLResponse)
async def view_comic_preview(request: Request, comic_id: str):
    """Renders the high-fidelity comic preview screen."""
    comic = comic_service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found.")

    if comic.status not in (GenerationState.COMPLETED, GenerationState.FAILED):
        # Redirect to the generating progress page if still working
        return RedirectResponse(url=f"/generating/{comic_id}", status_code=307)

    view_model = layout_service.prepare_comic_view_model(comic)
    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context={
            "comic": view_model,
            "raw_comic": comic,
        },
    )


@router.get("/comic/{comic_id}/status", response_model=ComicStatusResponse)
async def check_comic_status(comic_id: str):
    """Polling endpoint for frontend progress bar and step transitions."""
    comic = comic_service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic session not found.")

    # Calculate realistic stage percentage
    stage_weights = {
        GenerationState.QUEUED: 5,
        GenerationState.OUTLINE_GENERATING: 25,
        GenerationState.STORY_GENERATING: 45,
        GenerationState.IMAGES_GENERATING: 75,
        GenerationState.LAYOUT_BUILDING: 90,
        GenerationState.PDF_GENERATING: 95,
        GenerationState.COMPLETED: 100,
        GenerationState.FAILED: 100,
    }
    progress = stage_weights.get(comic.status, 10)

    return ComicStatusResponse(
        comic_id=comic.comic_id,
        status=comic.status,
        stage_description=comic.stage_description,
        progress_percent=progress,
        error_message=comic.error_message,
        comic=comic,
    )


@router.post("/comic/{comic_id}/regenerate-panel")
async def regenerate_panel_endpoint(comic_id: str, payload: RegeneratePanelRequest):
    """Regenerates a single panel illustration with optional artist guidance."""
    comic = comic_service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found.")

    panel = await comic_service.regenerate_single_panel(
        comic_id=comic_id,
        panel_number=payload.panel_number,
        custom_prompt_hint=payload.custom_prompt_hint,
    )
    if not panel:
        raise HTTPException(status_code=400, detail="Failed to locate or regenerate specified panel.")

    return {
        "success": True,
        "panel_number": panel.panel_number,
        "image_url": panel.image_url,
        "status": panel.status.value,
        "pdf_url": comic.pdf_url,
    }
