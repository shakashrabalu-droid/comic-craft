"""
ComicCraft - Gemini AI Service
Interfaces with the Google GenAI SDK (gemini-3.8-flash) for structured outline and dialogue generation.
"""

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import ValidationError as PydanticValidationError

from app.config import settings
from app.prompts.outline_prompt import OUTLINE_SYSTEM_INSTRUCTION, build_outline_prompt
from app.prompts.story_prompt import STORY_SYSTEM_INSTRUCTION, build_story_prompt
from app.schemas.comic_schema import ComicDetailedStorySchema, ComicOutlineSchema
from app.utils.logger import logger


class GeminiServiceError(Exception):
    """Raised when Gemini generation, parsing, or validation fails."""
    pass


class GeminiService:
    """Manages Gemini model interactions for structured comic story generation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.outline_model = settings.GEMINI_OUTLINE_MODEL
        self.story_model = settings.GEMINI_STORY_MODEL
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Google GenAI Client successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI Client: {e}")

    @property
    def is_configured(self) -> bool:
        """Checks if Gemini API credentials and client are available."""
        return bool(self.api_key and self._client)

    @staticmethod
    def _clean_json_response(raw_text: str) -> str:
        """Strips markdown code blocks, backticks, and extracts pure JSON payload."""
        text = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        # Find outer matching braces if extra text exists
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        return text

    async def generate_outline(
        self,
        story_idea: str,
        panel_count: int,
        genre: str,
        tone: str,
        art_style: str,
        main_character: Optional[str] = None,
        supporting_characters: Optional[str] = None,
        setting: Optional[str] = None,
        target_audience: Optional[str] = None,
    ) -> ComicOutlineSchema:
        """
        Stage 2: Generates a validated structured comic outline using Gemini.
        Falls back to offline generator if API key is not configured.
        """
        logger.info(f"Initiating Stage 2: Outline generation (Panels: {panel_count}, Genre: {genre}, Model: {self.outline_model})")

        prompt = build_outline_prompt(
            story_idea=story_idea,
            panel_count=panel_count,
            genre=genre,
            tone=tone,
            art_style=art_style,
            main_character=main_character,
            supporting_characters=supporting_characters,
            setting=setting,
            target_audience=target_audience,
        )

        if not self.is_configured:
            logger.warning("Gemini API key not configured or client unavailable. Using simulated offline generator for outline.")
            return self._generate_offline_outline(
                story_idea=story_idea,
                panel_count=panel_count,
                genre=genre,
                tone=tone,
                art_style=art_style,
                main_character=main_character,
                setting=setting,
            )

        # Production Gemini Call with Retries
        last_error = None
        for attempt in range(1, 3):
            try:
                raw_text = ""
                if hasattr(self._client, "models") and hasattr(self._client.models, "generate_content"):
                    from google.genai import types
                    response = self._client.models.generate_content(
                        model=self.outline_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=OUTLINE_SYSTEM_INSTRUCTION,
                            response_mime_type="application/json",
                            response_schema=ComicOutlineSchema,
                            temperature=0.7,
                        ),
                    )
                    raw_text = getattr(response, "text", "") or ""
                elif hasattr(self._client, "interactions"):
                    interaction = self._client.interactions.create(
                        model=self.outline_model,
                        input=f"{OUTLINE_SYSTEM_INSTRUCTION}\n\n{prompt}",
                    )
                    raw_text = getattr(interaction, "output_text", "") or ""

                if isinstance(raw_text, str) and raw_text.strip():
                    cleaned_text = self._clean_json_response(raw_text)
                    outline = ComicOutlineSchema.model_validate_json(cleaned_text)

                    # Ensure exact requested panel count
                    if len(outline.panels) != panel_count:
                        logger.warning(
                            f"Model generated {len(outline.panels)} panels instead of {panel_count}. Adjusting."
                        )
                        outline.panels = outline.panels[:panel_count]

                    logger.info(f"Stage 2 Outline generated successfully: '{outline.title}' with {len(outline.panels)} panels")
                    return outline

            except Exception as e:
                last_error = e
                logger.warning(f"Outline generation attempt {attempt} failed: {e}")

        logger.error(f"Live Gemini outline generation failed: {last_error}")
        raise GeminiServiceError(f"Live Gemini outline generation failed: {last_error}")

    async def generate_story_and_dialogue(
        self,
        outline: ComicOutlineSchema,
        art_style: str,
        tone: str,
    ) -> ComicDetailedStorySchema:
        """
        Stage 3: Expands and refines outline into polished dialogue and focused panel prompts.
        """
        logger.info(f"Initiating Stage 3: Story & Dialogue refinement (Model: {self.story_model})")

        prompt = build_story_prompt(
            outline_data=outline.model_dump(),
            art_style=art_style,
            tone=tone,
        )

        if not self.is_configured:
            logger.warning("Gemini API key not configured. Using simulated offline generator for story expansion.")
            return self._generate_offline_story(outline, art_style)

        last_error = None
        for attempt in range(1, 3):
            try:
                raw_text = ""
                if hasattr(self._client, "models") and hasattr(self._client.models, "generate_content"):
                    from google.genai import types
                    response = self._client.models.generate_content(
                        model=self.story_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=STORY_SYSTEM_INSTRUCTION,
                            response_mime_type="application/json",
                            response_schema=ComicDetailedStorySchema,
                            temperature=0.7,
                        ),
                    )
                    raw_text = getattr(response, "text", "") or ""
                elif hasattr(self._client, "interactions"):
                    interaction = self._client.interactions.create(
                        model=self.story_model,
                        input=f"{STORY_SYSTEM_INSTRUCTION}\n\n{prompt}",
                    )
                    raw_text = getattr(interaction, "output_text", "") or ""

                if isinstance(raw_text, str) and raw_text.strip():
                    cleaned_text = self._clean_json_response(raw_text)
                    story_detail = ComicDetailedStorySchema.model_validate_json(cleaned_text)
                    logger.info(f"Stage 3 Story refined successfully with {len(story_detail.panels)} detailed panels.")
                    return story_detail

            except Exception as e:
                last_error = e
                logger.warning(f"Story refinement attempt {attempt} failed: {e}")

        logger.error(f"Live Gemini story refinement failed: {last_error}")
        raise GeminiServiceError(f"Live Gemini story refinement failed: {last_error}")

    def _generate_offline_outline(
        self,
        story_idea: str,
        panel_count: int,
        genre: str,
        tone: str,
        art_style: str,
        main_character: Optional[str],
        setting: Optional[str],
    ) -> ComicOutlineSchema:
        """Reliable offline outline generator for local testing and zero-credential demonstrations."""
        protagonist_name = main_character or "Alex Drake"
        location = setting or "Neo-Metropolis City Center"

        from app.schemas.comic_schema import CharacterSchema, DialogueLineSchema, PanelOutlineSchema

        characters = [
            CharacterSchema(
                name=protagonist_name,
                role="Protagonist",
                appearance="Athletic build, determined amber eyes, sharp jawline",
                hair="Tousled raven-black hair with electric blue streak",
                clothing="Midnight-blue reinforced tactical jacket with high collar and silver clasps",
                personality="Resolute, quick-witted, fiercely loyal to truth",
                distinctive_features="Luminous silver pulse-gauntlet on the left wrist",
            ),
            CharacterSchema(
                name="Vector",
                role="Ally / Tech Specialist",
                appearance="Slender, inquisitive gaze, wire-rim smart spectacles",
                hair="Short cropped copper hair",
                clothing="Amber aviator vest with multi-pocket utility belt",
                personality="Analytical, enthusiastic, slightly nervous under fire",
                distinctive_features="Holographic data-ring humming with cyan telemetry",
            ),
        ]

        panels = []
        scenes_data = [
            (
                f"The shadow of mystery falls over {location}.",
                f"The city was quiet... too quiet for a Friday night.",
                [DialogueLineSchema(speaker=protagonist_name, text="Telemetry signal verified. We're close.", style="speech")],
                f"Establishing wide shot of {location} under neon rain, {protagonist_name} perched on an art-deco gargoyle.",
            ),
            (
                "An unexpected anomaly triggers alarms.",
                "Suddenly, the chronometer fractured into crystalline light.",
                [
                    DialogueLineSchema(speaker="Vector", text="Spike in the sector grid! Look out!", style="shout"),
                    DialogueLineSchema(speaker=protagonist_name, text="I see it!", style="speech"),
                ],
                f"Dynamic medium two-shot; {protagonist_name} drawing the glowing gauntlet as energy ripples across the street.",
            ),
            (
                "Confronting the turning point.",
                "There was no turning back now.",
                [DialogueLineSchema(speaker=protagonist_name, text="Whatever this is ends right here!", style="shout")],
                f"Low-angle heroic close-up of {protagonist_name} charging forward through shimmering shockwaves.",
            ),
            (
                "The resolution and new dawn.",
                "The dawn broke through the clouds, restoring balance.",
                [
                    DialogueLineSchema(speaker="Vector", text="Core stabilized. You pulled it off, Alex.", style="speech"),
                    DialogueLineSchema(speaker=protagonist_name, text="Just another day on the clock.", style="speech"),
                ],
                f"Cinematic wide angle sunrise over {location}, {protagonist_name} looking towards the horizon with a calm smirk.",
            ),
            (
                "Bonus Panel: The lingering enigma.",
                "Yet deep beneath the ruins, an ember still pulsed.",
                [DialogueLineSchema(speaker=protagonist_name, text="Wait... the signal hasn't stopped.", style="thought")],
                f"Mysterious close-up of a cracked relic glowing faintly in the rubble.",
            ),
            (
                "Bonus Panel: The next chapter awaits.",
                "To be continued in the chronicles of the pulse.",
                [DialogueLineSchema(speaker="Vector", text="Incoming transmission from Sector 9!", style="shout")],
                f"Full page dramatic splash composition of the team preparing for the next mission.",
            ),
        ]

        for i in range(1, panel_count + 1):
            s_idx = min(i - 1, len(scenes_data) - 1)
            scene, narration, dialogue, visual = scenes_data[s_idx]
            panels.append(
                PanelOutlineSchema(
                    panel_number=i,
                    scene=scene,
                    narration=narration,
                    dialogue=dialogue,
                    visual_description=visual,
                )
            )

        title = f"The Chronicles of {protagonist_name}"
        return ComicOutlineSchema(
            title=title,
            genre=genre,
            theme=f"Courage in {location}",
            characters=characters,
            setting=location,
            tone=tone,
            panels=panels,
        )

    def _generate_offline_story(
        self, outline: ComicOutlineSchema, art_style: str
    ) -> ComicDetailedStorySchema:
        """Reliable offline story polisher for local testing."""
        from app.schemas.comic_schema import DetailedPanelSchema

        detailed_panels = []
        for p in outline.panels:
            detailed_panels.append(
                DetailedPanelSchema(
                    panel_number=p.panel_number,
                    scene=p.scene,
                    narration=p.narration,
                    dialogue=p.dialogue,
                    emotional_context="High stakes and cinematic determination",
                    visual_prompt=f"{p.visual_description}. Rendered in {art_style} with dynamic comic book lighting, sharp outlines, and vivid color contrast.",
                )
            )

        return ComicDetailedStorySchema(
            title=outline.title,
            panels=detailed_panels,
        )


gemini_service = GeminiService()
