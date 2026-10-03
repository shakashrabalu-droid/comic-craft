"""
ComicCraft - Image Generation Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=4000,
    )

    negative_prompt: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    width: int = Field(
        default=1024,
        ge=256,
        le=2048,
    )

    height: int = Field(
        default=1024,
        ge=256,
        le=2048,
    )

    steps: int = Field(
        default=28,
        ge=1,
        le=100,
    )

    guidance_scale: float = Field(
        default=3.5,
        ge=0.0,
        le=20.0,
    )

    seed: Optional[int] = Field(
        default=None,
        ge=0,
    )


class ComicPanelRequest(BaseModel):

    scene: str = Field(
        ...,
        min_length=3,
        max_length=3000,
    )

    character: Optional[str] = None

    location: Optional[str] = None

    action: Optional[str] = None

    mood: Optional[str] = None

    camera: Optional[str] = None

    style: Optional[str] = None

    width: int = Field(
        default=1024,
        ge=256,
        le=2048,
    )

    height: int = Field(
        default=1024,
        ge=256,
        le=2048,
    )

    steps: int = Field(
        default=28,
        ge=1,
        le=100,
    )

    guidance_scale: float = Field(
        default=3.5,
        ge=0.0,
        le=20.0,
    )

    seed: Optional[int] = Field(
        default=None,
        ge=0,
    )
