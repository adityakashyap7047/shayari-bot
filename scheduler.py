"""
Scheduler — runs the full shayari reel pipeline on a repeating schedule.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

import config
from shayari_generator import generate_shayari
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


def run_pipeline(upload: bool = True) -> dict:
    """
    Execute the full pipeline once:
      1. Generate shayari with AI
      2. Create the reel video
      3. Upload to YouTube

    Returns a dict with run details.
    """
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("=" * 60)
    logger.info(f"🚀 PIPELINE RUN STARTED — {run_time}")
    logger.info("=" * 60)

    result = {"time": run_time, "status": "failed"}

    try:
        # ── Step 1: Generate Shayari ─────────────────────────
        logger.info("📝 Step 1/3: Generating shayari…")
        shayari = generate_shayari()
        logger.info(f"   Theme: {shayari['theme']}")
        logger.info(f"   Title: {shayari['title']}")
        for line in shayari["lines"]:
            logger.info(f"   → {line}")

        # ── Step 2: Create Video ─────────────────────────────
        logger.info("🎬 Step 2/3: Creating reel video…")
        video_path = create_reel(shayari["lines"])
        logger.info(f"   Video: {video_path}")

        # ── Step 3: Upload to YouTube ────────────────────────
        if upload:
            logger.info("📤 Step 3/3: Uploading to YouTube…")

            yt_title = f"{shayari['title']} | {config.WATERMARK_TEXT} #Shorts #Shayari"
            yt_description = (
                f"{shayari['full']}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 {config.WATERMARK_TEXT}\n"
                f"🎵 Theme: {shayari['theme']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"#Shorts #Shayari #HindiShayari #Poetry "
                f"#ShayariStatus #Motivation #Love #Reels"
            )

            video_id = upload_video(
                video_path=video_path,
                title=yt_title,
                description=yt_description,
            )

            if video_id:
                result["video_id"] = video_id
                result["url"] = f"https://youtube.com/shorts/{video_id}"
                logger.info(f"   ✅ Live at: {result['url']}")
            else:
                logger.error("   ❌ Upload failed.")
                result["status"] = "upload_failed"
                return result
        else:
            logger.info("⏭  Step 3/3: Skipping upload (--generate-only mode)")

        result["status"] = "success"
        result["video_path"] = video_path
        result["shayari"] = shayari

        logger.info("=" * 60)
        logger.info(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ PIPELINE FAILED: {e}", exc_info=True)
        result["error"] = str(e)

    return result


def start_scheduler():
    """Start the APScheduler to run the pipeline at fixed intervals."""
    logger.info("=" * 60)
    logger.info("🤖 SHAYARI REEL AUTOMATION STARTED")
    logger.info(f"   Interval: every {config.SCHEDULE_INTERVAL_HOURS} hours")
    logger.info(f"   Watermark: {config.WATERMARK_TEXT}")
    logger.info("=" * 60)

    # Run immediately on startup
    logger.info("▶ Running first pipeline immediately…")
    run_pipeline(upload=True)

    # Schedule recurring runs
    scheduler = BlockingScheduler()
    scheduler.add_job(
        func=lambda: run_pipeline(upload=True),
        trigger=IntervalTrigger(hours=config.SCHEDULE_INTERVAL_HOURS),
        id="shayari_pipeline",
        name="Shayari Reel Pipeline",
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
