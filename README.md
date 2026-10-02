# COMICCRAFT
### Generative AI Comic Story Creation Platform

ComicCraft is a production-ready Generative AI platform that transforms a user's creative story idea into a structured, fully illustrated, publication-grade comic book with narrative continuity, speech balloons, adaptive panel layouts, and printable PDF export.

---

## 1. Project Overview

ComicCraft bridges large language models and generative visual diffusion models to provide a cohesive comic generation studio. Rather than an ad-hoc collection of API calls, ComicCraft executes a staged state machine:
1. **User Input & Validation**: Captures narrative premise, character guidelines, universe setting, tone, art style, and panel counts.
2. **Structured Outline Generation**: Gemini analyzes pacing and establishes multi-character continuity profiles and panel beats.
3. **Story & Dialogue Refinement**: Polishes punchy speech bubbles (under 15 words per balloon) and atmospheric caption narration.
4. **Focused Panel Visual Prompt Synthesis**: Synthesizes targeted illustration prompts enforcing art styles and character visual traits while explicitly excluding text and bubble artifacts.
5. **Panel Illustration Generation**: Synthesizes illustrations via Hugging Face Stable Diffusion, Gemini Image API, or a resilient Comic Canvas fallback.
6. **Responsive Layout Builder**: Dynamically organizes panels into responsive grids and balances speech bubble placement.
7. **Interactive Preview**: Real-time canvas with live panel redrawing and dialog inspection.
8. **Publication PDF Export**: ReportLab compiles an authentic multi-page printable comic book with embedded typography and artwork.

---

## 2. Architecture & Data Flow

```
                      +-----------------------------+
                      |        User Browser         |
                      |   (Jinja2 + CSS + AJAX)     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |       FastAPI Backend       |
                      |  (Routes, Validation, Auth) |
                      +--------------+--------------+
                                     |
                +--------------------+--------------------+
                |                                         |
                v                                         v
   +-------------------------+               +-------------------------+
   |   AI Comic Orchestrator |               |    Safe File Manager    |
   |     (ComicService)      |               |  (Traversal Prevention) |
   +------------+------------+               +-------------------------+
                |
    +-----------+-----------+-----------------------+
    |                       |                       |
    v                       v                       v
+------------------+  +--------------------+  +--------------------+
|  Gemini Service  |  |   Image Service    |  |   Layout Builder   |
| (Structured JSON |  |  (Stable Diffusion |  | (Responsive Grids  |
|  Outline/Story)  |  |  + Resilient Canvas|  |  & Balloon Stagger)|
+------------------+  +---------+----------+  +---------+----------+
                                |                       |
                                +-----------+-----------+
                                            |
                                            v
                                 +--------------------+
                                 |    PDF Exporter    |
                                 |  (ReportLab Print) |
                                 +----------+---------+
                                            |
                                            v
                                 +--------------------+
                                 |  Export & Preview  |
                                 |  (Download / Redo) |
                                 +--------------------+
```

---

## 3. Tech Stack

- **Backend**: FastAPI, Uvicorn, Pydantic v2, Python 3.12
- **Generative AI & LLMs**: `google-genai` SDK (`gemini-3.8-flash` / `gemini-3.1-pro-preview`)
- **Visual Synthesis**: `huggingface_hub` (`stabilityai/stable-diffusion-xl-base-1.0` or `runwayml/stable-diffusion-v1-5`), Pillow (PIL)
- **PDF Compilation**: ReportLab (High-resolution, multi-page vector typesetting)
- **Frontend**: Jinja2 Templates, Tailwind CSS, Vanilla JavaScript (zero heavy node-modules dependencies)
- **Quality Assurance**: Pytest, Pytest-Asyncio, HTTPX

---

## 4. Project Directory Structure

