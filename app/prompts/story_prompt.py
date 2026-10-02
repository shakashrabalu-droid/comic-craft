"""
ComicCraft - Story and Dialogue Refinement Prompt
Expands the comic outline into production-ready dialogue, emotional beats, and panel visual prompts.
"""

from typing import Any, Dict


STORY_SYSTEM_INSTRUCTION = """You are a senior comic book dialogue specialist, script editor, and storyboard artist.
Your role is to take a comic outline and produce final polished script panels.

CRITICAL GUIDELINES:
1. DIALOGUE ECONOMY: Keep speech bubbles concise, natural, and expressive. Avoid wordy monologues. Dialogue must never exceed 15 words per balloon.
2. CHARACTER CONTINUITY: Ensure characters retain their names, relationships, personality quirks, and signature visual elements from the character profiles.
3. EMOTIONAL INTENSITY: Explicitly define the emotional context of each panel to guide acting and facial expressions.
4. VISUAL PROMPT CRAFTING: For each panel, generate a focused, ultra-detailed visual prompt specifically engineered for comic illustration.
   - Describe character physical traits exactly matching their profile.
   - Specify dynamic comic composition (e.g. low-angle upward perspective, close-up with motion blur, two-shot confrontation).
   - Describe atmospheric lighting and palette.
   - Strictly prohibit text, speech balloons, signatures, or panels inside the art.
5. JSON STRUCTURE: Conform strictly to the ComicDetailedStorySchema.
"""


def build_story_prompt(outline_data: Dict[str, Any], art_style: str, tone: str) -> str:
    """Builds prompt to polish story, dialogue, and generate focused image prompts."""
    import json

    serialized_outline = json.dumps(outline_data, indent=2)

    return f"""Take the following comic outline and produce the final, polished comic panels with refined dialogue and focused image prompts.

OUTLINE DATA:
{serialized_outline}

STYLE & TONE TARGETS:
- Art Style: {art_style}
- Tone: {tone}

REQUIREMENTS:
For each panel (matching the original count and order):
1. 'panel_number': Same panel number as outline.
2. 'scene': Refined scene action description.
3. 'narration': Polish caption text if appropriate (concise, atmospheric, or null).
4. 'dialogue': Polish dialogue lines. Keep each line punchy (under 15 words) and natural for comic balloons.
5. 'emotional_context': Emotional state, tension, and facial expression cues.
6. 'visual_prompt': Highly detailed illustration prompt. Include:
   - Art style aesthetic cues: "{art_style}"
   - Exact character physical details (costume, hair color, distinctive marks) matching the outline's character profiles
   - Specific camera composition and framing (e.g., dynamic Dutch angle, wide shot, extreme close-up)
   - Lighting and environment atmosphere
   - Quality keywords: "masterpiece, sharp focus, professional comic art, highly detailed, vivid color grading"
   - Negative constraints: "pure visual art, no speech bubbles, no text, no lettering, no comic borders, no watermark"

Return the complete response strictly following the ComicDetailedStorySchema JSON.
"""
