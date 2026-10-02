"""
Tests for ComicCraft FastAPI Routes and Endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.comic import Comic, ComicPanel, GenerationState, PanelState
from app.services.comic_service import comic_service


client = TestClient(app)


def test_health_endpoint():
    """Verifies health check endpoint returns 200 and standard status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "comiccraft"
    assert "version" in data


def test_landing_page_renders():
    """Verifies home page renders clean studio interface."""
    response = client.get("/")
    assert response.status_code == 200
    assert "COMICCRAFT" in response.text
    assert "Turn your ideas into comics" in response.text
    assert 'name="story_idea"' in response.text
    assert "CREATE MY COMIC" in response.text


def test_case_10_mobile_ui_responsiveness():
    """CASE 10: Verifies viewport meta tag and responsive layout hooks are present."""
    response = client.get("/")
    assert response.status_code == 200
    # Responsive viewport
    assert 'name="viewport"' in response.text
    assert "width=device-width" in response.text
    # Grid classes
    assert "grid" in response.text


def test_post_generate_json_success():
    """Verifies JSON POST to /generate creates comic and returns redirect."""
    payload = {
        "story_idea": "A detective in 2099 investigates a cyber robbery.",
        "genre": "Cyberpunk",
        "art_style": "Vibrant Modern Webtoon",
        "panel_count": 4,
        "tone": "Dark & Gritty",
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "comic_id" in data
    assert data["redirect_url"].startswith("/generating/")


def test_post_generate_form_success():
    """Verifies standard HTML form POST to /generate redirects to progress page."""
    form_data = {
        "story_idea": "A magical cat saves the kingdom from an enchanted sleep.",
        "genre": "Fantasy",
        "tone": "Whimsical",
        "art_style": "Watercolor Comic Illustration",
        "panel_count": 2,
    }
    response = client.post("/generate", data=form_data, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/generating/")


def test_post_generate_validation_error_handling():
    """Verifies empty or invalid inputs return user-friendly errors."""
    # Empty prompt
    response = client.post("/generate", json={"story_idea": "   ", "panel_count": 4})
    assert response.status_code in (400, 422)

    # Invalid panel count
    response = client.post(
        "/generate",
        json={"story_idea": "A valid story idea about wizards.", "panel_count": 9},
    )
    assert response.status_code in (400, 422)


def test_comic_status_polling():
    """Verifies status endpoint returns progression states."""
    # Pre-register a dummy comic
    comic = Comic(
        comic_id="test_status_comic_123",
        title="Status Check Comic",
        genre="Superhero",
        panel_count=4,
        status=GenerationState.STORY_GENERATING,
        stage_description="Writing dialogue...",
    )
    comic_service.register_comic(comic)

    response = client.get("/comic/test_status_comic_123/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "STORY_GENERATING"
    assert data["stage_description"] == "Writing dialogue..."
    assert data["progress_percent"] > 0


def test_comic_preview_and_pdf_download_flow():
    """Verifies full comic preview and PDF download flow."""
    comic = Comic(
        comic_id="flow_test_comic_456",
        title="The Final Frontier",
        genre="Sci-Fi",
        art_style="Retro Vintage Pop Art",
        panel_count=2,
        status=GenerationState.COMPLETED,
        panels=[
            ComicPanel(
                panel_number=1,
                scene="Spaceship enters warp speed.",
                narration="Approaching the event horizon.",
                visual_prompt="Spaceship speeding past blue stars.",
                status=PanelState.READY,
            ),
            ComicPanel(
                panel_number=2,
                scene="Sensors detect a new world.",
                narration="Touchdown confirmed.",
                visual_prompt="Lush green alien world.",
                status=PanelState.READY,
            ),
        ],
    )
    comic_service.register_comic(comic)

    # 1. Preview View
    preview_res = client.get("/comic/flow_test_comic_456")
    assert preview_res.status_code == 200
    assert "The Final Frontier" in preview_res.text
    assert "PANEL #1" in preview_res.text

    # 2. PDF Download
    pdf_res = client.get("/comic/flow_test_comic_456/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # 3. Export Success Page
    export_res = client.get("/export-success/flow_test_comic_456")
    assert export_res.status_code == 200
    assert "YOUR COMIC IS READY" in export_res.text


def test_regenerate_panel_endpoint():
    """Verifies single panel regeneration updates panel image."""
    comic = Comic(
        comic_id="regen_test_comic",
        title="Regen Demo",
        panel_count=2,
        status=GenerationState.COMPLETED,
        panels=[
            ComicPanel(
                panel_number=1,
                scene="Initial standoff.",
                visual_prompt="Two characters staring down.",
                status=PanelState.READY,
            )
        ],
    )
    comic_service.register_comic(comic)

    regen_res = client.post(
        "/comic/regen_test_comic/regenerate-panel",
        json={
            "panel_number": 1,
            "custom_prompt_hint": "Add dramatic thunderstorm in background.",
            "regenerate_image_only": True,
        },
    )
    assert regen_res.status_code == 200
    data = regen_res.json()
    assert data["success"] is True
    assert data["panel_number"] == 1
    assert data["image_url"].startswith("/static/generated/")
