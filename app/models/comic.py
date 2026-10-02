"""
ComicCraft - Domain Data Models
Defines Comic, ComicPanel, CharacterProfile, and GenerationState.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class GenerationState(str, Enum):
    """Explicit state machine for the comic generation pipeline."""
    QUEUED = "QUEUED"
    OUTLINE_GENERATING = "OUTLINE_GENERATING"
    STORY_GENERATING = "STORY_GENERATING"
    IMAGES_GENERATING = "IMAGES_GENERATING"
    LAYOUT_BUILDING = "LAYOUT_BUILDING"
    PDF_GENERATING = "PDF_GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PanelState(str, Enum):
    """State of an individual panel."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"


class DialogueStyle(str, Enum):
    """Visual style for comic dialogue balloons."""
    SPEECH = "speech"
    SHOUT = "shout"
    WHISPER = "whisper"
    THOUGHT = "thought"


class CharacterProfile(BaseModel):
    """Reusable character specification for cross-panel narrative and visual continuity."""
    name: str = Field(..., description="Character name")
    role: str = Field(default="Protagonist", description="Role (e.g. Hero, Sidekick, Antagonist)")
    appearance: str = Field(default="", description="Key facial and physical appearance")
    hair: str = Field(default="", description="Hair color, length, and style")
    clothing: str = Field(default="", description="Signature comic outfit and accessories")
    personality: str = Field(default="", description="Personality keywords")
    distinctive_features: str = Field(default="", description="Scars, glasses, aura, or special markers")

    def to_continuity_prompt(self) -> str:
        """Serializes character attributes into a concise prompt chunk for image generation."""
        parts = [f"{self.name} ({self.role})"]
        if self.appearance:
            parts.append(f"Appearance: {self.appearance}")
        if self.hair:
            parts.append(f"Hair: {self.hair}")
        if self.clothing:
            parts.append(f"Clothing: {self.clothing}")
        if self.distinctive_features:
            parts.append(f"Distinctive: {self.distinctive_features}")
        return " | ".join(parts)


class DialogueItem(BaseModel):
    """Speech or thought dialogue item inside a panel."""
    speaker: str = Field(..., description="Character speaking")
    text: str = Field(..., description="Dialogue text (concise for balloon)")
    style: DialogueStyle = Field(default=DialogueStyle.SPEECH, description="Balloon style")


class ComicPanel(BaseModel):
    """A single panel within a comic story."""
    panel_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    panel_number: int = Field(..., ge=1, le=10)
    scene: str = Field(..., description="Scene description")
    narration: Optional[str] = Field(default=None, description="Caption box narration at top/bottom")
    dialogue: List[DialogueItem] = Field(default_factory=list, description="Dialogue speech bubbles")
    emotional_context: Optional[str] = Field(default=None, description="Tone/emotion of the scene")
    visual_prompt: str = Field(..., description="Detailed, focused prompt for illustration")
    image_filename: Optional[str] = Field(default=None, description="Safe filename of the panel image")
    image_url: Optional[str] = Field(default=None, description="Web accessible URL to the image")
    status: PanelState = Field(default=PanelState.PENDING)


class Comic(BaseModel):
    """The master Comic aggregate root."""
    comic_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = Field(..., description="Title of the comic")
    genre: str = Field(default="Superhero")
    theme: Optional[str] = Field(default=None)
    characters: List[CharacterProfile] = Field(default_factory=list)
    setting: Optional[str] = Field(default=None)
    tone: str = Field(default="Epic / Action-Packed")
    art_style: str = Field(default="Classic Comic Book (90s Marvel/DC)")
    target_audience: Optional[str] = Field(default="General")
    panel_count: int = Field(default=4, ge=1, le=6)
    panels: List[ComicPanel] = Field(default_factory=list)
    pdf_filename: Optional[str] = Field(default=None)
    pdf_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: GenerationState = Field(default=GenerationState.QUEUED)
    stage_description: str = Field(default="Queued for generation...")
    error_message: Optional[str] = Field(default=None)
