"""
Tests for ComicCraft Validation Utilities and Pydantic Schemas.
"""

import pytest
from pydantic import ValidationError as PydanticValidationError
from app.schemas.comic_schema import (
    CharacterSchema,
    ComicOutlineSchema,
    DialogueLineSchema,
    PanelOutlineSchema,
)
from app.utils.validation import ValidationError, validate_story_input


def test_validate_story_input_success():
    """Validates standard input cleanly returns normalized dictionary."""
    result = validate_story_input(
        story_idea="A young cyber hacker unlocks an alien archive hidden on the dark web.",
        panel_count=4,
        genre="Cyberpunk",
        art_style="Vibrant Modern Webtoon",
        tone="Mysterious",
        main_character="Cipher",
    )
    assert result["story_idea"].startswith("A young cyber hacker")
    assert result["panel_count"] == 4
    assert result["genre"] == "Cyberpunk"
    assert result["main_character"] == "Cipher"


def test_case_4_empty_story_prompt():
    """CASE 4: Empty story prompt must raise ValidationError."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_story_input(story_idea="", panel_count=4)

    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_story_input(story_idea="   ", panel_count=4)


def test_case_5_very_long_story_prompt():
    """CASE 5: Very long story prompt (> 2000 chars) must raise ValidationError."""
    too_long = "Comic concept: " + ("superhero flying through space and fighting villains " * 50)
    assert len(too_long) > 2000

    with pytest.raises(ValidationError, match="too long"):
        validate_story_input(story_idea=too_long, panel_count=4)


def test_case_6_invalid_panel_count():
    """CASE 6: Invalid panel count must raise ValidationError."""
    for invalid_count in [0, -1, 5, 7, 100]:
        with pytest.raises(ValidationError, match="Invalid panel count"):
            validate_story_input(
                story_idea="A space bounty hunter takes on one final mission.",
                panel_count=invalid_count,
            )


def test_character_name_too_long():
    """Character names exceeding limit must be rejected."""
    long_name = "A" * 85
    with pytest.raises(ValidationError, match="Character name exceeds maximum"):
        validate_story_input(
            story_idea="A journey through enchanted lands.",
            panel_count=2,
            main_character=long_name,
        )


def test_comic_outline_schema_validation():
    """Verifies strict validation of ComicOutlineSchema."""
    outline_data = {
        "title": "Neon Vanguard",
        "genre": "Cyberpunk",
        "theme": "Sacrifice and freedom",
        "setting": "Neo-Chicago",
        "tone": "Gritty",
        "characters": [
            {
                "name": "Kora",
                "role": "Protagonist",
                "appearance": "Bionic left eye, leather jacket",
                "hair": "Neon purple mohawk",
                "clothing": "Weathered trench coat",
                "personality": "Rebellious",
                "distinctive_features": "Glowing neural cord",
            }
        ],
        "panels": [
            {
                "panel_number": 1,
                "scene": "Kora infiltrates the data vault.",
                "narration": "The security was top notch. So was she.",
                "dialogue": [
                    {"speaker": "Kora", "text": "I am in.", "style": "speech"}
                ],
                "visual_description": "Low angle wide shot of vault interior with green laser tripwires.",
            }
        ],
    }

    schema = ComicOutlineSchema.model_validate(outline_data)
    assert schema.title == "Neon Vanguard"
    assert len(schema.characters) == 1
    assert schema.panels[0].dialogue[0].text == "I am in."
