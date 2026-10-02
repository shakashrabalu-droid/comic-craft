"""
ComicCraft - Image Prompt Engineering Utility
Assembles and sanitizes focused panel prompts for Stable Diffusion and image generation backends.
"""

from typing import List, Optional
from app.models.comic import CharacterProfile


STYLE_MODIFIERS = {
    "Classic Comic Book (90s Marvel/DC)": "90s western comic book art style, bold ink lines, dynamic crosshatching, vibrant primary color palette, Jack Kirby / Jim Lee aesthetic, cinematic comic frame",
    "Japanese Manga (Clean Ink)": "modern Japanese manga illustration, high precision black and white ink line art with subtle screentones, expressive anime facial details, Shonen Jump style, dynamic speed lines",
    "Noir Graphic Novel (High Contrast Shadows)": "gritty noir graphic novel illustration, Frank Miller Sin City style, extreme chiaroscuro contrast, heavy shadows, muted desaturated tones with single accent color, atmospheric rain and fog",
    "Vibrant Modern Webtoon": "crisp modern digital webtoon art style, clean vector-like lineart, soft cel shading, luminous vibrant digital coloring, beautiful lighting highlights, Korean manhwa aesthetic",
    "Retro Vintage Pop Art": "vintage retro 1960s pop art comic print, Roy Lichtenstein style, visible Ben-Day dots, bold thick outlines, saturated primary colors, vintage newsprint paper texture",
    "Dark Fantasy & Gothic Ink": "dark gothic fantasy illustration, intricate etching and stippling, moody dark fantasy, grimdark palette, heavy dramatic shadows, Mike Mignola aesthetic",
    "Watercolor Comic Illustration": "expressive watercolor comic book art, soft bleeding pigments, hand-drawn ink contours, artistic brushstrokes, textured watercolor paper, whimsical and poetic atmosphere",
}

NEGATIVE_PROMPT = (
    "text, typography, words, watermark, signature, speech bubble, dialogue balloon, "
    "caption box, comic borders, frames within frame, multiple panels, split screen, "
    "blurry, distorted anatomy, extra limbs, bad hands, low resolution"
)


def format_panel_image_prompt(
    base_visual_prompt: str,
    art_style: str,
    character_profiles: Optional[List[CharacterProfile]] = None,
    scene_number: Optional[int] = None,
) -> str:
    """
    Synthesizes a cohesive, focused prompt for the image generation model.
    Ensures style modifiers and character appearance continuity are enforced.
    """
    style_suffix = STYLE_MODIFIERS.get(art_style, f"{art_style} comic illustration style, professional comic art")

    character_cues = []
    if character_profiles:
        for char in character_profiles:
            # Add character visual continuity markers
            cues = []
            if char.appearance:
                cues.append(char.appearance)
            if char.hair:
                cues.append(f"{char.hair} hair")
            if char.clothing:
                cues.append(f"wearing {char.clothing}")
            if char.distinctive_features:
                cues.append(char.distinctive_features)
            if cues:
                character_cues.append(f"{char.name} ({', '.join(cues)})")

    continuity_text = f"Characters: {'; '.join(character_cues)}. " if character_cues else ""

    # Clean and combine
    prompt = f"{base_visual_prompt.strip()}. {continuity_text}Aesthetic: {style_suffix}. Masterpiece quality, sharp details, vibrant lighting, clean composition."
    
    # Trim to reasonable length to fit CLIP / SD token limits
    return prompt[:1000]


def get_negative_prompt(art_style: str) -> str:
    """Returns negative prompt tailored to eliminate text, borders and bad artifacts."""
    base_neg = NEGATIVE_PROMPT
    if "Manga" in art_style:
        return f"{base_neg}, color, western comic"
    return base_neg
