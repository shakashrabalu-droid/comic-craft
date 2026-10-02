"""
Tests for ComicCraft AI Prompt Engineering Utilities.
"""

from app.models.comic import CharacterProfile
from app.prompts.image_prompt import format_panel_image_prompt, get_negative_prompt
from app.prompts.outline_prompt import build_outline_prompt
from app.prompts.story_prompt import build_story_prompt


def test_build_outline_prompt():
    """Verifies that outline prompt correctly injects parameters and constraints."""
    prompt = build_outline_prompt(
        story_idea="A time traveler gets stranded in Renaissance Florence.",
        panel_count=4,
        genre="Sci-Fi",
        tone="Humorous",
        art_style="Retro Vintage Pop Art",
        main_character="Dr. Emmett",
        setting="Florence 1504",
    )

    assert "STORY PREMISE:" in prompt
    assert "Renaissance Florence" in prompt
    assert "Requested Panel Count: 4" in prompt
    assert "Retro Vintage Pop Art" in prompt
    assert "Dr. Emmett" in prompt
    assert "ComicOutlineSchema JSON" in prompt


def test_build_story_prompt():
    """Verifies story refinement prompt embeds JSON outline and dialogue limits."""
    mock_outline = {
        "title": "Clockwork Knight",
        "panels": [
            {"panel_number": 1, "scene": "The knight wakes up."}
        ]
    }
    prompt = build_story_prompt(
        outline_data=mock_outline,
        art_style="Classic Comic Book (90s Marvel/DC)",
        tone="Epic / Action-Packed",
    )

    assert "Clockwork Knight" in prompt
    assert "ComicDetailedStorySchema" in prompt
    assert "under 15 words" in prompt
    assert "no speech bubbles, no text" in prompt


def test_format_panel_image_prompt_character_continuity():
    """Verifies character appearance continuity is synthesized into image prompt."""
    characters = [
        CharacterProfile(
            name="Valeria",
            role="Protagonist",
            appearance="Athletic build, piercing silver eyes",
            hair="Crimson braided hair",
            clothing="Golden winged armor and scarlet cloak",
            personality="Valiant",
            distinctive_features="Sunburst insignia medallion",
        )
    ]

    image_prompt = format_panel_image_prompt(
        base_visual_prompt="Valeria draws her broadsword at the gates of the citadel.",
        art_style="Classic Comic Book (90s Marvel/DC)",
        character_profiles=characters,
        scene_number=1,
    )

    assert "Valeria draws her broadsword" in image_prompt
    assert "Crimson braided hair" in image_prompt
    assert "Golden winged armor" in image_prompt
    assert "90s western comic book art style" in image_prompt


def test_negative_prompt_rules():
    """Verifies negative prompts exclude speech bubbles, lettering, and watermarks."""
    neg = get_negative_prompt("Classic Comic Book (90s Marvel/DC)")
    assert "speech bubble" in neg
    assert "watermark" in neg
    assert "text" in neg
    assert "typography" in neg

    manga_neg = get_negative_prompt("Japanese Manga (Clean Ink)")
    assert "color" in manga_neg
