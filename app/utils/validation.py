"""
ComicCraft - Input Validation Utility
Validates user inputs, limits, genres, art styles, and panel counts.
"""

from typing import Optional
from app.config import settings


SUPPORTED_GENRES = (
    "Superhero",
    "Sci-Fi",
    "Fantasy",
    "Noir / Detective",
    "Comedy",
    "Cyberpunk",
    "Manga / Shonen",
    "Horror / Mystery",
    "Slice of Life",
    "Adventure",
)

SUPPORTED_TONES = (
    "Epic / Action-Packed",
    "Humorous",
    "Dark & Gritty",
    "Dramatic",
    "Whimsical",
    "Mysterious",
    "Heartwarming",
)

SUPPORTED_ART_STYLES = (
    "Classic Comic Book (90s Marvel/DC)",
    "Japanese Manga (Clean Ink)",
    "Noir Graphic Novel (High Contrast Shadows)",
    "Vibrant Modern Webtoon",
    "Retro Vintage Pop Art",
    "Dark Fantasy & Gothic Ink",
    "Watercolor Comic Illustration",
)


class ValidationError(ValueError):
    """Custom validation error for user-facing validation failures."""
    pass


def validate_story_input(
    story_idea: str,
    panel_count: int,
    genre: Optional[str] = None,
    art_style: Optional[str] = None,
    tone: Optional[str] = None,
    main_character: Optional[str] = None,
) -> dict:
    """
    Validates all inputs for comic creation.
    Raises ValidationError if any parameter is invalid.
    Returns cleaned inputs.
    """
    # 1. Story Idea
    if not story_idea or not story_idea.strip():
        raise ValidationError("Story idea cannot be empty. Please enter your comic premise.")

    cleaned_story = story_idea.strip()
    if len(cleaned_story) < settings.MIN_STORY_IDEA_LENGTH:
        raise ValidationError(
            f"Story idea is too short. Please provide at least {settings.MIN_STORY_IDEA_LENGTH} characters."
        )

    if len(cleaned_story) > settings.MAX_STORY_IDEA_LENGTH:
        raise ValidationError(
            f"Story idea is too long ({len(cleaned_story)} chars). Maximum allowed is {settings.MAX_STORY_IDEA_LENGTH} characters."
        )

    # 2. Panel Count
    if panel_count not in settings.ALLOWED_PANEL_COUNTS:
        raise ValidationError(
            f"Invalid panel count '{panel_count}'. Supported panel counts are: {list(settings.ALLOWED_PANEL_COUNTS)}."
        )

    # 3. Main Character
    cleaned_character = main_character.strip() if main_character else None
    if cleaned_character and len(cleaned_character) > settings.MAX_CHARACTER_NAME_LENGTH:
        raise ValidationError(
            f"Character name exceeds maximum length of {settings.MAX_CHARACTER_NAME_LENGTH} characters."
        )

    # 4. Optional Fields Defaulting
    cleaned_genre = genre.strip() if genre and genre.strip() else "Superhero"
    cleaned_art_style = art_style.strip() if art_style and art_style.strip() else "Classic Comic Book (90s Marvel/DC)"
    cleaned_tone = tone.strip() if tone and tone.strip() else "Epic / Action-Packed"

    return {
        "story_idea": cleaned_story,
        "panel_count": panel_count,
        "genre": cleaned_genre,
        "art_style": cleaned_art_style,
        "tone": cleaned_tone,
        "main_character": cleaned_character,
    }
