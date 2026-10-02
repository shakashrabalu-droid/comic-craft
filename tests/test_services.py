"""
Tests for ComicCraft Business Services: Gemini, Image, Layout, PDF, and Comic Pipeline.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.schemas.comic_schema import ComicOutlineSchema
from app.services.comic_service import comic_service
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services.image_service import image_service
from app.services.layout_service import layout_service
from app.services.pdf_service import pdf_service
from app.utils.file_manager import file_manager


@pytest.mark.asyncio
async def test_case_1_simple_4_panel_superhero_story():
    """CASE 1: Simple 4-panel superhero story pipeline execution."""
    req = CreateComicRequest(
        story_idea="A young astronomer gains solar powers when an experimental orbital lens misfires.",
        genre="Superhero",
        main_character="Helios",
        tone="Epic / Action-Packed",
        art_style="Classic Comic Book (90s Marvel/DC)",
        panel_count=4,
    )
    comic = comic_service.initiate_comic(req)
    assert comic.status == GenerationState.QUEUED
    assert comic.panel_count == 4

    # Execute pipeline (uses offline generator when GEMINI_API_KEY is not set)
    await comic_service.execute_pipeline(comic.comic_id, req.story_idea)

    assert comic.status == GenerationState.COMPLETED
    assert len(comic.panels) == 4
    for panel in comic.panels:
        assert panel.image_filename is not None
        assert panel.status == PanelState.READY
    assert comic.pdf_filename is not None


@pytest.mark.asyncio
async def test_case_2_fantasy_story_with_multiple_characters():
    """CASE 2: Fantasy story with multiple characters and character continuity."""
    req = CreateComicRequest(
        story_idea="An elven ranger and a dwarf blacksmith must forge a celestial seal before midnight.",
        genre="Fantasy",
        main_character="Elrond & Thrain",
        supporting_characters="The Shadow Wyrm",
        setting="The Molten Forge of Khazad",
        tone="Dramatic",
        art_style="Dark Fantasy & Gothic Ink",
        panel_count=3,
    )
    comic = comic_service.initiate_comic(req)
    await comic_service.execute_pipeline(comic.comic_id, req.story_idea)

    assert comic.status == GenerationState.COMPLETED
    assert len(comic.panels) == 3
    # Check character continuity profiles
    assert len(comic.characters) >= 1
    for char in comic.characters:
        assert char.name is not None
        assert char.clothing is not None


@pytest.mark.asyncio
async def test_case_3_comedy_story():
    """CASE 3: Comedy story with punchy dialogue."""
    req = CreateComicRequest(
        story_idea="A cat accidentally joins a superhero guild and solves crimes by knocking coffee cups off tables.",
        genre="Comedy",
        main_character="Captain Whiskers",
        tone="Humorous",
        art_style="Retro Vintage Pop Art",
        panel_count=2,
    )
    comic = comic_service.initiate_comic(req)
    await comic_service.execute_pipeline(comic.comic_id, req.story_idea)

    assert comic.status == GenerationState.COMPLETED
    assert len(comic.panels) == 2


@pytest.mark.asyncio
async def test_case_7_ai_response_failure():
    """CASE 7: AI response failure recovery and graceful error handling."""
    service = GeminiService(api_key="test-key-mock")

    # Mock client generate_content to raise an exception
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Simulated Gemini API 503 Unavailable")
    service._client = mock_client

    with pytest.raises(GeminiServiceError, match="outline generation failed"):
        await service.generate_outline(
            story_idea="A broken pipeline scenario.",
            panel_count=4,
            genre="Sci-Fi",
            tone="Dramatic",
            art_style="Classic Comic Book (90s Marvel/DC)",
        )


@pytest.mark.asyncio
async def test_case_8_image_generation_fallback():
    """CASE 8: Image generation failure falls back to stylized canvas without crashing."""
    filename, url = await image_service.generate_panel_image(
        comic_id="test_fallback_comic",
        panel_number=1,
        visual_prompt="Hero stands atop a skyscraper in the pouring rain.",
        art_style="Noir Graphic Novel (High Contrast Shadows)",
        scene_description="Dramatic rain confrontation.",
    )
    assert filename.startswith("test_fallback_comic_panel_1_")
    assert filename.endswith(".png")
    assert url.startswith("/static/generated/")

    path = file_manager.get_image_path(filename)
    assert file_manager.file_exists(path)
    assert path.stat().st_size > 0


def test_case_9_pdf_export_and_missing_image_resilience():
    """CASE 9: PDF export succeeds even if an image file is missing on disk."""
    dummy_comic = Comic(
        comic_id="pdf_test_comic",
        title="The Fallback Avenger",
        genre="Superhero",
        art_style="Classic Comic Book (90s Marvel/DC)",
        panel_count=2,
        panels=[
            ComicPanel(
                panel_number=1,
                scene="The city slumbers.",
                narration="Night had fallen across Sector 7.",
                dialogue=[
                    DialogueItem(speaker="HERO", text="No crime tonight.", style=DialogueStyle.SPEECH)
                ],
                visual_prompt="Wide city view.",
                image_filename="non_existent_image_12345.png",
                status=PanelState.READY,
            ),
            ComicPanel(
                panel_number=2,
                scene="A siren wails in the distance.",
                narration="Or so he thought.",
                dialogue=[
                    DialogueItem(speaker="HERO", text="I spoke too soon!", style=DialogueStyle.SHOUT)
                ],
                visual_prompt="Close up face.",
                image_filename=None,
                status=PanelState.READY,
            ),
        ],
    )

    pdf_path, pdf_url = pdf_service.generate_pdf(dummy_comic)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000  # Valid non-empty PDF
    assert pdf_url.endswith(".pdf")


def test_gemini_json_cleaning():
    """Verifies that markdown code blocks and wrapping text are stripped safely."""
    raw_markdown = """```json
    {
        "title": "Cleaned Comic",
        "genre": "Sci-Fi"
    }
    ```"""
    cleaned = GeminiService._clean_json_response(raw_markdown)
    assert cleaned.startswith("{")
    assert cleaned.endswith("}")
    assert "Cleaned Comic" in cleaned


def test_file_manager_traversal_prevention():
    """Verifies directory traversal attacks are stopped."""
    with pytest.raises(ValueError, match="Directory traversal not permitted"):
        file_manager.get_safe_path(settings.IMAGES_DIR, "../../etc/passwd")


def test_layout_service_model_preparation():
    """Verifies layout service accurately enriches comic view model with balloon alignment."""
    dummy_comic = Comic(
        comic_id="layout_test",
        title="Grid Test",
        panel_count=4,
        panels=[
            ComicPanel(
                panel_number=1,
                scene="Meeting",
                dialogue=[
                    DialogueItem(speaker="Alice", text="Hello", style=DialogueStyle.SPEECH),
                    DialogueItem(speaker="Bob", text="Look out!", style=DialogueStyle.SHOUT),
                ],
                visual_prompt="Two characters meet.",
            )
        ],
    )
    vm = layout_service.prepare_comic_view_model(dummy_comic)
    assert vm["title"] == "Grid Test"
    assert vm["layout"]["name"] == "Quad 2x2 Comic Matrix"
    assert len(vm["panels"]) == 1
    assert vm["panels"][0]["dialogue"][0]["position_class"] == "balloon-top-left"
    assert vm["panels"][0]["dialogue"][1]["position_class"] == "balloon-top-right"
