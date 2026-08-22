"""
Video Creator — generates a shayari reel video with MoviePy.

Format:
  * 1080x1920 (9:16 vertical - YouTube Shorts)
  * Background image from backgrounds/ folder (or black fallback)
  * Shayari text displayed statically (all lines visible from start)
  * Watermark @shyariofficial-k2q at the bottom
  * ElevenLabs voiceover (primary audio) + background music (low volume)
"""

from __future__ import annotations

import os
import glob
import random
from datetime import datetime

from moviepy import (
    ColorClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    CompositeAudioClip,
    AudioFileClip,
    concatenate_audioclips,
)
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

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


def _pick_bg_image() -> str | None:
    """Randomly pick a background image from the backgrounds/ folder."""
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(config.BG_IMAGES_DIR, pattern)))

    if not files:
        print("  ⚠ No background images found — using black background.")
        return None

    chosen = random.choice(files)
    print(f"  🖼 Using background: {os.path.basename(chosen)}")
    return chosen


def _get_font(font_path: str, fallback: str = "Arial") -> str:
    """Return the font path if it exists, otherwise fall back."""
    if os.path.exists(font_path):
        return font_path
    print(f"  ⚠ Font not found: {font_path} — falling back to {fallback}")
    return fallback


def create_reel(
    shayari_lines: list[str],
    voiceover_path: str | None = None,
    output_filename: str | None = None,
    watermark_text: str | None = None,
) -> str:
    """
    Create a shayari reel video.

    Parameters
    ----------
    shayari_lines : list[str]
        The lines of shayari to display (typically 4 lines).
    voiceover_path : str, optional
        Path to the TTS voiceover audio file. If provided, video duration
        matches the voiceover and bg music volume is reduced.
    output_filename : str, optional
        Custom filename. If None, auto-generates with timestamp.
    watermark_text : str, optional
        Channel watermark text. Defaults to config.WATERMARK_TEXT.

    Returns
    -------
    str : path to the generated .mp4 file
    """
    if watermark_text is None:
        watermark_text = config.WATERMARK_TEXT
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"shayari_reel_{timestamp}.mp4"

    output_path = os.path.join(config.OUTPUT_DIR, output_filename)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # Determine video duration — voiceover drives it when available
    voiceover_clip = None
    if voiceover_path and os.path.exists(voiceover_path):
        voiceover_clip = AudioFileClip(voiceover_path)
        # Add 3s padding (1.5s before + 1.5s after voiceover)
        total_duration = voiceover_clip.duration + 3.0
        print(f"  🎙 Voiceover duration: {voiceover_clip.duration:.1f}s")
    else:
        num_lines = len(shayari_lines)
        total_duration = config.LINE_DISPLAY_TIME * num_lines + 4

    total_duration = min(total_duration, 58)  # keep under 60s for Shorts

    print(f"  🎬 Creating video: {total_duration:.1f}s, {config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}")

    num_lines = len(shayari_lines)

    # ── 1. Background (image or solid black fallback) ─────────
    bg_image_path = _pick_bg_image()
    if bg_image_path:
        bg_clip = (
            ImageClip(bg_image_path)
            .resized((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
            .with_duration(total_duration)
        )
        # Semi-transparent dark overlay so white text stays readable
        overlay = (
            ColorClip(
                size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                color=(0, 0, 0),
            )
            .with_duration(total_duration)
            .with_opacity(config.BG_OVERLAY_OPACITY)
        )
        bg_layers = [bg_clip, overlay]
    else:
        bg_clip = ColorClip(
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
            color=config.BG_COLOR,
        ).with_duration(total_duration)
        bg_layers = [bg_clip]

    # ── 2. Shayari text lines (static — all visible from start) ─
    font = _get_font(config.SHAYARI_FONT)
    text_clips = []

    # Calculate line spacing based on number of lines
    line_spacing = 130  # pixels between each line
    block_height = (num_lines - 1) * line_spacing
    # Position text in the upper portion of the frame (above character/image)
    # This keeps text in the black/empty area at the top
    y_top_area = int(config.VIDEO_HEIGHT * 0.12)  # start at ~12% from top
    y_start = y_top_area

    for i, line in enumerate(shayari_lines):
        txt = TextClip(
            text=line,
            font=font,
            font_size=config.SHAYARI_FONT_SIZE,
            color=config.TEXT_COLOR,
            text_align="center",
            size=(config.VIDEO_WIDTH - 160, None),  # wider margins to prevent wrapping
            method="caption",
        )

        y_pos = y_start + (i * line_spacing)

        txt = txt.with_position(("center", y_pos))
        txt = txt.with_duration(total_duration)

        text_clips.append(txt)

    # ── 3. Watermark ─────────────────────────────────────────
    watermark_font = _get_font(config.WATERMARK_FONT, fallback="Arial")
    watermark = TextClip(
        text=watermark_text,
        font=watermark_font,
        font_size=config.WATERMARK_FONT_SIZE,
        color="#888888",
        text_align="center",
        size=(config.VIDEO_WIDTH - 120, None),
        method="caption",
    )
    watermark = watermark.with_position(("center", config.VIDEO_HEIGHT - 120))
    watermark = watermark.with_duration(total_duration)

    # ── 4. Compose video ─────────────────────────────────────
    video = CompositeVideoClip(
        bg_layers + text_clips + [watermark],
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
    )

    # ── 5. Audio: voiceover + background music ────────────────
    audio_layers = []
    music_clip = None

    # Voiceover (primary audio)
    if voiceover_clip:
        # Start voiceover 1.5s into the video for a natural feel
        vo = voiceover_clip.with_start(1.5)
        if config.VOICEOVER_VOLUME != 1.0:
            vo = vo.with_volume_scaled(config.VOICEOVER_VOLUME)
        audio_layers.append(vo)

    # Background music
    music_path = _pick_bg_music()
    if music_path:
        music_clip = AudioFileClip(music_path)

        # Loop music if shorter than video
        if music_clip.duration < total_duration:
            loops_needed = int(total_duration / music_clip.duration) + 1
            music_clip = concatenate_audioclips([music_clip] * loops_needed)

        music_clip = music_clip.subclipped(0, total_duration)

        # Apply fade in/out
        music_clip = music_clip.with_effects([
            AudioFadeIn(config.MUSIC_FADE_IN),
            AudioFadeOut(config.MUSIC_FADE_OUT),
        ])

        # Lower bg music volume when voiceover is present
        if voiceover_clip:
            music_clip = music_clip.with_volume_scaled(config.BG_MUSIC_VOLUME_WITH_VO)

        audio_layers.append(music_clip)

    # Mix all audio layers
    if audio_layers:
        if len(audio_layers) == 1:
            final_audio = audio_layers[0]
        else:
            final_audio = CompositeAudioClip(audio_layers)
        video = video.with_audio(final_audio)

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
    if voiceover_clip:
        voiceover_clip.close()
    if music_clip:
        music_clip.close()

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
