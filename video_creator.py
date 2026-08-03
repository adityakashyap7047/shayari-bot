"""
Video Creator — generates a shayari reel video with MoviePy.

Format:
  * 1080x1920 (9:16 vertical - YouTube Shorts)
  * Black background
  * Shayari lines pop up one by one with fade-in
  * Watermark @shyariofficial-k2q at the bottom
  * Background music from bg_music/ folder
"""

from __future__ import annotations

import os
import glob
import random
from datetime import datetime

from moviepy import (
    ColorClip,
    TextClip,
    CompositeVideoClip,
    AudioFileClip,
    concatenate_audioclips,
)
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
from moviepy.video.fx import FadeIn, FadeOut

import config


def _pick_bg_music() -> str | None:
    """Randomly pick a music file from the bg_music/ folder."""
    patterns = ["*.mp3", "*.wav", "*.ogg", "*.m4a"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(config.BG_MUSIC_DIR, pattern)))

    if not files:
        print("  ⚠ No background music found in bg_music/ — video will be silent.")
        return None

    chosen = random.choice(files)
    print(f"  🎵 Using music: {os.path.basename(chosen)}")
    return chosen


def _get_font(font_path: str, fallback: str = "Arial") -> str:
    """Return the font path if it exists, otherwise fall back."""
    if os.path.exists(font_path):
        return font_path
    print(f"  ⚠ Font not found: {font_path} — falling back to {fallback}")
    return fallback


def create_reel(shayari_lines: list[str], output_filename: str | None = None) -> str:
    """
    Create a shayari reel video.

    Parameters
    ----------
    shayari_lines : list[str]
        The lines of shayari to display (typically 4 lines).
    output_filename : str, optional
        Custom filename. If None, auto-generates with timestamp.

    Returns
    -------
    str : path to the generated .mp4 file
    """
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"shayari_reel_{timestamp}.mp4"

    output_path = os.path.join(config.OUTPUT_DIR, output_filename)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    num_lines = len(shayari_lines)
    total_duration = config.LINE_DISPLAY_TIME * num_lines + 4  # +4s for intro/outro padding
    total_duration = min(total_duration, 58)  # keep under 60s for Shorts

    print(f"  🎬 Creating video: {total_duration}s, {config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}")

    # ── 1. Black background ──────────────────────────────────
    bg_clip = ColorClip(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=config.BG_COLOR,
    ).with_duration(total_duration)

    # ── 2. Shayari text lines (pop up one by one) ────────────
    font = _get_font(config.SHAYARI_FONT)
    text_clips = []

    for i, line in enumerate(shayari_lines):
        start_time = 1.5 + (i * config.LINE_DISPLAY_TIME)  # 1.5s initial pause

        txt = TextClip(
            text=line,
            font=font,
            font_size=config.SHAYARI_FONT_SIZE,
            color=config.TEXT_COLOR,
            text_align="center",
            size=(config.VIDEO_WIDTH - 120, None),  # wrap within margins
            method="caption",
        )

        # Position: stack lines vertically centered
        # Calculate Y position — center the block of text
        block_height = num_lines * 120  # approximate height per line
        y_start = (config.VIDEO_HEIGHT - block_height) // 2
        y_pos = y_start + (i * 120)

        txt = txt.with_position(("center", y_pos))
        txt = txt.with_start(start_time)
        txt = txt.with_duration(total_duration - start_time)

        # Fade-in effect for each line
        txt = txt.with_effects([FadeIn(config.FADE_DURATION)])

        text_clips.append(txt)

    # ── 3. Watermark ─────────────────────────────────────────
    watermark_font = _get_font(config.WATERMARK_FONT, fallback="Arial")
    watermark = TextClip(
        text=config.WATERMARK_TEXT,
        font=watermark_font,
        font_size=config.WATERMARK_FONT_SIZE,
        color="#888888",
        text_align="center",
        size=(config.VIDEO_WIDTH - 120, None),
        method="caption",
    )
    watermark = watermark.with_position(("center", config.VIDEO_HEIGHT - 120))
    watermark = watermark.with_duration(total_duration)
    watermark = watermark.with_effects([FadeIn(2.0)])

    # ── 4. Compose video ─────────────────────────────────────
    video = CompositeVideoClip(
        [bg_clip] + text_clips + [watermark],
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
    )

    # ── 5. Background music ──────────────────────────────────
    music_path = _pick_bg_music()
    if music_path:
        audio = AudioFileClip(music_path)

        # Loop audio if shorter than video
        if audio.duration < total_duration:
            loops_needed = int(total_duration / audio.duration) + 1
            audio = concatenate_audioclips([audio] * loops_needed)

        audio = audio.subclipped(0, total_duration)

        # Apply fade in/out
        audio = audio.with_effects([
            AudioFadeIn(config.MUSIC_FADE_IN),
            AudioFadeOut(config.MUSIC_FADE_OUT),
        ])

        video = video.with_audio(audio)

    # ── 6. Render ────────────────────────────────────────────
    print(f"  ⏳ Rendering video to: {output_path}")
    video.write_videofile(
        output_path,
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger="bar",
    )

    # Clean up
    video.close()
    if music_path:
        audio.close()

    print(f"  ✅ Video saved: {output_path}")
    return output_path


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_lines = [
        "दिल के टुकड़े हज़ार हुए",
        "कोई यहाँ गिरा कोई वहाँ गिरा",
        "जिसको हमने अपना समझा",
        "वो भी ग़ैरों में जा मिला",
    ]
    path = create_reel(test_lines)
    print(f"\nTest video created: {path}")
