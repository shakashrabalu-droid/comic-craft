"""
ComicCraft - Comic Generation Pipeline Orchestrator

Coordinates:
- Gemini story generation
- Image generation
- Image fallback
- Layout preparation
- PDF generation
- Panel regeneration
"""

import asyncio
from typing import Dict, Optional
from uuid import uuid4

from app.config import settings
from app.models.comic import (
    CharacterProfile,
    Comic,
    ComicPanel,
    DialogueItem,
    DialogueStyle,
    GenerationState,
    PanelState,
)
from app.models.requests import CreateComicRequest
from app.schemas.comic_schema import (
    ComicDetailedStorySchema,
    ComicOutlineSchema,
)
from app.services.gemini_service import gemini_service
from app.services.image_service import image_service
from app.services.layout_service import layout_service
from app.services.pdf_service import pdf_service
from app.utils.logger import logger
from app.utils.validation import validate_story_input


class ComicService:
    """In-memory comic registry and lifecycle pipeline."""

    def __init__(self):
        self._comics: Dict[str, Comic] = {}

        # IMPORTANT:
        # asyncio synchronization primitives must not be created
        # in one event loop and reused in another.
        self._image_semaphore = None
        self._image_semaphore_loop = None

    def _get_image_semaphore(self):
        """Return a semaphore belonging to the current event loop."""
        loop = asyncio.get_running_loop()

        if (
            self._image_semaphore is None
            or self._image_semaphore_loop is not loop
        ):
            self._image_semaphore = asyncio.Semaphore(2)
            self._image_semaphore_loop = loop

        return self._image_semaphore

    def _save_to_disk(self, comic: Comic) -> None:
        """Persist comic state to disk."""
        try:
            settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

            path = settings.TEMP_DIR / f"{comic.comic_id}.json"

            path.write_text(
                comic.model_dump_json(indent=2),
                encoding="utf-8",
            )

        except Exception as e:
            logger.warning(
                f"Failed to persist comic {comic.comic_id}: {e}"
            )

    def get_comic(self, comic_id: str) -> Optional[Comic]:
        """Retrieve comic from memory or disk."""

        if comic_id in self._comics:
            return self._comics[comic_id]

        try:
            path = settings.TEMP_DIR / f"{comic_id}.json"

            if path.exists():
                comic = Comic.model_validate_json(
                    path.read_text(encoding="utf-8")
                )

                self._comics[comic_id] = comic

                return comic

        except Exception as e:
            logger.warning(
                f"Failed to load comic {comic_id}: {e}"
            )

        return None

    def register_comic(self, comic: Comic) -> None:
        """Register and persist comic."""
        self._comics[comic.comic_id] = comic
        self._save_to_disk(comic)

    def initiate_comic(
        self,
        req: CreateComicRequest,
    ) -> Comic:
        """Create a new comic in QUEUED state."""

        cleaned = validate_story_input(
            story_idea=req.story_idea,
            panel_count=req.panel_count,
            genre=req.genre,
            art_style=req.art_style,
            tone=req.tone,
            main_character=req.main_character,
        )

        comic_id = uuid4().hex

        comic = Comic(
            comic_id=comic_id,
            title=(
                f"The Legend of "
                f"{cleaned['main_character'] or 'ComicCraft'}"
            ),
            genre=cleaned["genre"],
            theme=cleaned["story_idea"][:100],
            setting=req.setting or "Atmospheric Comic Realm",
            tone=cleaned["tone"],
            art_style=cleaned["art_style"],
            target_audience=req.target_audience or "All Ages",
            panel_count=cleaned["panel_count"],
            status=GenerationState.QUEUED,
            stage_description="Preparing your story...",
        )

        self.register_comic(comic)

        logger.info(
            f"Initialized new comic "
            f"[{comic_id[:8]}] - Panels: {comic.panel_count}"
        )

        return comic

    async def execute_pipeline(
        self,
        comic_id: str,
        story_idea: str,
    ) -> None:
        """Execute complete comic generation pipeline."""

        comic = self.get_comic(comic_id)

        if not comic:
            logger.error(
                f"Cannot execute pipeline: Comic {comic_id} not found."
            )
            return

        try:

            # ==================================================
            # OUTLINE
            # ==================================================

            comic.status = GenerationState.OUTLINE_GENERATING
            comic.stage_description = (
                "Building the comic outline..."
            )

            self._save_to_disk(comic)

            logger.info(
                f"Comic [{comic_id[:8]}] -> "
                f"Stage: OUTLINE_GENERATING"
            )

            outline: ComicOutlineSchema = (
                await gemini_service.generate_outline(
                    story_idea=story_idea,
                    panel_count=comic.panel_count,
                    genre=comic.genre,
                    tone=comic.tone,
                    art_style=comic.art_style,
                    main_character=(
                        comic.characters[0].name
                        if comic.characters
                        else None
                    ),
                    setting=comic.setting,
                    target_audience=comic.target_audience,
                )
            )

            comic.title = outline.title

            comic.characters = [
                CharacterProfile(
                    name=c.name,
                    role=c.role,
                    appearance=c.appearance,
                    hair=c.hair,
                    clothing=c.clothing,
                    personality=c.personality,
                    distinctive_features=c.distinctive_features,
                )
                for c in outline.characters
            ]

            # ==================================================
            # STORY
            # ==================================================

            comic.status = GenerationState.STORY_GENERATING
            comic.stage_description = (
                "Writing dialogue and refining scenes..."
            )

            logger.info(
                f"Comic [{comic_id[:8]}] -> "
                f"Stage: STORY_GENERATING"
            )

            detailed_story = (
                await gemini_service.generate_story_and_dialogue(
                    outline=outline,
                    art_style=comic.art_style,
                    tone=comic.tone,
                )
            )

            panels_map: Dict[int, ComicPanel] = {}

            for dp in detailed_story.panels:

                dialogue_items = []

                for d in dp.dialogue:

                    try:
                        d_style = DialogueStyle(
                            d.style.lower()
                        )

                    except ValueError:
                        d_style = DialogueStyle.SPEECH

                    dialogue_items.append(
                        DialogueItem(
                            speaker=d.speaker,
                            text=d.text,
                            style=d_style,
                        )
                    )

                panel = ComicPanel(
                    panel_number=dp.panel_number,
                    scene=dp.scene,
                    narration=dp.narration,
                    dialogue=dialogue_items,
                    emotional_context=dp.emotional_context,
                    visual_prompt=dp.visual_prompt,
                    status=PanelState.GENERATING,
                )

                panels_map[dp.panel_number] = panel

            comic.panels = [
                panels_map[num]
                for num in sorted(panels_map.keys())
            ]

            # ==================================================
            # IMAGE GENERATION
            # ==================================================

            comic.status = GenerationState.IMAGES_GENERATING
            comic.stage_description = (
                "Generating illustrations for your comic..."
            )

            logger.info(
                f"Comic [{comic_id[:8]}] -> "
                f"Stage: IMAGES_GENERATING"
            )

            async def generate_single_panel(
                panel: ComicPanel,
            ):

                semaphore = self._get_image_semaphore()

                async with semaphore:

                    try:

                        filename, url = (
                            await image_service.generate_panel_image(
                                comic_id=comic_id,
                                panel_number=panel.panel_number,
                                visual_prompt=panel.visual_prompt,
                                art_style=comic.art_style,
                                scene_description=panel.scene,
                                character_profiles=comic.characters,
                            )
                        )

                        panel.image_filename = filename
                        panel.image_url = url
                        panel.status = PanelState.READY

                    except Exception as e:

                        logger.error(
                            f"Image generation failed for "
                            f"panel {panel.panel_number}: {e}"
                        )

                        panel.status = PanelState.FAILED

            await asyncio.gather(
                *(
                    generate_single_panel(panel)
                    for panel in comic.panels
                )
            )

            # ==================================================
            # LAYOUT
            # ==================================================

            comic.status = GenerationState.LAYOUT_BUILDING
            comic.stage_description = (
                "Assembling comic layout..."
            )

            logger.info(
                f"Comic [{comic_id[:8]}] -> "
                f"Stage: LAYOUT_BUILDING"
            )

            await asyncio.sleep(0.1)

            # ==================================================
            # PDF
            # ==================================================

            comic.status = GenerationState.PDF_GENERATING
            comic.stage_description = (
                "Rendering publication PDF..."
            )

            logger.info(
                f"Comic [{comic_id[:8]}] -> "
                f"Stage: PDF_GENERATING"
            )

            try:

                pdf_path, pdf_url = (
                    pdf_service.generate_pdf(comic)
                )

                comic.pdf_filename = pdf_path.name
                comic.pdf_url = pdf_url

            except Exception as e:

                logger.warning(
                    f"PDF creation warning: {e}. "
                    f"Comic web preview remains accessible."
                )

            # ==================================================
            # COMPLETE
            # ==================================================

            comic.status = GenerationState.COMPLETED
            comic.stage_description = (
                "Your comic is ready!"
            )
            comic.error_message = None

            self._save_to_disk(comic)

            logger.info(
                f"Comic [{comic_id[:8]}] "
                f"successfully completed generation!"
            )

        except Exception as e:

            comic.status = GenerationState.FAILED

            comic.stage_description = (
                "Comic generation encountered an issue."
            )

            comic.error_message = (
                f"Comic generation could not be completed. {str(e)}"
            )

            self._save_to_disk(comic)

            logger.exception(
                f"Pipeline failure for Comic "
                f"[{comic_id}]: {e}"
            )

    async def regenerate_single_panel(
        self,
        comic_id: str,
        panel_number: int,
        custom_prompt_hint: Optional[str] = None,
    ) -> Optional[ComicPanel]:
        """Regenerate one panel."""

        comic = self.get_comic(comic_id)

        if not comic:
            return None

        target_panel = next(
            (
                p
                for p in comic.panels
                if p.panel_number == panel_number
            ),
            None,
        )

        if not target_panel:
            return None

        prompt = target_panel.visual_prompt

        if custom_prompt_hint:
            prompt = (
                f"{prompt}. "
                f"{custom_prompt_hint}"
            )

        target_panel.status = PanelState.GENERATING

        try:

            filename, url = (
                await image_service.generate_panel_image(
                    comic_id=comic_id,
                    panel_number=panel_number,
                    visual_prompt=prompt,
                    art_style=comic.art_style,
                    scene_description=target_panel.scene,
                    character_profiles=comic.characters,
                )
            )

            target_panel.image_filename = filename
            target_panel.image_url = url
            target_panel.status = PanelState.READY

            try:

                pdf_path, pdf_url = (
                    pdf_service.generate_pdf(comic)
                )

                comic.pdf_filename = pdf_path.name
                comic.pdf_url = pdf_url

            except Exception as e:

                logger.warning(
                    f"Re-generating PDF failed: {e}"
                )

            self._save_to_disk(comic)

            return target_panel

        except Exception as e:

            target_panel.status = PanelState.FAILED

            logger.error(
                f"Failed to regenerate panel "
                f"{panel_number}: {e}"
            )

            return target_panel


comic_service = ComicService()