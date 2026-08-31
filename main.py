"""
YouTube Shayari Reel Automation (Multi-Channel)
================================================
Main entry point for the automation system.

Usage:
    python main.py                        Start the automated scheduler (all channels)
    python main.py --once                 Generate and upload one reel per channel
    python main.py --once --channel ID    Generate and upload for a specific channel only
    python main.py --generate-only        Generate videos without uploading
    python main.py --test-auth            Test YouTube authentication for all channels
    python main.py --list-channels        List all configured channels
    python main.py --migrate              Migrate single-channel setup to multi-channel
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
  python main.py                             Start the automated scheduler (all channels)
  python main.py --once                      Generate & upload one reel per channel
  python main.py --once --channel my_channel Generate & upload for a specific channel
  python main.py --generate-only             Generate videos only (no upload)
  python main.py --test-auth                 Test YouTube authentication
  python main.py --list-channels             List all configured channels
  python main.py --migrate                   Migrate single-channel to multi-channel
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
        help="Test YouTube authentication for all (or specified) channels.",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default=None,
        help="Specify a shayari theme (e.g., 'love', 'life').",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default=None,
        help="Target a specific channel by its ID (used with --once or --generate-only).",
    )
    parser.add_argument(
        "--list-channels",
        action="store_true",
        help="List all configured channels and their status.",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate the single-channel setup to multi-channel directory structure.",
    )

    args = parser.parse_args()

    # -- List Channels --
    if args.list_channels:
        from channel_manager import print_channel_summary
        print_channel_summary()
        return

    # -- Migrate --
    if args.migrate:
        from channel_manager import migrate_single_channel_setup
        print("\n🔄 Migrating single-channel setup to multi-channel...\n")
        migrate_single_channel_setup()
        return

    # -- Test Auth Mode --
    if args.test_auth:
        from channel_manager import get_enabled_channels, get_channel_by_id
        from youtube_uploader import _authenticate

        if args.channel:
            channel = get_channel_by_id(args.channel)
            if not channel:
                print(f"\n❌ Channel '{args.channel}' not found in channels.json\n")
                sys.exit(1)
            channels = [channel]
        else:
            channels = get_enabled_channels()

        print(f"\n[AUTH] Testing YouTube authentication for {len(channels)} channel(s)...\n")
        for ch in channels:
            print(f"  📺 {ch.name} ({ch.handle})")
            try:
                _authenticate(
                    client_secrets_path=ch.client_secrets_path,
                    token_path=ch.token_file_path,
                )
                print(f"  ✅ Auth OK!\n")
            except Exception as e:
                print(f"  ❌ Auth failed: {e}\n")
        return

    # -- Generate-Only Mode --
    if args.generate_only:
        from channel_manager import get_enabled_channels, get_channel_by_id
        from shayari_generator import generate_shayari
        from tts_generator import generate_voiceover
        from video_creator import create_reel

        if args.channel:
            channel = get_channel_by_id(args.channel)
            if not channel:
                print(f"\n❌ Channel '{args.channel}' not found in channels.json\n")
                sys.exit(1)
            channels = [channel]
        else:
            channels = get_enabled_channels()

        print(f"\n[MODE] Generate-Only — {len(channels)} channel(s)\n")

        for ch in channels:
            print(f"\n{'─'*50}")
            print(f"  📺 {ch.name} ({ch.handle})")
            print(f"{'─'*50}")

            shayari = generate_shayari(theme=args.theme, channel=ch)
            voiceover_path = generate_voiceover(shayari["lines"])
            video_path = create_reel(
                shayari["lines"],
                voiceover_path=voiceover_path,
                watermark_text=ch.watermark,
            )

            print(f"\n{'='*50}")
            print(f"[OK] Video generated for {ch.name}!")
            print(f"  File : {video_path}")
            print(f"  Title: {shayari['title']}")
            print(f"  Theme: {shayari['theme']}")
            if voiceover_path:
                print(f"  Voice: {voiceover_path}")
            print(f"{'='*50}\n")
        return

    # -- One-Shot Mode --
    if args.once:
        from channel_manager import get_enabled_channels, get_channel_by_id
        from scheduler import run_pipeline, run_all_channels

        if args.channel:
            channel = get_channel_by_id(args.channel)
            if not channel:
                print(f"\n❌ Channel '{args.channel}' not found in channels.json\n")
                sys.exit(1)

            print(f"\n[MODE] One-Shot: {channel.name} ({channel.handle})\n")
            result = run_pipeline(upload=True, channel=channel)

            if result["status"] == "success":
                print(f"\n[OK] Done! Video: {result.get('url', 'N/A')}\n")
            else:
                print(f"\n[FAIL] {result.get('error', 'Unknown error')}\n")
                sys.exit(1)
        else:
            print(f"\n[MODE] One-Shot: All Enabled Channels\n")
            results = run_all_channels(upload=True)

            success = sum(1 for r in results if r.get("status") == "success")
            skipped = sum(1 for r in results if r.get("status") == "daily_limit")
            failed = len(results) - success - skipped
            print(f"\n[DONE] {success} succeeded, {skipped} skipped, {failed} failed\n")
            if success == 0 and failed > 0:
                # Only exit with error if ALL channels failed (no uploads at all)
                sys.exit(1)
        return

    # -- Scheduler Mode (default) --
    from channel_manager import get_enabled_channels
    import config

    channels = get_enabled_channels()
    channel_list = "\n".join(
        f"    |     {i}. {ch.name} ({ch.handle})"
        for i, ch in enumerate(channels, 1)
    )

    print(f"""
    +===================================================+
    |                                                   |
    |   Shayari Reel Automation (Multi-Channel)         |
    |   ──────────────────────────────────────          |
    |   Channels : {len(channels)} enabled                           |
{channel_list}
    |                                                   |
    |   Schedule : Every {config.SCHEDULE_INTERVAL_HOURS} hours                       |
    |   Daily max: {config.MAX_UPLOADS_PER_DAY} reels/channel/day                  |
    |   Engine   : AI-powered Hindi shayari             |
    |                                                   |
    |   Press Ctrl+C to stop                            |
    |                                                   |
    +===================================================+
    """)

    from scheduler import start_scheduler
    start_scheduler()


if __name__ == "__main__":
    main()
