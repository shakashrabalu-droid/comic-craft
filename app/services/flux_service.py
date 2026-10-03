import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from app.config import settings

load_dotenv()

logger = logging.getLogger(__name__)


class FluxService:
    """
    Hugging Face image generation service.

    Gemini is used for text generation.
    Hugging Face is used for comic panel image generation.
    """

    def __init__(self):
        self.api_key = (
            os.getenv("HF_TOKEN")
            or getattr(settings, "HUGGINGFACE_API_KEY", None)
        )

        self.provider = os.getenv(
            "HF_PROVIDER",
            "hf-inference",
        )

        self.model = os.getenv(
            "FLUX_MODEL",
            "stabilityai/stable-diffusion-3-medium-diffusers",
        )

        self.width = int(
            os.getenv("IMAGE_WIDTH", "1024")
        )

        self.height = int(
            os.getenv("IMAGE_HEIGHT", "1024")
        )

        self.steps = int(
            os.getenv("IMAGE_STEPS", "28")
        )

        self.guidance_scale = float(
            os.getenv("IMAGE_GUIDANCE_SCALE", "7.0")
        )

        self.client: Optional[InferenceClient] = None

        if self.api_key:
            self.client = InferenceClient(
                provider=self.provider,
                api_key=self.api_key,
            )

            logger.info(
                "Hugging Face image client initialized | "
                "provider=%s | model=%s",
                self.provider,
                self.model,
            )
        else:
            logger.warning(
                "Hugging Face token not configured."
            )

    def generate(
        self,
        prompt: str,
        filename: str,
    ) -> Path:
        """
        Generate a real AI image using Hugging Face.
        """

        if self.client is None:
            raise RuntimeError(
                "Hugging Face token is missing. "
                "Set HF_TOKEN in .env."
            )

        output_path = settings.IMAGES_DIR / filename
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Generating AI image | provider=%s | model=%s",
            self.provider,
            self.model,
        )

        image = self.client.text_to_image(
            prompt=prompt,
            model=self.model,
            width=self.width,
            height=self.height,
            num_inference_steps=self.steps,
            guidance_scale=self.guidance_scale,
        )

        if image is None:
            raise RuntimeError(
                "Hugging Face returned no image."
            )

        image.save(
            output_path,
            format="PNG",
        )

        if not output_path.exists():
            raise RuntimeError(
                f"Image was not saved: {output_path}"
            )

        logger.info(
            "REAL AI image generated: %s",
            output_path,
        )

        return output_path


flux_service = FluxService()
