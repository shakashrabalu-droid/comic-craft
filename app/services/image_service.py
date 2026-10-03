import asyncio
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.services.flux_service import flux_service

logger = logging.getLogger(__name__)


class ImageService:
    """
    ComicCraft image generation service.

    Primary provider:
        Hugging Face

    Fallback:
        Local placeholder image

    Gemini is NOT used for image generation.
    """

    def __init__(self):
        self.backend = settings.IMAGE_GENERATION_BACKEND

    # ============================================================
    # PROVIDER IMAGE GENERATION
    # ============================================================

    def generate(
        self,
        prompt: str,
        filename: str,
    ) -> Path:
        """
        Generate an image using the configured image provider.
        """

        if self.backend in ("auto", "huggingface"):
            return flux_service.generate(
                prompt=prompt,
                filename=filename,
            )

        if self.backend == "fallback":
            raise RuntimeError(
                "Fallback backend selected."
            )

        if self.backend == "gemini":
            raise RuntimeError(
                "Gemini image generation is not used by ComicCraft."
            )

        raise RuntimeError(
            f"Unsupported image generation backend: {self.backend}"
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
        """
        Create a local placeholder image when the provider fails.

        This keeps the comic pipeline operational even when the
        external image provider is unavailable.
        """

        unique_id = uuid4().hex[:8]

        filename = (
            f"{comic_id}_panel_{panel_number}_"
            f"{unique_id}.png"
        )

        output_path = settings.IMAGES_DIR / filename
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

        draw = ImageDraw.Draw(image)

        # --------------------------------------------------------
        # Fonts
        # --------------------------------------------------------

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
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # --------------------------------------------------------
        # Outer border
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Header
        # --------------------------------------------------------

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
            f"COMICCRAFT • PANEL {panel_number}"
        )

        draw.text(
            (60, 65),
            title,
            fill="#FFFFFF",
            font=font_large,
        )

        # --------------------------------------------------------
        # Visual area
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Simple placeholder composition
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Prompt information
        # --------------------------------------------------------

        prompt_text = visual_prompt[:240]

        draw.text(
            (75, height - 145),
            prompt_text,
            fill="#FFFFFF",
            font=font_small,
        )

        draw.text(
            (75, height - 95),
            f"Style: {art_style[:100]}",
            fill="#BBBBBB",
            font=font_small,
        )

        # --------------------------------------------------------
        # Save
        # --------------------------------------------------------

        image.save(
            output_path,
            format="PNG",
        )

        image.save(
            static_path,
            format="PNG",
        )

        url = (
            f"/static/generated/{filename}"
        )

        logger.info(
            "Created local fallback image: %s",
            output_path,
        )

        return filename, url

    # ============================================================
    # PANEL GENERATION
    # ============================================================

    async def generate_panel_image(
        self,
        comic_id: str,
        panel_number: int,
        visual_prompt: str,
        art_style: str,
        scene_description: Optional[str] = None,
        character_profiles=None,
    ):
        """
        Generate a comic panel.

        Primary path:
            Comic prompt
                ↓
            Hugging Face
                ↓
            PNG

        Failure path:
            Local placeholder
        """

        # --------------------------------------------------------
        # Unique filename for this panel
        # --------------------------------------------------------

        provider_filename = (
            f"{comic_id}_panel_{panel_number}_"
            f"{uuid4().hex[:8]}.png"
        )

        # --------------------------------------------------------
        # Character continuity
        # --------------------------------------------------------

        character_context = ""

        if character_profiles:
            character_lines = []

            for character in character_profiles:
                try:
                    if hasattr(character, "to_prompt"):
                        character_lines.append(
                            character.to_prompt()
                        )
                    elif hasattr(character, "model_dump"):
                        data = character.model_dump()

                        name = data.get(
                            "name",
                            "Character",
                        )

                        appearance = data.get(
                            "appearance",
                            "",
                        )

                        clothing = data.get(
                            "clothing",
                            "",
                        )

                        hair = data.get(
                            "hair",
                            "",
                        )

                        character_lines.append(
                            f"{name}: "
                            f"{appearance}; "
                            f"{hair}; "
                            f"{clothing}"
                        )
                    else:
                        character_lines.append(
                            str(character)
                        )

                except Exception:
                    character_lines.append(
                        str(character)
                    )

            if character_lines:
                character_context = (
                    "\n\nCHARACTER CONTINUITY:\n"
                    + "\n".join(character_lines)
                )

        # --------------------------------------------------------
        # Final image prompt
        # --------------------------------------------------------

        prompt = f"""
Create a single high-quality comic book panel illustration.

ART STYLE:
{art_style}

VISUAL DESCRIPTION:
{visual_prompt}

SCENE:
{scene_description or visual_prompt}
{character_context}

COMPOSITION REQUIREMENTS:
- cinematic comic-book composition
- strong subject separation
- readable silhouettes
- expressive character poses
- detailed environment
- dynamic camera angle
- dramatic lighting
- professional illustrated artwork
- consistent character appearance
- coherent visual storytelling
- polished finished artwork

IMPORTANT:
- no speech bubbles
- no captions
- no UI elements
- no borders
- no watermark
- no logos
- no written text inside the artwork
"""

        # --------------------------------------------------------
        # Try Hugging Face
        # --------------------------------------------------------

        try:
            result = await asyncio.to_thread(
                self.generate,
                prompt,
                provider_filename,
            )

            if not result:
                raise RuntimeError(
                    "Image provider returned no output."
                )

            result_path = Path(result)

            if not result_path.exists():
                raise RuntimeError(
                    "Image provider returned a missing file: "
                    f"{result_path}"
                )

            filename = result_path.name

            static_path = (
                settings.STATIC_DIR
                / "generated"
                / filename
            )

            static_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            # Copy generated image to static directory.
            if (
                result_path.resolve()
                != static_path.resolve()
            ):
                static_path.write_bytes(
                    result_path.read_bytes()
                )

            url = (
                f"/static/generated/{filename}"
            )

            logger.info(
                "REAL AI panel generated | "
                "comic=%s | panel=%s | file=%s",
                comic_id,
                panel_number,
                filename,
            )

            return filename, url

        # --------------------------------------------------------
        # Provider failure → local fallback
        # --------------------------------------------------------

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


# ============================================================
# SERVICE INSTANCE
# ============================================================

image_service = ImageService()
