"""
ComicCraft - Safe File Manager Utility
Manages storage paths, directory traversal prevention, and unique file generation.
"""

import os
import re
import uuid
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.logger import logger


class SafeFileManager:
    """Manages file storage safely ensuring no directory traversal or data exposure."""

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Sanitizes a string to be safely used as a filename."""
        cleaned = re.sub(r"[^\w\s-]", "", name).strip().lower()
        cleaned = re.sub(r"[-\s]+", "_", cleaned)
        return cleaned[:50] or "comic"

    @classmethod
    def get_safe_path(cls, base_dir: Path, target_filename: str) -> Path:
        """Resolves target_filename within base_dir and asserts it does not escape base_dir."""
        # Detect traversal patterns explicitly
        if ".." in target_filename or target_filename.startswith(("/", "\\")):
            logger.error(f"Directory traversal attempt detected: {target_filename}")
            raise ValueError("Invalid file path: Directory traversal not permitted")

        resolved_base = base_dir.resolve()
        resolved_path = (base_dir / target_filename).resolve()

        if not str(resolved_path).startswith(str(resolved_base)):
            logger.error(f"Directory traversal attempt detected: {target_filename}")
            raise ValueError("Invalid file path: Directory traversal not permitted")

        return resolved_path

    @classmethod
    def generate_image_filename(cls, comic_id: str, panel_number: int, ext: str = "png") -> str:
        """Generates a predictable yet collision-free filename for a comic panel image."""
        clean_ext = ext.lstrip(".")
        return f"{comic_id}_panel_{panel_number}_{uuid.uuid4().hex[:8]}.{clean_ext}"

    @classmethod
    def generate_pdf_filename(cls, comic_id: str, title: str) -> str:
        """Generates a clean filename for the exported comic PDF."""
        clean_title = cls.sanitize_filename(title)
        return f"{clean_title}_{comic_id[:8]}.pdf"

    @classmethod
    def get_image_path(cls, filename: str) -> Path:
        """Returns safe path in images directory."""
        return cls.get_safe_path(settings.IMAGES_DIR, filename)

    @classmethod
    def get_pdf_path(cls, filename: str) -> Path:
        """Returns safe path in PDF directory."""
        return cls.get_safe_path(settings.PDF_DIR, filename)

    @classmethod
    def file_exists(cls, path: Path) -> bool:
        """Checks if a file exists and is indeed a file."""
        return path.exists() and path.is_file()

    @classmethod
    def cleanup_file(cls, path: Path) -> bool:
        """Safely removes a file if it exists."""
        try:
            if cls.file_exists(path):
                path.unlink()
                logger.info(f"Cleaned up file: {path.name}")
                return True
        except Exception as e:
            logger.warning(f"Failed to cleanup file {path}: {e}")
        return False


file_manager = SafeFileManager()
