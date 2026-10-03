"""
ComicCraft - FLUX Comic Prompt Builder
"""


BASE_COMIC_STYLE = (
    "professional comic book illustration, "
    "clean ink linework, "
    "detailed character design, "
    "cinematic composition, "
    "expressive faces, "
    "dynamic visual storytelling, "
    "detailed environment, "
    "dramatic lighting, "
    "professional digital coloring"
)


DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, "
    "distorted anatomy, "
    "deformed hands, "
    "extra fingers, "
    "missing fingers, "
    "duplicate characters, "
    "duplicate limbs, "
    "cropped face, "
    "distorted face, "
    "watermark, "
    "logo, "
    "unreadable text"
)


def build_comic_prompt(
    scene: str,
    character: str | None = None,
    location: str | None = None,
    action: str | None = None,
    mood: str | None = None,
    camera: str | None = None,
    style: str | None = None,
) -> str:

    parts = []

    parts.append(
        style
        if style
        else BASE_COMIC_STYLE
    )

    parts.append(
        f"Scene: {scene}"
    )

    if character:
        parts.append(
            f"Character: {character}"
        )

    if location:
        parts.append(
            f"Location: {location}"
        )

    if action:
        parts.append(
            f"Action: {action}"
        )

    if mood:
        parts.append(
            f"Mood: {mood}"
        )

    if camera:
        parts.append(
            f"Camera composition: {camera}"
        )

    parts.append(
        "single comic panel, "
        "clear subject, "
        "coherent perspective, "
        "strong visual hierarchy"
    )

    return ", ".join(parts)
