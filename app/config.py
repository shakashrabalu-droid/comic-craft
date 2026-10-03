"""
ComicCraft - Configuration Module

Centralized application configuration.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# ==================================================
# PROJECT ROOT
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==================================================
# SETTINGS
# ==================================================

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # -----------------------------
    # Application
    # -----------------------------

    APP_NAME: str = "ComicCraft"

    APP_VERSION: str = "1.0.0"

    APP_ENV: str = "development"

    DEBUG: bool = True

    HOST: str = "127.0.0.1"

    PORT: int = 8000

    MAX_REQUEST_SIZE_BYTES: int = 10 * 1024 * 1024


    # -----------------------------
    # Paths
    # -----------------------------

    BASE_DIR: Path = BASE_DIR

    STATIC_DIR: Path = BASE_DIR / "static"

    TEMPLATES_DIR: Path = BASE_DIR / "templates"

    GENERATED_DIR: Path = BASE_DIR / "generated"

    IMAGES_DIR: Path = BASE_DIR / "generated" / "images"

    PDF_DIR: Path = BASE_DIR / "generated" / "pdf"

    TEMP_DIR: Path = BASE_DIR / "generated" / "temporary"


    # -----------------------------
    # Gemini
    # -----------------------------

    GEMINI_API_KEY: Optional[str] = None

    GEMINI_MODEL: str = "gemini-3.8-flash"

    GEMINI_OUTLINE_MODEL: str = "gemini-3.8-flash"

    GEMINI_STORY_MODEL: str = "gemini-3.8-flash"


    # -----------------------------
    # Hugging Face / FLUX
    # -----------------------------

    HF_TOKEN: Optional[str] = None

    HF_PROVIDER: str = "fal-ai"

    FLUX_MODEL: str = "black-forest-labs/FLUX.1-dev"


    # -----------------------------
    # Image Generation
    # -----------------------------

    IMAGE_GENERATION_BACKEND: Literal[
        "auto",
        "huggingface",
        "gemini",
        "fallback",
    ] = "huggingface"

    IMAGE_GENERATION_FALLBACK: str = "fallback"

    IMAGE_WIDTH: int = 1024

    IMAGE_HEIGHT: int = 1024

    IMAGE_STEPS: int = 28

    IMAGE_GUIDANCE_SCALE: float = 3.5


    # -----------------------------
    # Comic Configuration
    # -----------------------------

    ALLOWED_PANEL_COUNTS: tuple[int, ...] = (
        1,
        2,
        3,
        4,
        6,
    )


    # -----------------------------
    # Generation Constraints
    # -----------------------------

    MAX_STORY_IDEA_LENGTH: int = 2000

    MIN_STORY_IDEA_LENGTH: int = 5

    MAX_CHARACTER_NAME_LENGTH: int = 80

    REQUEST_TIMEOUT_SECONDS: float = 120.0


    # -----------------------------
    # Environment Configuration
    # -----------------------------

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


    # -----------------------------
    # Directory Initialization
    # -----------------------------

    def ensure_directories(self) -> None:
        """Create required runtime directories."""

        directories = (
            self.GENERATED_DIR,
            self.IMAGES_DIR,
            self.PDF_DIR,
            self.TEMP_DIR,
            self.STATIC_DIR / "generated",
        )

        for path in directories:
            path.mkdir(
                parents=True,
                exist_ok=True,
            )


# ==================================================
# GLOBAL SETTINGS
# ==================================================

settings = Settings()

settings.ensure_directories()
