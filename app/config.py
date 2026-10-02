"""
ComicCraft - Configuration Module
Centralized environment and application configuration using Pydantic Settings.
"""

from pathlib import Path
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root Directory: comiccraft/
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Application Configuration
    APP_NAME: str = "ComicCraft"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    MAX_REQUEST_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # Paths
    BASE_DIR: Path = BASE_DIR
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    GENERATED_DIR: Path = BASE_DIR / "generated"
    IMAGES_DIR: Path = BASE_DIR / "generated" / "images"
    PDF_DIR: Path = BASE_DIR / "generated" / "pdf"
    TEMP_DIR: Path = BASE_DIR / "generated" / "temporary"

    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_OUTLINE_MODEL: str = "gemini-3.8-flash"
    GEMINI_STORY_MODEL: str = "gemini-3.8-flash"

    # Hugging Face API / Stable Diffusion
    HUGGINGFACE_API_KEY: Optional[str] = None
    STABLE_DIFFUSION_MODEL: str = "stabilityai/stable-diffusion-xl-base-1.0"

    # Image Backend: 'auto' checks HF -> Gemini -> Fallback
    IMAGE_GENERATION_BACKEND: Literal["auto", "huggingface", "gemini", "fallback"] = "auto"

    # Panel Layout Options
    ALLOWED_PANEL_COUNTS: tuple[int, ...] = (1, 2, 3, 4, 6)

    # Generation Constraints
    MAX_STORY_IDEA_LENGTH: int = 2000
    MIN_STORY_IDEA_LENGTH: int = 5
    MAX_CHARACTER_NAME_LENGTH: int = 80
    REQUEST_TIMEOUT_SECONDS: float = 60.0

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        """Create required runtime storage directories if they do not exist."""
        for path in (self.GENERATED_DIR, self.IMAGES_DIR, self.PDF_DIR, self.TEMP_DIR, self.STATIC_DIR / "generated"):
            path.mkdir(parents=True, exist_ok=True)


# Global settings singleton
settings = Settings()
settings.ensure_directories()
