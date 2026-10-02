"""
ComicCraft - Structured Logging Utility
Provides configured logger with secret scrubbing and formatting.
"""

import logging
import re
import sys
from typing import Any


class SecretFilter(logging.Filter):
    """Filter to scrub potential API keys and tokens from log records."""

    # Matches common API key formats (Google AI, HF tokens, bearer tokens)
    API_KEY_PATTERNS = [
        re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        re.compile(r"hf_[A-Za-z0-9]{34,}"),
        re.compile(r"sk-[A-Za-z0-9-_]{20,}"),
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-_]{16,}", re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.scrub_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.scrub_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.scrub_value(v) for v in record.args)
        return True

    @classmethod
    def scrub_text(cls, text: str) -> str:
        scrubbed = text
        for pattern in cls.API_KEY_PATTERNS:
            scrubbed = pattern.sub("[REDACTED_API_KEY]", scrubbed)
        return scrubbed

    @classmethod
    def scrub_value(cls, val: Any) -> Any:
        if isinstance(val, str):
            return cls.scrub_text(val)
        return val


def setup_logger(name: str = "comiccraft", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | [%(name)s:%(module)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretFilter())

        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_logger("comiccraft")
