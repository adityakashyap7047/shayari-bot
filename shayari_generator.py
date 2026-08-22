"""
Shayari Generator — picks from a curated collection of shayaris.
Uses Gemini AI only for generating YouTube titles.

Supports multi-channel: each channel can have its own shayari collection
and theme filter.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime

from dotenv import load_dotenv
from google import genai

import config

load_dotenv()

# Legacy path for backward compatibility (single-channel mode)
COLLECTION_FILE = os.path.join(config.BASE_DIR, "shayari_collection.json")


def _get_client() -> genai.Client:
    """Initialise the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise RuntimeError(
            "GEMINI_API_KEY is not set.  "
            "Get one from https://aistudio.google.com/ and add it to .env"
        )
    return genai.Client(api_key=api_key)


def _load_collection(collection_path: str | None = None) -> dict:
    """Load the shayari collection from JSON file.

    Parameters
    ----------
    collection_path : str, optional
        Path to a channel-specific collection. Defaults to root COLLECTION_FILE.
    """
    path = collection_path or COLLECTION_FILE
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Shayari collection not found: {path}\n"
            "Please create shayari_collection.json with your shayaris."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_collection(data: dict, collection_path: str | None = None) -> None:
    """Save updated collection (with used_ids tracking)."""
    path = collection_path or COLLECTION_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _pick_shayari(data: dict, themes: list[str] | None = None) -> dict | None:
    """Pick a random unused shayari from the collection.

    Parameters
    ----------
    data : dict
        The loaded shayari collection data.
    themes : list[str], optional
        If provided, only pick shayaris whose theme is in this list.
        If empty or None, all shayaris are eligible.

    If all have been used, reset the used list and start over.
    """
    # Filter by themes if specified
    if themes:
        eligible = [s for s in data["shayaris"] if s.get("theme", "") in themes]
    else:
        eligible = data["shayaris"]

    if not eligible:
        print(f"  ⚠ No shayaris found for themes: {themes} — using all shayaris")
        eligible = data["shayaris"]

    all_ids = [s["id"] for s in eligible]
    used_ids = set(data.get("used_ids", []))

    available_ids = [sid for sid in all_ids if sid not in used_ids]

    # All used up — reset and start fresh
    if not available_ids:
        total = len(eligible)
        print(f"  🔄 All {total} shayaris used! Resetting collection…")
        data["used_ids"] = []
        available_ids = all_ids

    chosen_id = random.choice(available_ids)

    # Mark as used
    data["used_ids"].append(chosen_id)

    # Find and return the shayari
    for s in eligible:
        if s["id"] == chosen_id:
            return s
    return None


def generate_shayari(
    theme: str | None = None,
    channel=None,
    max_retries: int = 3,
) -> dict:
    """
    Pick a shayari from the curated collection and generate a title.

    Parameters
    ----------
    theme : str, optional
        Override theme (for CLI --theme flag).
    channel : Channel, optional
        Channel object with themes and collection path.
    max_retries : int
        Number of retries for title generation.

    Returns
    -------
    dict with keys:
        - "lines"  : list[str]  — the lines of shayari
        - "theme"  : str        — the theme
        - "title"  : str        — a short YouTube-friendly title
        - "full"   : str        — the full shayari as one string
    """
    # Determine collection path and themes from channel
    collection_path = None
    channel_themes = None

    if channel is not None:
        collection_path = channel.shayari_collection_path
        if channel.themes:
            channel_themes = channel.themes
        print(f"  📺 Channel: {channel.name} ({channel.handle})")

    # Load collection and pick a random unused shayari
    data = _load_collection(collection_path)
    shayari = _pick_shayari(data, themes=channel_themes)

    if shayari is None:
        raise RuntimeError("Could not pick a shayari from the collection.")

    lines = shayari["lines"]
    shayari_theme = shayari.get("theme", theme or "zindagi")
    full_text = "\n".join(lines)

    # Save updated used_ids
    _save_collection(data, collection_path)

    remaining = len(data["shayaris"]) - len(data.get("used_ids", []))
    print(f"  📜 Picked shayari #{shayari['id']} — theme: {shayari_theme}")
    print(f"  📊 Remaining unused: {remaining}/{len(data['shayaris'])}")
    for line in lines:
        print(f"     {line}")

    # Generate a short title using Gemini
    client = _get_client()
    title_prompt = (
        f"Write a very short catchy Hinglish title (max 5 words, in Roman script, NOT Devanagari) "
        f"for this shayari. Only output the title, nothing else:\n{full_text}"
    )

    try:
        title_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=title_prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 50,
                "thinking_config": {"thinking_budget": 0},
            },
        )
        title = (title_response.text or shayari_theme).strip().strip('"').strip("'")
    except Exception as e:
        print(f"  ⚠ Title generation failed ({e}), using theme as title.")
        title = shayari_theme.split("(")[0].strip().title()

    print(f"  ✅ Title: {title}")

    return {
        "lines": lines,
        "theme": shayari_theme,
        "title": title,
        "full": full_text,
    }


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    load_dotenv()
    result = generate_shayari()
    print(f"\nTitle: {result['title']}")
    print(f"Theme: {result['theme']}")
    print(f"\n{result['full']}")