```
comiccraft/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── config.py                # Pydantic Settings and environment configuration
│   ├── routes/
│   │   ├── pages.py             # Landing, generating, and success views
│   │   ├── comic.py             # Generation, polling, and panel redrawing
│   │   └── export.py            # PDF streaming and export triggers
│   ├── services/
│   │   ├── gemini_service.py    # Structured outline and dialogue expansion
│   │   ├── image_service.py     # Stable Diffusion, Gemini image, & fallback
│   │   ├── comic_service.py     # Pipeline orchestrator & state machine
│   │   ├── layout_service.py    # Responsive grid geometry and balloon alignment
│   │   └── pdf_service.py       # Publication-quality ReportLab PDF generation
│   ├── models/
│   │   ├── comic.py             # Aggregate roots: Comic, ComicPanel, CharacterProfile
│   │   └── requests.py          # API DTOs and status responses
│   ├── schemas/
│   │   └── comic_schema.py      # Strict Pydantic schemas for AI JSON output
│   ├── prompts/
│   │   ├── outline_prompt.py    # Outline system instruction & constraints
│   │   ├── story_prompt.py      # Dialogue & scene expansion prompt
│   │   └── image_prompt.py      # Visual prompt formatting & negative rules
│   └── utils/
│       ├── validation.py        # Input sanitation & boundary checks
│       ├── file_manager.py      # Path traversal safety & file lifecycle
│       └── logger.py            # Structured logging with secret scrubbing
│
├── templates/
│   ├── base.html                # Shared shell, header, and footer
│   ├── index.html               # Comic studio creation form with presets
│   ├── generating.html          # Stage-based real-time progress screen
│   ├── comic_preview.html       # Interactive comic book page preview
│   └── export_success.html      # Comic ready showcase & PDF download
│
├── static/
│   ├── css/style.css            # Authentic comic book styles and speech balloons
│   ├── js/app.js                # Polling, live panel redrawing, character counter
│   └── generated/               # Public mirrors for generated web assets
│
├── generated/
│   ├── images/                  # Stored panel illustrations
│   ├── pdf/                     # Stored comic book PDFs
│   └── temporary/               # Temporary scratch buffers
│
├── tests/
│   ├── test_routes.py           # Endpoint integration tests
│   ├── test_validation.py       # Input sanitation and schema tests
│   ├── test_prompts.py          # AI prompt engineering tests
│   └── test_services.py         # Pipeline, image fallback, and PDF tests
│
├── .env.example                 # Environment template
├── .gitignore                   # Git exclusion rules
├── requirements.txt             # Production dependencies
├── README.md                    # System documentation
└── run.py                       # Local startup script
```

---

## 5. Environment & API Key Configuration

1. Duplicate `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure environment variables in `.env`:
   ```ini
   # Google Gemini API
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_OUTLINE_MODEL=gemini-3.8-flash
   GEMINI_STORY_MODEL=gemini-3.8-flash

   # Hugging Face API (for Stable Diffusion image generation)
   HUGGINGFACE_API_KEY=your_huggingface_token_here
   STABLE_DIFFUSION_MODEL=stabilityai/stable-diffusion-xl-base-1.0

   # Image Generation Backend: auto | huggingface | gemini | fallback
   IMAGE_GENERATION_BACKEND=auto

   # Server Settings
   APP_ENV=development
   HOST=127.0.0.1
   PORT=8000
   DEBUG=True
   ```

> [!NOTE]
> If `GEMINI_API_KEY` or `HUGGINGFACE_API_KEY` are not set, ComicCraft gracefully activates its built-in offline story generator and stylized comic canvas illustration engine. The platform is completely operational for development, testing, and UI demonstration without paid credentials.

---

## 6. Running Locally

### Installation
Ensure Python 3.12+ is installed, then run:

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Start the Application
Run the launcher script:
```bash
python run.py
```
Or with Uvicorn:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser at:
`http://127.0.0.1:8000`

---

## 7. AI Models & Generation Stages

| Stage | Model / Engine | Purpose |
|---|---|---|
| **Outline** | `gemini-3.8-flash` | Pacing, tone, and multi-character continuity profiles |
| **Story & Dialogue** | `gemini-3.8-flash` | Punchy dialogue lines, narrative captions, emotional beats |
| **Prompt Synthesis** | Internal Prompt Engine | Translates character profiles & art style into focused image prompts |
| **Illustrations** | `stabilityai/stable-diffusion-xl-base-1.0` / Gemini Image / Resilient Canvas | High-fidelity panel artwork without embedded text |
| **Typesetting** | ReportLab + Jinja2 | Typesets dialogue balloons and narration outside the illustration |

---

## 8. Automated Testing

Run the comprehensive automated test suite with pytest:

```bash
pytest -v
```

The test suite covers:
- **Case 1**: Simple 4-panel superhero story end-to-end pipeline.
- **Case 2**: Multi-character fantasy story with character continuity checks.
- **Case 3**: Comedy story with punchy dialogue.
- **Case 4**: Empty story prompt rejection.
- **Case 5**: Overlong story prompt rejection (>2000 chars).
- **Case 6**: Invalid panel count constraints.
- **Case 7**: AI response failure handling and graceful error recovery.
- **Case 8**: Image generation failure fallback to stylized canvas.
- **Case 9**: PDF export resilience with missing image handling.
- **Case 10**: Mobile UI responsiveness and viewport compliance.

---

## 9. Security & Production Quality Rules

- **Zero Secrets in Code**: All API keys and secrets load strictly from environment variables.
- **Secret Scrubbing Filter**: All log records are passed through a custom regex scrubber that masks Google AI, Hugging Face, and Bearer tokens before writing to stdout.
- **Path Traversal Prevention**: `SafeFileManager` validates every requested file path against the designated storage root, rejecting any attempts with relative path segments (`../`).
- **Request Size Limiting**: Middleware rejects any HTTP payload exceeding 10MB (HTTP 413).
- **Graceful Error Handling**: Unhandled internal exceptions return standardized user-friendly responses without leaking server stack traces.

---

## 10. Future Improvements

- Background Celery/Redis queue for high-volume distributed generation.
- Interactive drag-and-drop speech bubble positioning on the canvas.
- User account library with saved comic collections and public share links.
