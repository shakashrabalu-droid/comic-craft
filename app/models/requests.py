"""
ComicCraft - API Request and Response DTOs
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.comic import Comic, GenerationState


class CreateComicRequest(BaseModel):
    """Payload for starting a new comic generation."""
    story_idea: str = Field(..., min_length=5, max_length=2000, description="Core comic story premise")
    genre: Optional[str] = Field(default="Superhero", description="Comic genre")
    main_character: Optional[str] = Field(default=None, max_length=80, description="Protagonist name / summary")
    supporting_characters: Optional[str] = Field(default=None, max_length=200, description="Supporting cast or villains")
    setting: Optional[str] = Field(default=None, max_length=150, description="Primary location or universe")
    tone: Optional[str] = Field(default="Epic / Action-Packed", description="Tone and emotional mood")
    art_style: Optional[str] = Field(default="Classic Comic Book (90s Marvel/DC)", description="Illustration art style")
    panel_count: int = Field(default=4, ge=1, le=6, description="Number of panels in the comic")
    target_audience: Optional[str] = Field(default="All Ages", max_length=50)


class RegeneratePanelRequest(BaseModel):
    """Payload for regenerating a specific panel."""
    panel_number: int = Field(..., ge=1, le=6)
    custom_prompt_hint: Optional[str] = Field(default=None, max_length=300)
    regenerate_image_only: bool = Field(default=True)


class ComicStatusResponse(BaseModel):
    """Polling response payload representing comic progress."""
    comic_id: str
    status: GenerationState
    stage_description: str
    progress_percent: int = Field(default=0, ge=0, le=100)
    error_message: Optional[str] = None
    comic: Optional[Comic] = None
