"""Generate an Instagram caption from the actual Reel video with Gemini."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
PROCESSING_TIMEOUT_SECONDS = 600


class CaptionError(RuntimeError):
    """Gemini could not produce a usable caption."""


def generate_caption(video_bytes: bytes, filename: str) -> str:
    """Upload a video to Gemini, analyse its visuals/audio, and return a caption."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise CaptionError("GEMINI_API_KEY is not configured.")
    if not video_bytes:
        raise CaptionError("The Reel video is empty.")

    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover
        raise CaptionError("The Gemini SDK is missing. Reinstall the project dependencies.") from exc

    suffix = Path(filename).suffix.lower()
    if suffix not in {".mp4", ".mov"}:
        suffix = ".mp4"

    uploaded = None
    temp_path = None
    client = None
    prompt = (
        "Watch and listen to this complete video. Understand what is actually "
        "shown and heard; do not guess from the filename. Write one engaging, "
        "natural Instagram Reel caption that accurately describes the content. "
        "Add 3 to 8 relevant hashtags at the end. Do not invent names, events, "
        "claims, or details not supported by the video. Keep the caption under "
        "2,000 characters. Return only the caption, without an explanation."
    )

    try:
        client = genai.Client(api_key=api_key)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
            temp.write(video_bytes)
            temp_path = temp.name

        uploaded = client.files.upload(file=temp_path)
        deadline = time.monotonic() + PROCESSING_TIMEOUT_SECONDS
        while not uploaded.state or uploaded.state.name != "ACTIVE":
            state = uploaded.state.name if uploaded.state else "UNSPECIFIED"
            if state == "FAILED":
                raise CaptionError("Gemini could not process the uploaded video.")
            if time.monotonic() >= deadline:
                raise CaptionError("Gemini video processing took too long. Please retry.")
            time.sleep(5)
            uploaded = client.files.get(name=uploaded.name)

        response = client.models.generate_content(model=MODEL, contents=[uploaded, prompt])
        caption = (response.text or "").strip().strip("`").strip()
        if not caption:
            raise CaptionError("Gemini returned an empty caption.")
        if len(caption) > 2200:
            raise CaptionError("Gemini's caption exceeded Instagram's 2,200-character limit.")
        return caption
    except CaptionError:
        raise
    except Exception as exc:
        raise CaptionError(f"Gemini request failed: {exc}") from exc
    finally:
        if uploaded is not None and client is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
