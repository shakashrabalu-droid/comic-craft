"""
ComicCraft - FLUX Image Generation Service

Handles communication with Hugging Face Inference Providers
and FLUX.1-dev.

Architecture:

FastAPI
   ↓
ImageService
   ↓
FluxService
   ↓
Hugging Face
   ↓
Fal AI
   ↓
FLUX.1-dev
"""

from pathlib import Path
from typing import Optional
from uuid import uuid4

from huggingface_hub import InferenceClient

from app.config import settings


class FluxService:
    """Service responsible for FLUX.1-dev image generation."""

    def __init__(self) -> None:

        if not settings.HF_TOKEN:
            raise RuntimeError(
                "HF_TOKEN is missing. "
                "Add your Hugging Face token to .env"
            )

        self.client = InferenceClient(
            provider=settings.HF_PROVIDER,
            api_key=settings.HF_TOKEN,
        )

        self.model = settings.FLUX_MODEL


    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """
        Generate an image using FLUX.1-dev.
        """

        width = width or settings.IMAGE_WIDTH

        height = height or settings.IMAGE_HEIGHT

        steps = steps or settings.IMAGE_STEPS

        guidance_scale = (
            guidance_scale
            if guidance_scale is not None
            else settings.IMAGE_GUIDANCE_SCALE
        )


        image = self.client.text_to_image(
            prompt=prompt,
            model=self.model,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            seed=seed,
        )


        # ------------------------------------------
        # Save generated image
        # ------------------------------------------

        filename = (
            f"{uuid4().hex}_flux.png"
        )

        output_path = (
            Path(settings.IMAGES_DIR)
            / filename
        )

        image.save(
            output_path,
            format="PNG",
        )


        return {
            "success": True,
            "filename": filename,
            "path": str(output_path),
            "model": self.model,
            "provider": settings.HF_PROVIDER,
            "width": width,
            "height": height,
            "seed": seed,
        }


# Singleton instance
flux_service = FluxService()
