"""
Scheduler — runs the full shayari reel pipeline on a repeating schedule.

Multi-channel aware: each scheduled run processes ALL enabled channels
sequentially (generate → create → upload per channel).

Daily limit: uploads at most MAX_UPLOADS_PER_DAY reels per channel per day.
"""

import logging
import time
from datetime import datetime, date

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

import config
from channel_manager import Channel, get_enabled_channels, print_channel_summary
from shayari_generator import generate_shayari
from tts_generator import generate_voiceover
from video_creator import create_reel
from youtube_uploader import upload_video

# ── Logging setup ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("automation.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── Daily upload tracker ─────────────────────────────────────
# Tracks how many reels have been uploaded per channel today.
# Format: { "channel_id": { "date": "YYYY-MM-DD", "count": N } }
_daily_uploads: dict[str, dict] = {}


def _get_daily_count(channel_id: str) -> int:
    """Get how many reels have been uploaded today for a channel."""
    today = date.today().isoformat()
    entry = _daily_uploads.get(channel_id, {})
    if entry.get("date") != today:
        # New day — reset counter
        _daily_uploads[channel_id] = {"date": today, "count": 0}
        return 0
    return entry.get("count", 0)


def _increment_daily_count(channel_id: str) -> None:
    """Increment the daily upload count for a channel."""
    today = date.today().isoformat()
    if channel_id not in _daily_uploads or _daily_uploads[channel_id].get("date") != today:
        _daily_uploads[channel_id] = {"date": today, "count": 0}
    _daily_uploads[channel_id]["count"] += 1


def run_pipeline(upload: bool = True, channel: Channel | None = None) -> dict:
    """
    Execute the full pipeline once for a single channel.

    Parameters
    ----------
    upload : bool
        Whether to upload to YouTube.
    channel : Channel, optional
        The channel to process. If None, uses legacy single-channel mode.

    Returns a dict with run details.
    """
    channel_label = f"[{channel.name}]" if channel else "[default]"
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("=" * 60)
    logger.info(f"🚀 PIPELINE RUN STARTED — {channel_label} — {run_time}")
    logger.info("=" * 60)

    result = {"time": run_time, "status": "failed", "channel": channel_label}

    try:
        # ── Step 1: Generate Shayari ─────────────────────────
        logger.info(f"📝 Step 1/3: Generating shayari… {channel_label}")
        shayari = generate_shayari(channel=channel)
        logger.info(f"   Theme: {shayari['theme']}")
        logger.info(f"   Title: {shayari['title']}")
        for line in shayari["lines"]:
            logger.info(f"   → {line}")

        # ── Step 1.5: Generate Voiceover ───────────────────
        logger.info(f"🎙 Step 1.5/3: Generating voiceover... {channel_label}")
        voiceover_path = generate_voiceover(shayari["lines"])
        if voiceover_path:
            logger.info(f"   Voiceover: {voiceover_path}")
        else:
            logger.info("   Voiceover: skipped (TTS disabled or failed)")

        # ── Step 2: Create Video ─────────────────────────────
        watermark = channel.watermark if channel else config.WATERMARK_TEXT
        logger.info(f"🎬 Step 2/3: Creating reel video… {channel_label}")
        video_path = create_reel(
            shayari["lines"],
            voiceover_path=voiceover_path,
            watermark_text=watermark,
        )
        logger.info(f"   Video: {video_path}")

        # ── Step 3: Upload to YouTube ────────────────────────
        if upload:
            logger.info(f"📤 Step 3/3: Uploading to YouTube… {channel_label}")

            yt_title = f"{shayari['title']} | {watermark} #Shorts #Shayari"
            yt_description = (
                f"{shayari['full']}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 {watermark}\n"
                f"🎵 Theme: {shayari['theme']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"#Shorts #Shayari #HindiShayari #Poetry "
                f"#ShayariStatus #Motivation #Love #Reels"
            )

            # Per-channel upload params
            upload_kwargs = {
                "video_path": video_path,
                "title": yt_title,
                "description": yt_description,
            }

            if channel:
                upload_kwargs["tags"] = channel.tags
                upload_kwargs["category_id"] = channel.youtube_category_id
                upload_kwargs["client_secrets_path"] = channel.client_secrets_path
                upload_kwargs["token_path"] = channel.token_file_path

            video_id = upload_video(**upload_kwargs)

            if video_id:
                result["video_id"] = video_id
                result["url"] = f"https://youtube.com/shorts/{video_id}"
                logger.info(f"   ✅ Live at: {result['url']}")

                # Track the successful upload
                if channel:
                    _increment_daily_count(channel.id)
            else:
                logger.error(f"   ❌ Upload failed. {channel_label}")
                result["status"] = "upload_failed"
                return result
        else:
            logger.info(f"⏭  Step 3/3: Skipping upload (--generate-only mode) {channel_label}")

        result["status"] = "success"
        result["video_path"] = video_path
        result["shayari"] = shayari

        logger.info("=" * 60)
        logger.info(f"✅ PIPELINE COMPLETED SUCCESSFULLY {channel_label}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ PIPELINE FAILED {channel_label}: {e}", exc_info=True)
        result["error"] = str(e)

    return result


