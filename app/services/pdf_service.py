"""
ComicCraft - PDF Export Service
Builds high-resolution, multi-page, publication-grade comic PDFs with ReportLab.
"""

from pathlib import Path
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.models.comic import Comic
from app.utils.file_manager import file_manager
from app.utils.logger import logger


class PDFServiceError(Exception):
    """Raised when PDF generation encounters an unrecoverable failure."""
    pass


class ComicPDFService:
    """Renders structured comic books into printable, publication-quality PDFs."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Configures typography styles for titles, captions, and speech bubbles."""
        self.title_style = ParagraphStyle(
            name="ComicTitle",
            parent=self.styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=30,
            alignment=1,  # Center
            textColor=colors.HexColor("#1A1A24"),
            spaceAfter=6,
        )
        self.meta_style = ParagraphStyle(
            name="ComicMeta",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#6366F1"),
            spaceAfter=12,
        )
        self.caption_style = ParagraphStyle(
            name="ComicCaption",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1F2937"),
        )
        self.speaker_style = ParagraphStyle(
            name="ComicSpeaker",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#312E81"),
        )
        self.dialogue_style = ParagraphStyle(
            name="ComicDialogue",
            parent=self.styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#111827"),
        )
        self.panel_header_style = ParagraphStyle(
            name="PanelHeader",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=colors.white,
        )

    def generate_pdf(self, comic: Comic) -> tuple[Path, str]:
        """
        Builds the comic PDF document.
        Returns tuple of (absolute_pdf_path, web_accessible_url).
        """
        logger.info(f"Generating PDF for Comic [{comic.comic_id[:8]}] - '{comic.title}'")

        pdf_filename = file_manager.generate_pdf_filename(comic.comic_id, comic.title)
        pdf_path = file_manager.get_pdf_path(pdf_filename)
        static_pdf_path = settings.STATIC_DIR / "generated" / pdf_filename

        # Document setup: Letter with 0.4 inch margins for optimal comic real estate
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=0.4 * inch,
            rightMargin=0.4 * inch,
            topMargin=0.4 * inch,
            bottomMargin=0.4 * inch,
        )

        story = []

        # 1. Comic Title Header
        story.append(Paragraph(comic.title.upper(), self.title_style))
        meta_line = f"GENRE: {comic.genre.upper()}  |  STYLE: {comic.art_style.upper()}  |  ISSUE #1"
        story.append(Paragraph(meta_line, self.meta_style))
        story.append(
            HRFlowable(
                width="100%",
                thickness=2,
                color=colors.HexColor("#1F2937"),
                spaceAfter=14,
            )
        )

        # 2. Panels Assembly
        # We group panels into pages: 2 panels per page yields great comic readability
        panels_per_page = 2
        for idx, panel in enumerate(comic.panels):
            panel_card = self._build_panel_element(panel, doc.width)
            story.append(KeepTogether(panel_card))
            story.append(Spacer(1, 14))

            # Page break after every `panels_per_page` except the last
            if (idx + 1) % panels_per_page == 0 and (idx + 1) < len(comic.panels):
                story.append(PageBreak())

        # Build document with footer callback for page numbers
        try:
            doc.build(
                story,
                onFirstPage=self._draw_page_decorations,
                onLaterPages=self._draw_page_decorations,
            )

            # Mirror to static generated folder for immediate download
            static_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copyfile(pdf_path, static_pdf_path)

            logger.info(f"PDF generated successfully at {pdf_path}")
            return pdf_path, f"/static/generated/{pdf_filename}"

        except Exception as e:
            logger.error(f"PDF generation failed for comic {comic.comic_id}: {e}")
            raise PDFServiceError(f"Failed to generate comic PDF: {e}")

    def _build_panel_element(self, panel, available_width: float):
        """Constructs a composite Flowable representing one bounded comic panel."""
        elements = []

        # Panel Header Badge
        header_text = f"  PANEL {panel.panel_number}: {panel.scene[:70]}"
        header_p = Paragraph(header_text, self.panel_header_style)
        header_table = Table([[header_p]], colWidths=[available_width])
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F2937")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(header_table)

        # Panel Content Table: Left = Illustration (approx 240pt), Right = Narration & Dialogue
        img_col_width = 240
        text_col_width = available_width - img_col_width - 8

        # Image flowable
        img_flowable = self._resolve_image_flowable(panel.image_filename, img_col_width, img_col_width)

        # Text flowable list
        text_elements = []

        # Narration caption box (classic comic yellow box)
        if panel.narration:
            narr_p = Paragraph(f"<b>NARRATION:</b> {panel.narration}", self.caption_style)
            narr_table = Table([[narr_p]], colWidths=[text_col_width - 12])
            narr_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),  # Comic Yellow
                        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#D97706")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            text_elements.append(narr_table)
            text_elements.append(Spacer(1, 6))

        # Dialogue speech items
        if panel.dialogue:
            for dia in panel.dialogue:
                speaker_p = Paragraph(dia.speaker.upper(), self.speaker_style)
                quote_symbol = '"'
                balloon_p = Paragraph(f"{quote_symbol}{dia.text}{quote_symbol}", self.dialogue_style)

                dia_table = Table([[speaker_p], [balloon_p]], colWidths=[text_col_width - 16])
                dia_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                            ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#4B5563")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                text_elements.append(dia_table)
                text_elements.append(Spacer(1, 5))

        # If no dialogue or narration
        if not text_elements:
            text_elements.append(Paragraph("<i>[Dramatic silent action]</i>", self.dialogue_style))

        # Put Image and Text into a side-by-side Table
        row_table = Table([[img_flowable, text_elements]], colWidths=[img_col_width, text_col_width])
        row_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#1F2937")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(row_table)

        return elements

    def _resolve_image_flowable(self, filename: Optional[str], width: float, height: float):
        """Safely loads image from disk or renders an illustrated placeholder."""
        if filename:
            try:
                img_path = file_manager.get_image_path(filename)
                if file_manager.file_exists(img_path):
                    return RLImage(str(img_path), width=width, height=height)
            except Exception as e:
                logger.warning(f"Failed to embed image {filename}: {e}")

        # Fallback Placeholder Table
        placeholder_p = Paragraph(
            "<b>[COMIC PANEL ILLUSTRATION]</b><br/><font size='7'>Image being rendered or offline</font>",
            self.dialogue_style,
        )
        placeholder_table = Table([[placeholder_p]], colWidths=[width], rowHeights=[height])
        placeholder_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E5E7EB")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#9CA3AF")),
                ]
            )
        )
        return placeholder_table

    def _draw_page_decorations(self, canvas, doc):
        """Renders page numbering and comic watermark on footer."""
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6B7280"))

        footer_text = f"COMICCRAFT AI  •  PAGE {doc.page}"
        canvas.drawCentredString(letter[0] / 2.0, 0.25 * inch, footer_text)

        canvas.restoreState()


pdf_service = ComicPDFService()
