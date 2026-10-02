"""
ComicCraft - Layout Builder Service
Structures panels into responsive grid geometries and positions narrative elements.
"""

from typing import Any, Dict, List
from app.models.comic import Comic, ComicPanel


class LayoutService:
    """Calculates responsive grid placements, balloon positioning, and page compositions."""

    LAYOUT_CONFIGS = {
        1: {
            "name": "Single Splash Page",
            "css_grid": "grid-cols-1",
            "panels_per_page": 1,
            "panel_aspect": "aspect-square md:aspect-[4/3]",
        },
        2: {
            "name": "Duo Dramatic Confrontation",
            "css_grid": "grid-cols-1 md:grid-cols-2",
            "panels_per_page": 2,
            "panel_aspect": "aspect-square",
        },
        3: {
            "name": "Classic Triptych Strip",
            "css_grid": "grid-cols-1 md:grid-cols-3",
            "panels_per_page": 3,
            "panel_aspect": "aspect-[4/5]",
        },
        4: {
            "name": "Quad 2x2 Comic Matrix",
            "css_grid": "grid-cols-1 md:grid-cols-2",
            "panels_per_page": 4,
            "panel_aspect": "aspect-square",
        },
        6: {
            "name": "Six-Panel Standard Book",
            "css_grid": "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
            "panels_per_page": 6,
            "panel_aspect": "aspect-square",
        },
    }

    def get_layout_metadata(self, panel_count: int) -> Dict[str, Any]:
        """Returns layout specification for the requested panel count."""
        return self.LAYOUT_CONFIGS.get(
            panel_count,
            {
                "name": f"{panel_count}-Panel Custom Layout",
                "css_grid": "grid-cols-1 md:grid-cols-2",
                "panels_per_page": panel_count,
                "panel_aspect": "aspect-square",
            },
        )

    def prepare_comic_view_model(self, comic: Comic) -> Dict[str, Any]:
        """
        Enriches comic panels with layout metadata, speech balloon placements,
        and responsive CSS class hooks for rendering in templates or PDF.
        """
        layout_meta = self.get_layout_metadata(comic.panel_count)
        enriched_panels = []

        for idx, panel in enumerate(comic.panels):
            # Calculate staggered speech bubble alignment
            enriched_dialogue = []
            for d_idx, dia in enumerate(panel.dialogue):
                # Alternate balloon positioning: left, right, center
                align_classes = ["balloon-top-left", "balloon-top-right", "balloon-bottom-left", "balloon-bottom-right"]
                align = align_classes[d_idx % len(align_classes)]
                enriched_dialogue.append(
                    {
                        "speaker": dia.speaker,
                        "text": dia.text,
                        "style": dia.style.value if hasattr(dia.style, "value") else str(dia.style),
                        "position_class": align,
                    }
                )

            enriched_panels.append(
                {
                    "panel_id": panel.panel_id,
                    "panel_number": panel.panel_number,
                    "scene": panel.scene,
                    "narration": panel.narration,
                    "dialogue": enriched_dialogue,
                    "image_url": panel.image_url or "/static/images/placeholder.png",
                    "emotional_context": panel.emotional_context,
                    "status": panel.status.value if hasattr(panel.status, "value") else str(panel.status),
                }
            )

        return {
            "comic_id": comic.comic_id,
            "title": comic.title,
            "genre": comic.genre,
            "theme": comic.theme,
            "tone": comic.tone,
            "art_style": comic.art_style,
            "characters": [c.model_dump() for c in comic.characters],
            "panel_count": comic.panel_count,
            "layout": layout_meta,
            "panels": enriched_panels,
            "created_at": comic.created_at.strftime("%B %d, %Y - %H:%M UTC"),
            "pdf_url": comic.pdf_url,
        }


layout_service = LayoutService()