def run_all_channels(upload: bool = True) -> list[dict]:
    """
    Run the pipeline for ALL enabled channels.
    Respects the daily upload limit (MAX_UPLOADS_PER_DAY per channel).

    Returns a list of result dicts, one per channel.
    """
    channels = get_enabled_channels()
    max_per_day = config.MAX_UPLOADS_PER_DAY

    if not channels:
        logger.warning("⚠ No enabled channels found in channels.json!")
        return []

    logger.info("=" * 60)
    logger.info(f"🔄 MULTI-CHANNEL RUN — {len(channels)} channel(s)")
    logger.info(f"   Daily limit: {max_per_day} reels/channel/day")
    logger.info("=" * 60)

    results = []
    for i, channel in enumerate(channels, 1):
        logger.info(f"\n{'─'*40}")
        logger.info(f"📺 Channel {i}/{len(channels)}: {channel.name} ({channel.handle})")
        logger.info(f"{'─'*40}")

        # Check daily limit
        daily_count = _get_daily_count(channel.id)
        if daily_count >= max_per_day:
            logger.info(f"   ⏸ Daily limit reached ({daily_count}/{max_per_day}) — skipping until tomorrow")
            results.append({
                "channel": channel.name,
                "status": "daily_limit",
                "uploads_today": daily_count,
            })
            continue

        logger.info(f"   📊 Uploads today: {daily_count}/{max_per_day}")

        # Validate channel before running
        issues = channel.validate()
        if issues:
            for issue in issues:
                logger.error(f"   ⚠ {issue}")
            results.append({
                "channel": channel.name,
                "status": "config_error",
                "errors": issues,
            })
            continue

        try:
            result = run_pipeline(upload=upload, channel=channel)
            results.append(result)
        except Exception as e:
            logger.error(f"   ❌ Channel {channel.name} crashed: {e}", exc_info=True)
            results.append({
                "channel": channel.name,
                "status": "failed",
                "error": str(e),
            })

        # Delay between channels to avoid YouTube API rate limits
        if i < len(channels):
            delay = 60
            logger.info(f"   ⏳ Waiting {delay}s before next channel (rate limit protection)…")
            time.sleep(delay)

    # Summary
    success = sum(1 for r in results if r.get("status") == "success")
    skipped = sum(1 for r in results if r.get("status") == "daily_limit")
    failed = len(results) - success - skipped
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 MULTI-CHANNEL RUN COMPLETE: {success} ✅ / {skipped} ⏸ / {failed} ❌")
    logger.info(f"{'='*60}\n")

    return results


def start_scheduler():
    """Start the APScheduler to run the pipeline at fixed intervals for all channels."""
    channels = get_enabled_channels()

    logger.info("=" * 60)
    logger.info("🤖 SHAYARI REEL AUTOMATION STARTED (MULTI-CHANNEL)")
    logger.info(f"   Channels : {len(channels)} enabled")
    for ch in channels:
        logger.info(f"     → {ch.name} ({ch.handle})")
    logger.info(f"   Interval : every {config.SCHEDULE_INTERVAL_HOURS} hours")
    logger.info(f"   Daily max: {config.MAX_UPLOADS_PER_DAY} reels/channel/day")
    logger.info("=" * 60)

    # Run immediately on startup for all channels
    logger.info("▶ Running first pipeline for all channels…")
    run_all_channels(upload=True)

    # Schedule recurring runs
    scheduler = BlockingScheduler()
    scheduler.add_job(
        func=lambda: run_all_channels(upload=True),
        trigger=IntervalTrigger(hours=config.SCHEDULE_INTERVAL_HOURS),
        id="shayari_pipeline_multichannel",
        name="Shayari Reel Pipeline (Multi-Channel)",
        replace_existing=True,
    )

    logger.info(f"\n⏰ Next run in {config.SCHEDULE_INTERVAL_HOURS} hours. Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n🛑 Scheduler stopped by user.")
        scheduler.shutdown()


if __name__ == "__main__":
    start_scheduler()

