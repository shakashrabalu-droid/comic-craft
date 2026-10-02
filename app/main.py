"""
ComicCraft - FastAPI Application Entrypoint
Generative AI Comic Story Creation Platform
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routes import comic, export, pages
from app.utils.logger import logger
from app.utils.validation import ValidationError


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"*** Starting {settings.APP_NAME} v{settings.APP_VERSION} on {settings.HOST}:{settings.PORT} ***")
    yield
    logger.info(f"*** Shutting down {settings.APP_NAME} ***")


app = FastAPI(
    title="ComicCraft",
    description="Generative AI Comic Story Creation Platform",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS middleware for modern frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure runtime directories exist
settings.ensure_directories()

# Mount Static Assets
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Templates engine
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


# Global Request Size Limiter Middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_SIZE_BYTES:
        logger.warning(f"Request rejected: size {content_length} bytes exceeds limit {settings.MAX_REQUEST_SIZE_BYTES}")
        return JSONResponse(
            status_code=413,
            content={"detail": "Payload Too Large: Maximum allowed request size is 10 MB."},
        )
    return await call_next(request)


# Centralized Exception Handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation failure on {request.url.path}: {exc}")
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "error_banner": str(exc),
            "genres": [
                "Superhero", "Sci-Fi", "Fantasy", "Noir / Detective",
                "Comedy", "Cyberpunk", "Manga / Shonen", "Horror / Mystery",
                "Slice of Life", "Adventure"
            ],
            "tones": [
                "Epic / Action-Packed", "Humorous", "Dark & Gritty",
                "Dramatic", "Whimsical", "Mysterious", "Heartwarming"
            ],
            "art_styles": [
                "Classic Comic Book (90s Marvel/DC)",
                "Japanese Manga (Clean Ink)",
                "Noir Graphic Novel (High Contrast Shadows)",
                "Vibrant Modern Webtoon",
                "Retro Vintage Pop Art",
                "Dark Fantasy & Gothic Ink",
                "Watercolor Comic Illustration"
            ],
            "allowed_panels": settings.ALLOWED_PANEL_COUNTS,
        },
        status_code=400,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error {exc.status_code} - ComicCraft</title>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body class="bg-comic-dark text-white min-h-screen flex items-center justify-center p-6">
            <div class="comic-card max-w-lg w-full text-center p-8 bg-zinc-900 border-2 border-yellow-400 rounded-xl shadow-2xl">
                <div class="text-5xl font-black text-yellow-400 mb-4">{exc.status_code}</div>
                <h2 class="text-2xl font-bold mb-3">Notice</h2>
                <p class="text-zinc-300 mb-6">{exc.detail}</p>
                <a href="/" class="btn-comic-primary px-6 py-3 rounded-lg font-bold inline-block">Return to Studio</a>
            </div>
        </body>
        </html>
        """,
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
    # Never expose technical tracebacks to client in production
    return JSONResponse(
        status_code=500,
        content={"detail": "Comic generation could not be completed. Please try again."},
    )


# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health status and operational telemetry (no sensitive secrets exposed)."""
    return {
        "status": "ok",
        "service": "comiccraft",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "image_backend": settings.IMAGE_GENERATION_BACKEND,
    }


# Include Routers
app.include_router(pages.router)
app.include_router(comic.router)
app.include_router(export.router)
