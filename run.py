"""
ComicCraft - Local Development Server Launcher
Usage: python run.py
"""

import uvicorn
from app.config import settings
from app.utils.logger import logger


def main():
    logger.info(f"Launching ComicCraft server at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
