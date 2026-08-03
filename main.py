"""
YouTube Shayari Reel Automation
===================================
Main entry point for the automation system.

Usage:
    python main.py                  Start the automated scheduler (every 3 hours)
    python main.py --once           Generate and upload one reel immediately
    python main.py --generate-only  Generate video without uploading (testing)
    python main.py --test-auth      Test YouTube authentication only
"""

import argparse
import os
import sys

from dotenv import load_dotenv

# Force UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load environment variables before anything else
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shayari Reel Automation - AI-generated shayari reels uploaded automatically.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                   Start the automated scheduler
  python main.py --once            Generate & upload one reel now
  python main.py --generate-only   Generate video only (no upload)
  python main.py --test-auth       Test YouTube authentication
        """,
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the pipeline once and exit (generate + upload).",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate a reel video without uploading to YouTube.",
    )
    parser.add_argument(
        "--test-auth",
        action="store_true",
        help="Test YouTube authentication only.",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default=None,
        help="Specify a shayari theme (e.g., 'love', 'life').",
    )

    args = parser.parse_args()

    # -- Test Auth Mode --
    if args.test_auth:
        print("\n[AUTH] Testing YouTube authentication...\n")
        from youtube_uploader import _authenticate
        _authenticate()
        print("\n[OK] Authentication works! You're ready to go.\n")
        return

    # -- Generate-Only Mode --
    if args.generate_only:
        print("\n[MODE] Generate-Only (no upload)\n")
        from shayari_generator import generate_shayari
        from video_creator import create_reel

        shayari = generate_shayari(theme=args.theme)
        video_path = create_reel(shayari["lines"])

        print(f"\n{'='*50}")
        print(f"[OK] Video generated successfully!")
        print(f"  File : {video_path}")
        print(f"  Title: {shayari['title']}")
        print(f"  Theme: {shayari['theme']}")
        print(f"{'='*50}\n")
        return

    # -- One-Shot Mode --
    if args.once:
        print("\n[MODE] One-Shot: Generate + Upload\n")
        from scheduler import run_pipeline
        result = run_pipeline(upload=True)

        if result["status"] == "success":
            print(f"\n[OK] Done! Video: {result.get('url', 'N/A')}\n")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}\n")
            sys.exit(1)
        return

    # -- Scheduler Mode (default) --
    print("""
    +===================================================+
    |                                                   |
    |   Shayari Reel Automation                         |
    |   ------------------------                        |
    |   Channel: @shyariofficial-k2q                    |
    |   Schedule: Uploading every 3 hours               |
    |   Engine: AI-powered Hindi shayari                |
    |                                                   |
    |   Press Ctrl+C to stop                            |
    |                                                   |
    +===================================================+
    """)

    from scheduler import start_scheduler
    start_scheduler()


if __name__ == "__main__":
    main()
