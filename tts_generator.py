"""
TTS Generator — generates voiceover audio for shayari reels.

Primary: ElevenLabs API (high-quality, paid plan required for library voices)
Fallback: Google TTS (gTTS) — free, unlimited, decent Hindi quality
"""

from __future__ import annotations

import os
from datetime import datetime

import config


def _generate_with_elevenlabs(text: str, output_path: str) -> bool:
    """
    Try generating voiceover with ElevenLabs.
    Returns True on success, False on failure.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key or api_key == "your_elevenlabs_api_key_here":
        print("  ⚠ ELEVENLABS_API_KEY not set — trying gTTS fallback...")
        return False

    try:
        from elevenlabs.client import ElevenLabs

        print(f"  🎙 Trying ElevenLabs TTS...")
        print(f"     Voice ID: {config.ELEVENLABS_VOICE_ID}")
        print(f"     Model: {config.ELEVENLABS_MODEL_ID}")

        client = ElevenLabs(api_key=api_key)

        audio_iterator = client.text_to_speech.convert(
            text=text,
            voice_id=config.ELEVENLABS_VOICE_ID,
            model_id=config.ELEVENLABS_MODEL_ID,
            output_format="mp3_44100_128",
        )

        with open(output_path, "wb") as f:
            for chunk in audio_iterator:
                f.write(chunk)

        file_size = os.path.getsize(output_path)
        print(f"  ✅ ElevenLabs voiceover saved ({file_size / 1024:.1f} KB)")
        return True

    except Exception as e:
        print(f"  ⚠ ElevenLabs failed: {e}")
        # Clean up partial file
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


def _generate_with_gtts(text: str, output_path: str) -> bool:
    """
    Fallback: generate voiceover with Google TTS (free).
    Returns True on success, False on failure.
    """
    try:
        from gtts import gTTS

        print(f"  🔄 Using gTTS fallback (free, Hindi)...")

        tts = gTTS(text=text, lang="hi", slow=False)
        tts.save(output_path)

        file_size = os.path.getsize(output_path)
        print(f"  ✅ gTTS voiceover saved ({file_size / 1024:.1f} KB)")
        return True

    except Exception as e:
        print(f"  ❌ gTTS also failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


def generate_voiceover(shayari_lines: list[str], output_filename: str | None = None) -> str | None:
    """
    Generate a voiceover audio file from shayari lines.

    Tries ElevenLabs first, falls back to gTTS if it fails.

    Parameters
    ----------
    shayari_lines : list[str]
        The lines of shayari to convert to speech.
    output_filename : str, optional
        Custom filename for the audio. If None, auto-generates with timestamp.

    Returns
    -------
    str or None
        Path to the generated .mp3 file, or None if TTS is disabled or all engines fail.
    """
    if not config.TTS_ENABLED:
        print("  ⏭ TTS is disabled (TTS_ENABLED=False)")
        return None

    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"voiceover_{timestamp}.mp3"

    output_path = os.path.join(config.OUTPUT_DIR, output_filename)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # Join lines with pauses
    full_text = " ... ".join(shayari_lines)
    print(f"  🎙 Generating voiceover ({len(full_text)} chars)...")

    # Try ElevenLabs first
    if _generate_with_elevenlabs(full_text, output_path):
        return output_path

    # Fallback to gTTS
    print("  🔄 Falling back to gTTS...")
    if _generate_with_gtts(full_text, output_path):
        return output_path

    # Both failed
    print("  ❌ All TTS engines failed — continuing without voiceover.")
    return None


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    test_lines = [
        "दिल के टुकड़े हज़ार हुए",
        "कोई यहाँ गिरा कोई वहाँ गिरा",
        "जिसको हमने अपना समझा",
        "वो भी ग़ैरों में जा मिला",
    ]
    result = generate_voiceover(test_lines)
    if result:
        print(f"\nTest voiceover created: {result}")
    else:
        print("\nVoiceover generation skipped or failed.")
