"""
ComicCraft - Comic Generation Pipeline Orchestrator
Coordinates Gemini story generation, image synthesis, layout formatting, and PDF export.
"""

import asyncio
from typing import Dict, List, Optional
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
from app.schemas.comic_schema import ComicDetailedStorySchema, ComicOutlineSchema
from app.services.gemini_service import gemini_service
from app.services.image_service import image_service
from app.services.layout_service import layout_service
from app.services.pdf_service import pdf_service
from app.utils.logger import logger
from app.utils.validation import validate_story_input


class ComicService:
    """In-memory comic registry and lifecycle state machine orchestrator."""

    def __init__(self):
        # In-memory storage for active session comics
        self._comics: Dict[str, Comic] = {}
        # Concurrency semaphore for image generation
        self._image_semaphore = asyncio.Semaphore(2)

    def get_comic(self, comic_id: str) -> Optional[Comic]:
        """Retrieves a comic by its unique identifier."""
        return self._comics.get(comic_id)

    def register_comic(self, comic: Comic) -> None:
        """Stores a comic in registry."""
        self._comics[comic.comic_id] = comic

    def initiate_comic(self, req: CreateComicRequest) -> Comic:
        """
        Validates input and creates the initial Comic record in QUEUED state.
        """
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
            title=f"The Legend of {cleaned['main_character'] or 'ComicCraft'}",
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
        logger.info(f"Initialized new comic [{comic_id[:8]}] - Panels: {comic.panel_count}")
        return comic

    async def execute_pipeline(self, comic_id: str, story_idea: str) -> None:
        """
        Executes the end-to-end multi-stage generation pipeline asynchronously.
        """
        comic = self.get_comic(comic_id)
        if not comic:
            logger.error(f"Cannot execute pipeline: Comic {comic_id} not found.")
            return

        try:
            # ================= STAGE 2: OUTLINE =================
            comic.status = GenerationState.OUTLINE_GENERATING
            comic.stage_description = "Building the comic outline..."
            logger.info(f"Comic [{comic_id[:8]}] -> Stage: OUTLINE_GENERATING")

            outline: ComicOutlineSchema = await gemini_service.generate_outline(
                story_idea=story_idea,
                panel_count=comic.panel_count,
                genre=comic.genre,
                tone=comic.tone,
                art_style=comic.art_style,
                main_character=comic.characters[0].name if comic.characters else None,
                setting=comic.setting,
                target_audience=comic.target_audience,
            )

            # Update comic title and character continuity profiles
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

            # ================= STAGE 3: STORY & DIALOGUE =================
            comic.status = GenerationState.STORY_GENERATING
            comic.stage_description = "Writing dialogue and refining scenes..."
            logger.info(f"Comic [{comic_id[:8]}] -> Stage: STORY_GENERATING")

            detailed_story: ComicDetailedStorySchema = await gemini_service.generate_story_and_dialogue(
                outline=outline,
                art_style=comic.art_style,
                tone=comic.tone,
            )

            # Initialize panels with story details
            panels_map: Dict[int, ComicPanel] = {}
            for dp in detailed_story.panels:
                dialogue_items = []
                for d in dp.dialogue:
                    try:
                        d_style = DialogueStyle(d.style.lower())
                    except ValueError:
                        d_style = DialogueStyle.SPEECH
                    dialogue_items.append(
                        DialogueItem(speaker=d.speaker, text=d.text, style=d_style)
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

            comic.panels = [panels_map[num] for num in sorted(panels_map.keys())]

            # ================= STAGE 4 & 5: IMAGE GENERATION =================
            comic.status = GenerationState.IMAGES_GENERATING
            comic.stage_description = "Generating illustrations for your comic..."
            logger.info(f"Comic [{comic_id[:8]}] -> Stage: IMAGES_GENERATING")

            # Concurrently generate panel images with rate-limiting semaphore
            async def generate_single_panel(p: ComicPanel):
                async with self._image_semaphore:
                    try:
                        filename, url = await image_service.generate_panel_image(
                            comic_id=comic_id,
                            panel_number=p.panel_number,
                            visual_prompt=p.visual_prompt,
                            art_style=comic.art_style,
                            scene_description=p.scene,
                            character_profiles=comic.characters,
                        )
                        p.image_filename = filename
                        p.image_url = url
                        p.status = PanelState.READY
                    except Exception as e:
                        logger.error(f"Image generation failed for panel {p.panel_number}: {e}")
                        p.status = PanelState.FAILED

            await asyncio.gather(*(generate_single_panel(p) for p in comic.panels))

            # ================= STAGE 6: LAYOUT BUILDING =================
            comic.status = GenerationState.LAYOUT_BUILDING
            comic.stage_description = "Assembling comic layout..."
            logger.info(f"Comic [{comic_id[:8]}] -> Stage: LAYOUT_BUILDING")
            # Layout metadata calculated on the fly by layout_service
            await asyncio.sleep(0.3)

            # ================= STAGE 7: PDF GENERATION =================
            comic.status = GenerationState.PDF_GENERATING
            comic.stage_description = "Rendering publication PDF..."
            logger.info(f"Comic [{comic_id[:8]}] -> Stage: PDF_GENERATING")

            try:
                pdf_path, pdf_url = pdf_service.generate_pdf(comic)
                comic.pdf_filename = pdf_path.name
                comic.pdf_url = pdf_url
            except Exception as e:
                logger.warning(f"PDF creation warning: {e}. Comic web preview remains accessible.")

            # ================= COMPLETED =================
            comic.status = GenerationState.COMPLETED
            comic.stage_description = "Your comic is ready!"
            logger.info(f"Comic [{comic_id[:8]}] successfully completed generation!")

        except Exception as e:
            comic.status = GenerationState.FAILED
            comic.stage_description = "Comic generation encountered an issue."
            comic.error_message = f"Comic generation could not be completed. {str(e)}"
            logger.exception(f"Pipeline failure for Comic [{comic_id}]: {e}")

    async def regenerate_single_panel(
        self, comic_id: str, panel_number: int, custom_prompt_hint: Optional[str] = None
    ) -> Optional[ComicPanel]:
        """Regenerates the illustration for a specific panel."""
        comic = self.get_comic(comic_id)
        if not comic:
            return None

        target_panel = next((p for p in comic.panels if p.panel_number == panel_number), None)
        if not target_panel:
            return None

        prompt = target_panel.visual_prompt
        if custom_prompt_hint:
            prompt = f"{prompt}. {custom_prompt_hint}"

        target_panel.status = PanelState.GENERATING
        try:
            filename, url = await image_service.generate_panel_image(
                comic_id=comic_id,
                panel_number=panel_number,
                visual_prompt=prompt,
                art_style=comic.art_style,
                scene_description=target_panel.scene,
                character_profiles=comic.characters,
            )
            target_panel.image_filename = filename
            target_panel.image_url = url
            target_panel.status = PanelState.READY

            # Re-generate PDF with updated panel
            try:
                pdf_path, pdf_url = pdf_service.generate_pdf(comic)
                comic.pdf_filename = pdf_path.name
                comic.pdf_url = pdf_url
            except Exception as e:
                logger.warning(f"Re-generating PDF failed: {e}")

            return target_panel
        except Exception as e:
            target_panel.status = PanelState.FAILED
            logger.error(f"Failed to regenerate panel {panel_number}: {e}")
            return target_panel


comic_service = ComicService()
