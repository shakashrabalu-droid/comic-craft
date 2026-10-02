"""
ComicCraft - Image Generation Service
Generates panel illustrations using Hugging Face Stable Diffusion, Gemini Image API, or Stylized Comic Canvas Fallback.
"""

import asyncio
import io
import math
import random
import time
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.prompts.image_prompt import format_panel_image_prompt, get_negative_prompt
from app.models.comic import CharacterProfile
from app.utils.file_manager import file_manager
from app.utils.logger import logger


class ImageServiceError(Exception):
    """Raised for image generation failures."""
    pass


class ImageService:
    """Orchestrates image generation across multiple backends with resilient fallbacks."""

    def __init__(self):
        self.hf_token = settings.HUGGINGFACE_API_KEY
        self.sd_model = settings.STABLE_DIFFUSION_MODEL
        self.backend_mode = settings.IMAGE_GENERATION_BACKEND
        self._hf_client = None

        if self.hf_token:
            try:
                from huggingface_hub import InferenceClient
                self._hf_client = InferenceClient(token=self.hf_token)
                logger.info("Initialized Hugging Face InferenceClient.")
            except Exception as e:
                logger.warning(f"Failed to initialize Hugging Face client: {e}")

    async def generate_panel_image(
        self,
        comic_id: str,
        panel_number: int,
        visual_prompt: str,
        art_style: str,
        scene_description: str,
        character_profiles: Optional[List[CharacterProfile]] = None,
    ) -> tuple[str, str]:
        """
        Generates an illustration for a single panel.
        Returns tuple of (safe_filename, relative_web_url).
        """
        full_prompt = format_panel_image_prompt(
            base_visual_prompt=visual_prompt,
            art_style=art_style,
            character_profiles=character_profiles,
            scene_number=panel_number,
        )
        negative_prompt = get_negative_prompt(art_style)
        filename = file_manager.generate_image_filename(comic_id, panel_number)
        output_path = file_manager.get_image_path(filename)
        static_output_path = settings.STATIC_DIR / "generated" / filename

        logger.info(f"Generating illustration for Comic [{comic_id[:8]}] Panel #{panel_number} (Style: {art_style})")

        # 1. Attempt Hugging Face Stable Diffusion if configured
        if self._hf_client and self.backend_mode in ("auto", "huggingface"):
            try:
                img_data = await self._generate_with_hf(full_prompt, negative_prompt)
                if img_data:
                    self._save_and_mirror_image(img_data, output_path, static_output_path)
                    logger.info(f"Panel #{panel_number} generated via Hugging Face Stable Diffusion.")
                    return filename, f"/static/generated/{filename}"
            except Exception as e:
                logger.warning(f"HF Stable Diffusion generation failed for panel {panel_number}: {e}. Falling back.")

        # 2. Attempt Gemini Image API if configured
        if settings.GEMINI_API_KEY and self.backend_mode in ("auto", "gemini"):
            try:
                img_data = await self._generate_with_gemini(full_prompt)
                if img_data:
                    self._save_and_mirror_image(img_data, output_path, static_output_path)
                    logger.info(f"Panel #{panel_number} generated via Gemini Image API.")
                    return filename, f"/static/generated/{filename}"
            except Exception as e:
                logger.warning(f"Gemini Image generation failed for panel {panel_number}: {e}. Falling back.")

        # 3. Resilient Stylized Comic Canvas Fallback
        logger.info(f"Rendering high-fidelity stylized comic canvas for Panel #{panel_number}.")
        fallback_img = self._create_stylized_comic_canvas(
            panel_number=panel_number,
            art_style=art_style,
            scene_description=scene_description,
            visual_prompt=visual_prompt,
        )
        self._save_and_mirror_image(fallback_img, output_path, static_output_path)
        return filename, f"/static/generated/{filename}"

    async def _generate_with_hf(self, prompt: str, negative_prompt: str) -> Optional[Image.Image]:
        """Calls Hugging Face InferenceClient text_to_image in thread pool."""
        loop = asyncio.get_running_loop()

        def _call_hf():
            return self._hf_client.text_to_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                model=self.sd_model,
                width=768,
                height=768,
            )

        try:
            return await asyncio.wait_for(loop.run_in_executor(None, _call_hf), timeout=35.0)
        except Exception as e:
            logger.warning(f"HF text_to_image error: {e}")
            return None

    async def _generate_with_gemini(self, prompt: str) -> Optional[Image.Image]:
        """Attempts Gemini Image generation if available."""
        loop = asyncio.get_running_loop()

        def _call_gemini():
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Using Imagen 3 or Gemini image endpoint
            result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    output_mime_type="image/png",
                )
            )
            if result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                return Image.open(io.BytesIO(img_bytes))
            return None

        try:
            return await asyncio.wait_for(loop.run_in_executor(None, _call_gemini), timeout=30.0)
        except Exception as e:
            logger.debug(f"Gemini generate_images call skipped or failed: {e}")
            return None

    def _create_stylized_comic_canvas(
        self,
        panel_number: int,
        art_style: str,
        scene_description: str,
        visual_prompt: str,
        width: int = 768,
        height: int = 768,
    ) -> Image.Image:
        """
        Generates a visually rich, professional comic art placeholder canvas.
        Includes atmospheric gradients, halftone comic patterns, dramatic horizon,
        silhouettes, and stylized panel badges.
        """
        img = Image.new("RGB", (width, height), color=(15, 20, 30))
        draw = ImageDraw.Draw(img)

        # Style palette definitions
        palettes = {
            "Classic Comic Book (90s Marvel/DC)": [(230, 50, 40), (245, 180, 20), (30, 60, 140)],
            "Japanese Manga (Clean Ink)": [(30, 30, 35), (140, 145, 155), (240, 240, 245)],
            "Noir Graphic Novel (High Contrast Shadows)": [(10, 10, 15), (70, 75, 85), (200, 30, 30)],
            "Vibrant Modern Webtoon": [(120, 40, 220), (250, 80, 160), (40, 200, 240)],
            "Retro Vintage Pop Art": [(220, 40, 60), (255, 220, 50), (40, 140, 220)],
            "Dark Fantasy & Gothic Ink": [(20, 15, 30), (90, 50, 80), (180, 120, 70)],
            "Watercolor Comic Illustration": [(60, 120, 180), (140, 200, 190), (240, 220, 180)],
        }
        colors = palettes.get(art_style, [(40, 60, 120), (180, 70, 140), (240, 180, 60)])

        # 1. Atmospheric Vertical Gradient
        c1, c2, c3 = colors[0], colors[1], colors[2]
        for y in range(height):
            ratio = y / height
            if ratio < 0.5:
                r_sub = ratio * 2
                r = int(c1[0] * (1 - r_sub) + c2[0] * r_sub)
                g = int(c1[1] * (1 - r_sub) + c2[1] * r_sub)
                b = int(c1[2] * (1 - r_sub) + c2[2] * r_sub)
            else:
                r_sub = (ratio - 0.5) * 2
                r = int(c2[0] * (1 - r_sub) + c3[0] * r_sub)
                g = int(c2[1] * (1 - r_sub) + c3[1] * r_sub)
                b = int(c2[2] * (1 - r_sub) + c3[2] * r_sub)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # 2. Comic Halftone / Speed Line Rays
        center_x, center_y = width // 2, int(height * 0.45)
        num_rays = 28
        for i in range(num_rays):
            angle = (2 * math.pi / num_rays) * i
            ray_len = width * 0.9
            end_x = center_x + ray_len * math.cos(angle)
            end_y = center_y + ray_len * math.sin(angle)
            draw.line(
                [(center_x, center_y), (end_x, end_y)],
                fill=(255, 255, 255, 35),
                width=2 if i % 2 == 0 else 1,
            )

        # 3. Dynamic Comic Silhouettes / Horizon Buildings or Mountains
        silhouette_color = (12, 14, 20)
        # Jagged skyline/terrain
        points = [(0, height), (0, int(height * 0.65))]
        for x in range(0, width + 50, 45):
            h_var = int(math.sin(x * 0.05 + panel_number) * 40 + math.cos(x * 0.02) * 30)
            points.append((x, int(height * 0.68) + h_var))
        points.append((width, height))
        draw.polygon(points, fill=silhouette_color)

        # Dramatic hero silhouette standing on cliff/ledge
        hero_x = int(width * 0.48)
        hero_y = int(height * 0.62)
        # Cape / body
        draw.polygon(
            [
                (hero_x - 20, hero_y + 60),
                (hero_x + 20, hero_y + 60),
                (hero_x + 10, hero_y + 10),
                (hero_x - 10, hero_y + 10),
            ],
            fill=(5, 5, 8),
        )
        # Head / hood
        draw.ellipse([(hero_x - 12, hero_y - 10), (hero_x + 12, hero_y + 14)], fill=(5, 5, 8))
        # Flowing cape edge
        draw.polygon(
            [(hero_x - 10, hero_y + 15), (hero_x - 55, hero_y + 55), (hero_x - 8, hero_y + 40)],
            fill=(8, 8, 12),
        )

        # 4. Bold Comic Border
        border_width = 8
        draw.rectangle(
            [(border_width // 2, border_width // 2), (width - border_width // 2, height - border_width // 2)],
            outline=(10, 10, 15),
            width=border_width,
        )

        # 5. Panel Number Badge (top-left classic comic corner box)
        badge_box = [(16, 16), (160, 60)]
        draw.rectangle(badge_box, fill=(245, 190, 20), outline=(10, 10, 15), width=3)
        draw.text((26, 26), f"PANEL {panel_number}", fill=(10, 10, 15))

        # 6. Stylized Art Style Tag (bottom-right)
        style_short = art_style.split("(")[0].strip()[:24]
        tag_box = [(width - 240, height - 50), (width - 18, height - 18)]
        draw.rectangle(tag_box, fill=(15, 18, 25), outline=(245, 190, 20), width=2)
        draw.text((width - 228, height - 42), style_short, fill=(240, 240, 245))

        return img

    def _save_and_mirror_image(self, img: Image.Image, primary_path: Path, static_path: Path) -> None:
        """Saves image to primary storage and mirrors it to the static folder for immediate HTTP serving."""
        primary_path.parent.mkdir(parents=True, exist_ok=True)
        static_path.parent.mkdir(parents=True, exist_ok=True)

        img.save(primary_path, format="PNG", optimize=True)
        img.save(static_path, format="PNG", optimize=True)

        # Validate that image is non-empty and readable
        if not primary_path.exists() or primary_path.stat().st_size == 0:
            raise ImageServiceError(f"Generated image failed validation: {primary_path}")


image_service = ImageService()
