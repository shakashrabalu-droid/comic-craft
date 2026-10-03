"""
ComicCraft - Image Generation Routes
"""

from fastapi import APIRouter, HTTPException

from app.prompts.image_prompts import (
    DEFAULT_NEGATIVE_PROMPT,
    build_comic_prompt,
)

from app.schemas.image import (
    ImageGenerationRequest,
    ComicPanelRequest,
)

from app.services.image_service import image_service


router = APIRouter(
    prefix="/api/images",
    tags=["Image Generation"],
)


@router.post("/generate")
async def generate_image(
    request: ImageGenerationRequest,
):
    """
    Generate an image directly from a prompt.
    """

    try:

        result = image_service.generate(
            prompt=request.prompt,
            negative_prompt=(
                request.negative_prompt
                or DEFAULT_NEGATIVE_PROMPT
            ),
            width=request.width,
            height=request.height,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/generate-panel")
async def generate_panel(
    request: ComicPanelRequest,
):
    """
    Generate a comic panel from structured scene data.
    """

    try:

        prompt = build_comic_prompt(
            scene=request.scene,
            character=request.character,
            location=request.location,
            action=request.action,
            mood=request.mood,
            camera=request.camera,
            style=request.style,
        )


        result = image_service.generate(
            prompt=prompt,
            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
            width=request.width,
            height=request.height,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
        )


        return {
            **result,
            "prompt": prompt,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
