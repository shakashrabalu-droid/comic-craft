"""
ComicCraft - Image Generation Service

Handles:
- Flux/HuggingFace image generation
- Character continuity prompts
- Local fallback image generation
- Static image URLs
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.services.flux_service import flux_service

logger = logging.getLogger(__name__)


class ImageService:

    def __init__(self):
        self.backend = settings.IMAGE_GENERATION_BACKEND

    # ============================================================
    # CHARACTER CONTINUITY
    # ============================================================

    @staticmethod
    def _character_continuity(
        character_profiles: Optional[list[Any]],
    ) -> str:

        if not character_profiles:
            return ""

        parts = []

        for character in character_profiles:

            try:
                if hasattr(
                    character,
                    "to_continuity_prompt",
                ):
                    parts.append(
                        character.to_continuity_prompt()
                    )
                    continue

                name = getattr(
                    character,
                    "name",
                    "",
                )

                role = getattr(
                    character,
                    "role",
                    "",
                )

                appearance = getattr(
                    character,
                    "appearance",
                    "",
                )

                hair = getattr(
                    character,
                    "hair",
                    "",
                )

                clothing = getattr(
                    character,
                    "clothing",
                    "",
                )

                parts.append(
                    (
                        f"{name} ({role}); "
                        f"Appearance: {appearance}; "
                        f"Hair: {hair}; "
                        f"Clothing: {clothing}"
                    )
                )

            except Exception:
                continue

        if not parts:
            return ""

        return (
            "\nCHARACTER CONTINUITY:\n"
            + "\n".join(
                f"- {item}"
                for item in parts
            )
        )

    # ============================================================
    # PROVIDER
    # ============================================================

    def generate(
        self,
        prompt: str,
    ) -> Path:

        if self.backend in (
            "auto",
            "huggingface",
        ):

            # IMPORTANT:
            # flux_service.generate() accepts the prompt.
            # Do NOT pass filename= here.
            result = flux_service.generate(
                prompt=prompt,
            )

            return Path(result)

        if self.backend == "fallback":
            raise RuntimeError(
                "Fallback backend selected."
            )

        if self.backend == "gemini":
            raise RuntimeError(
                "Gemini image backend is not "
                "implemented in ImageService."
            )

        raise RuntimeError(
            f"Unsupported image generation backend: "
            f"{self.backend}"
        )

    # ============================================================
    # LOCAL FALLBACK
    # ============================================================

    def _create_fallback_image(
        self,
        comic_id: str,
        panel_number: int,
        visual_prompt: str,
        art_style: str,
    ):

        unique_id = uuid4().hex[:8]

        filename = (
            f"{comic_id}_panel_{panel_number}_"
            f"{unique_id}.png"
        )

        output_path = (
            settings.IMAGES_DIR
            / filename
        )

        static_path = (
            settings.STATIC_DIR
            / "generated"
            / filename
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        static_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        width = 768
        height = 768

        image = Image.new(
            "RGB",
            (width, height),
            "#111111",
        )

        draw = ImageDraw.Draw(
            image
        )

        # Border
        draw.rectangle(
            (
                20,
                20,
                width - 20,
                height - 20,
            ),
            outline="#FFFFFF",
            width=4,
        )

        # Header
        draw.rectangle(
            (
                40,
                40,
                width - 40,
                120,
            ),
            outline="#FFFFFF",
            width=2,
        )

        title = (
            f"COMICCRAFT • PANEL "
            f"{panel_number}"
        )

        try:

            font_large = ImageFont.truetype(
                "arial.ttf",
                28,
            )

            font_small = ImageFont.truetype(
                "arial.ttf",
                20,
            )

        except Exception:

            font_large = (
                ImageFont.load_default()
            )

            font_small = (
                ImageFont.load_default()
            )

        draw.text(
            (60, 65),
            title,
            fill="#FFFFFF",
            font=font_large,
        )

        # Main visual area
        visual_box = (
            60,
            160,
            width - 60,
            height - 170,
        )

        draw.rectangle(
            visual_box,
            outline="#AAAAAA",
            width=2,
        )

        # Simple cinematic placeholder
        center_x = width // 2
        center_y = 450

        draw.ellipse(
            (
                center_x - 90,
                center_y - 90,
                center_x + 90,
                center_y + 90,
            ),
            outline="#FFFFFF",
            width=4,
        )

        draw.line(
            (
                center_x - 180,
                center_y + 170,
                center_x,
                center_y + 20,
            ),
            fill="#FFFFFF",
            width=4,
        )

        draw.line(
            (
                center_x + 180,
                center_y + 170,
                center_x,
                center_y + 20,
            ),
            fill="#FFFFFF",
            width=4,
        )

        # Prompt
        prompt_text = (
            visual_prompt[:240]
        )

        draw.text(
            (
                75,
                height - 145,
            ),
            prompt_text,
            fill="#FFFFFF",
            font=font_small,
        )

        draw.text(
            (
                75,
                height - 95,
            ),
            f"Style: {art_style[:100]}",
            fill="#BBBBBB",
            font=font_small,
        )

        image.save(
            output_path
        )

        image.save(
            static_path
        )

        url = (
            f"/static/generated/"
            f"{filename}"
        )

        logger.info(
            "Created local fallback image: %s",
            output_path,
        )

        return (
            filename,
            url,
        )

    # ============================================================
    # PANEL IMAGE
    # ============================================================

    async def generate_panel_image(
        self,
        comic_id: str,
        panel_number: int,
        visual_prompt: str,
        art_style: str,
        scene_description: Optional[str] = None,
        character_profiles: Optional[list[Any]] = None,
        **kwargs: Any,
    ):

        continuity = (
            self._character_continuity(
                character_profiles
            )
        )

        prompt = f"""
Create a high-quality comic panel illustration.

ART STYLE:
{art_style}

VISUAL DESCRIPTION:
{visual_prompt}

SCENE:
{scene_description or visual_prompt}

{continuity}

REQUIREMENTS:
- cinematic comic composition
- strong subject separation
- clear character poses
- detailed environment
- consistent character appearance
- dramatic lighting
- readable silhouettes
- no UI elements
- no watermark
- no speech bubbles
- no written text
"""

        try:

            result = await asyncio.to_thread(
                self.generate,
                prompt,
            )

            if not result:
                raise RuntimeError(
                    "Image provider returned no output."
                )

            result_path = Path(
                result
            )

            if not result_path.exists():
                raise RuntimeError(
                    "Image provider returned "
                    f"missing file: {result_path}"
                )

            # Create our own safe ComicCraft filename.
            filename = (
                f"{comic_id}_panel_"
                f"{panel_number}_"
                f"{uuid4().hex[:8]}.png"
            )

            output_path = (
                settings.IMAGES_DIR
                / filename
            )

            static_path = (
                settings.STATIC_DIR
                / "generated"
                / filename
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            static_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            # Copy provider image into ComicCraft storage.
            output_path.write_bytes(
                result_path.read_bytes()
            )

            static_path.write_bytes(
                result_path.read_bytes()
            )

            url = (
                f"/static/generated/"
                f"{filename}"
            )

            logger.info(
                "Generated panel %s for comic %s",
                panel_number,
                comic_id,
            )

            return (
                filename,
                url,
            )

        except Exception as error:

            logger.warning(
                "Image provider failed for panel %s: %s. "
                "Using local fallback.",
                panel_number,
                error,
            )

            return self._create_fallback_image(
                comic_id=comic_id,
                panel_number=panel_number,
                visual_prompt=visual_prompt,
                art_style=art_style,
            )


image_service = ImageService()
