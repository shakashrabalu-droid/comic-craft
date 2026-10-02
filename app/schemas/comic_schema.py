"""
ComicCraft - Pydantic Schemas for AI Structured Outputs
Defines strict schemas passed to Gemini structured generation or JSON schema validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CharacterSchema(BaseModel):
    """Structured character definition returned by the AI outline stage."""
    name: str = Field(..., description="Character's name")
    role: str = Field(..., description="Role in story: Protagonist, Antagonist, Ally, Mentor")
    appearance: str = Field(..., description="Specific physical appearance (facial features, build, skin tone)")
    hair: str = Field(..., description="Hair color, texture, style")
    clothing: str = Field(..., description="Signature outfit, distinct clothing colors and accessories")
    personality: str = Field(..., description="Core temperament and mannerisms")
    distinctive_features: str = Field(..., description="Eye color, scars, insignia, cape, emblems, or signature props")


class DialogueLineSchema(BaseModel):
    """Structured dialogue line for comic balloon."""
    speaker: str = Field(..., description="Name of the character speaking")
    text: str = Field(..., description="Concise dialogue line (1-2 sentences maximum, punchy for comic balloon)")
    style: str = Field(default="speech", description="Bubble style: speech, shout, whisper, thought")


class PanelOutlineSchema(BaseModel):
    """Outline representation of an individual comic panel."""
    panel_number: int = Field(..., ge=1, le=10, description="Sequential panel number")
    scene: str = Field(..., description="Dramatic moment or action taking place")
    narration: Optional[str] = Field(default=None, description="Optional caption box narrative text")
    dialogue: List[DialogueLineSchema] = Field(default_factory=list, description="Dialogue exchanges in this panel")
    visual_description: str = Field(..., description="Key visual framing, environment, character actions and lighting")


class ComicOutlineSchema(BaseModel):
    """Structured output schema for the comic outline generation stage."""
    title: str = Field(..., description="Catchy, professional comic title")
    genre: str = Field(..., description="Comic genre")
    theme: str = Field(..., description="Core underlying theme or moral of the issue")
    characters: List[CharacterSchema] = Field(..., description="List of character profiles maintaining continuity")
    setting: str = Field(..., description="Primary location and environment rules")
    tone: str = Field(..., description="Overall emotional and artistic tone")
    panels: List[PanelOutlineSchema] = Field(..., description="Sequential panels outlining the comic arc")


class DetailedPanelSchema(BaseModel):
    """Detailed story, refined dialogue, and visual prompt for a single panel."""
    panel_number: int = Field(..., ge=1, le=10)
    scene: str = Field(..., description="Refined dramatic action")
    narration: Optional[str] = Field(default=None, description="Polished caption narration")
    dialogue: List[DialogueLineSchema] = Field(default_factory=list)
    emotional_context: str = Field(..., description="Atmosphere and characters' emotional states")
    visual_prompt: str = Field(
        ...,
        description="Focused illustration prompt: Art style, camera angle/composition, lighting, environment, exact character appearance consistent with profiles, zero typography or bubbles."
    )


class ComicDetailedStorySchema(BaseModel):
    """Polished story generation output."""
    title: str = Field(...)
    panels: List[DetailedPanelSchema] = Field(...)
