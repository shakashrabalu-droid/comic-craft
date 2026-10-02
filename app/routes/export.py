"""
ComicCraft - PDF Export and Download Routes
Serves generated comic PDFs securely as download attachments.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.config import settings
from app.services.comic_service import comic_service
from app.services.pdf_service import pdf_service
from app.utils.file_manager import file_manager
from app.utils.logger import logger

router = APIRouter(tags=["Export"])


@router.get("/comic/{comic_id}/pdf")
async def download_comic_pdf(comic_id: str):
    """Downloads the generated comic as a print-ready PDF."""
    comic = comic_service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found.")

    # If PDF was not generated yet, try to generate it now
    if not comic.pdf_filename:
        try:
            pdf_path, pdf_url = pdf_service.generate_pdf(comic)
            comic.pdf_filename = pdf_path.name
            comic.pdf_url = pdf_url
        except Exception as e:
            logger.error(f"On-demand PDF generation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate comic PDF.")

    pdf_file_path = file_manager.get_pdf_path(comic.pdf_filename)
    if not file_manager.file_exists(pdf_file_path):
        # Fallback check static directory
        static_path = settings.STATIC_DIR / "generated" / comic.pdf_filename
        if file_manager.file_exists(static_path):
            pdf_file_path = static_path
        else:
            raise HTTPException(status_code=404, detail="PDF file not found on disk.")

    download_name = file_manager.generate_pdf_filename(comic_id, comic.title)

    return FileResponse(
        path=str(pdf_file_path),
        media_type="application/pdf",
        filename=download_name,
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


@router.get("/comic/{comic_id}/export")
async def trigger_export_flow(comic_id: str):
    """Triggers final export flow and redirects to the success presentation page."""
    comic = comic_service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found.")

    if not comic.pdf_filename:
        try:
            pdf_path, pdf_url = pdf_service.generate_pdf(comic)
            comic.pdf_filename = pdf_path.name
            comic.pdf_url = pdf_url
        except Exception as e:
            logger.error(f"Export generation failed: {e}")

    return RedirectResponse(url=f"/export-success/{comic_id}", status_code=303)
