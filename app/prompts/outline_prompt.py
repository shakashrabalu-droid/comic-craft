"""
ComicCraft - Outline Prompt Engineering
Builds system instructions and user prompt for structured comic outline generation.
"""

from typing import Optional


OUTLINE_SYSTEM_INSTRUCTION = """You are a master comic book writer and narrative architect (Marvel, DC, Dark Horse, Image Comics veteran).
Your task is to transform a user's story premise into a structured, gripping, panel-by-panel comic outline.

CRITICAL RULES:
1. NARRATIVE ARC: Distribute dramatic pacing across exactly the requested number of panels (Introduction -> Inciting Moment / Rising Action -> Climax -> Resolution or Cliffhanger).
2. CHARACTER CONTINUITY: Define explicit, consistent character profiles (signature clothing, hairstyle, colors, distinguishing traits) that will persist throughout every panel.
3. DIALOGUE DISCIPLINE: Dialogue must be punchy and succinct (maximum 15 words per line) so it comfortably fits within comic speech balloons without obscuring art.
4. VISUAL FRAMING: Visual descriptions must specify cinematic camera composition (wide shot, dutch angle, close-up, bird's-eye view, dynamic low-angle) and environmental lighting.
5. NO TYPOGRAPHY IN ART: The visual description is strictly for illustrations; do not request printed speech bubbles inside the illustration itself.
6. STRUCTURED OUTPUT: Output strictly valid JSON conforming to the requested schema.
"""


def build_outline_prompt(
    story_idea: str,
    panel_count: int,
    genre: str,
    tone: str,
    art_style: str,
    main_character: Optional[str] = None,
    supporting_characters: Optional[str] = None,
    setting: Optional[str] = None,
    target_audience: Optional[str] = None,
) -> str:
    """Builds the prompt string for outline generation."""
    character_info = main_character if main_character else "Develop a compelling protagonist suited for the premise."
    supporting_info = supporting_characters if supporting_characters else "Create necessary supporting characters / adversaries as needed."
    setting_info = setting if setting else "Establish an atmospheric setting that enhances the tone."
    audience_info = target_audience if target_audience else "General Comic Readers"

    return f"""Create a structured comic book outline based on the following specifications:

STORY PREMISE:
"{story_idea}"

PARAMETERS:
- Requested Panel Count: {panel_count} (You must output exactly {panel_count} panels numbered 1 to {panel_count})
- Genre: {genre}
- Tone: {tone}
- Art Style: {art_style}
- Target Audience: {audience_info}
- Main Character Notes: {character_info}
- Supporting Characters: {supporting_info}
- Setting / World: {setting_info}

REQUIREMENTS:
1. Provide a punchy, unforgettable comic title.
2. Provide a list of character profiles with consistent visual traits (appearance, hair, clothing, signature accessories).
3. Outline exactly {panel_count} panels. For each panel provide:
   - panel_number (integer 1..{panel_count})
   - scene (one concise summary sentence of the action)
   - narration (optional caption box text, or null if pure action/dialogue)
   - dialogue (array of {{speaker, text, style}} where style is 'speech', 'shout', 'whisper', or 'thought')
   - visual_description (camera angle, character positioning, action, lighting, mood)

Return the response strictly matching the ComicOutlineSchema JSON structure.
"""
