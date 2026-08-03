"""
Shayari Generator — picks from a curated collection of shayaris.
Uses Gemini AI only for generating YouTube titles.
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

# Path to the shayari collection file
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


def _load_collection() -> dict:
    """Load the shayari collection from JSON file."""
    if not os.path.exists(COLLECTION_FILE):
        raise FileNotFoundError(
            f"Shayari collection not found: {COLLECTION_FILE}\n"
            "Please create shayari_collection.json with your shayaris."
        )
    with open(COLLECTION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_collection(data: dict) -> None:
    """Save updated collection (with used_ids tracking)."""
    with open(COLLECTION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _pick_shayari(data: dict) -> dict | None:
    """Pick a random unused shayari from the collection.
    
    If all have been used, reset the used list and start over.
    """
    all_ids = [s["id"] for s in data["shayaris"]]
    used_ids = set(data.get("used_ids", []))

    available_ids = [sid for sid in all_ids if sid not in used_ids]

    # All used up — reset and start fresh
    if not available_ids:
        print("  🔄 All 20 shayaris used! Resetting collection…")
        data["used_ids"] = []
        available_ids = all_ids

    chosen_id = random.choice(available_ids)

    # Mark as used
    data["used_ids"].append(chosen_id)
    _save_collection(data)

    # Find and return the shayari
    for s in data["shayaris"]:
        if s["id"] == chosen_id:
            return s
    return None


def generate_shayari(theme: str | None = None, max_retries: int = 3) -> dict:
    """
    Pick a shayari from the curated collection and generate a title.

    Returns
    -------
    dict with keys:
        - "lines"  : list[str]  — the lines of shayari
        - "theme"  : str        — the theme
        - "title"  : str        — a short YouTube-friendly title
        - "full"   : str        — the full shayari as one string
    """
    # Load collection and pick a random unused shayari
    data = _load_collection()
    shayari = _pick_shayari(data)

    if shayari is None:
        raise RuntimeError("Could not pick a shayari from the collection.")

    lines = shayari["lines"]
    shayari_theme = shayari.get("theme", theme or "zindagi")
    full_text = "\n".join(lines)

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
