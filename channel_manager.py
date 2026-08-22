"""
Channel Manager — loads and manages multi-channel configuration.

Each channel has its own:
  - YouTube OAuth credentials (client_secrets.json + token.json)
  - Shayari collection (shayari_collection.json)
  - Watermark text, tags, themes, and category ID

Channels are defined in channels.json at the project root.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field

import config


@dataclass
class Channel:
    """Represents a single YouTube channel configuration."""
    id: str
    name: str
    handle: str
    enabled: bool
    watermark: str
    themes: list[str]
    tags: list[str]
    youtube_category_id: str
    client_secrets: str      # relative path from BASE_DIR
    token_file: str          # relative path from BASE_DIR
    shayari_collection: str  # relative path from BASE_DIR

    @property
    def client_secrets_path(self) -> str:
        """Absolute path to the channel's client_secrets.json."""
        return os.path.join(config.BASE_DIR, self.client_secrets)

    @property
    def token_file_path(self) -> str:
        """Absolute path to the channel's token.json."""
        return os.path.join(config.BASE_DIR, self.token_file)

    @property
    def shayari_collection_path(self) -> str:
        """Absolute path to the channel's shayari_collection.json."""
        return os.path.join(config.BASE_DIR, self.shayari_collection)

    @property
    def channel_dir(self) -> str:
        """Absolute path to the channel's directory."""
        return os.path.join(config.CHANNELS_DIR, self.id)

    def validate(self) -> list[str]:
        """Check if the channel is properly configured. Returns a list of issues."""
        issues = []
        if not os.path.exists(self.client_secrets_path):
            issues.append(f"client_secrets not found: {self.client_secrets_path}")
        if not os.path.exists(self.shayari_collection_path):
            issues.append(f"shayari_collection not found: {self.shayari_collection_path}")
        return issues


def load_channels() -> list[Channel]:
    """
    Load all channels from channels.json.

    Returns
    -------
    list[Channel] : All channel configurations (including disabled ones).
    """
    channels_file = config.CHANNELS_FILE
    if not os.path.exists(channels_file):
        raise FileNotFoundError(
            f"channels.json not found: {channels_file}\n"
            "Create it with your channel configurations. See README for format."
        )

    with open(channels_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    channels = []
    for ch in data.get("channels", []):
        channels.append(Channel(
            id=ch["id"],
            name=ch["name"],
            handle=ch.get("handle", ""),
            enabled=ch.get("enabled", True),
            watermark=ch.get("watermark", ch.get("handle", "")),
            themes=ch.get("themes", []),
            tags=ch.get("tags", config.YOUTUBE_DEFAULT_TAGS),
            youtube_category_id=ch.get("youtube_category_id", config.YOUTUBE_CATEGORY_ID),
            client_secrets=ch["client_secrets"],
            token_file=ch["token_file"],
            shayari_collection=ch["shayari_collection"],
        ))

    return channels


def get_enabled_channels() -> list[Channel]:
    """Load and return only the enabled channels."""
    return [ch for ch in load_channels() if ch.enabled]


def get_channel_by_id(channel_id: str) -> Channel | None:
    """Find a specific channel by its ID."""
    for ch in load_channels():
        if ch.id == channel_id:
            return ch
    return None


def migrate_single_channel_setup() -> None:
    """
    Migrate the legacy single-channel setup to the multi-channel structure.

    This copies existing root-level files into channels/shayari_official/
    without deleting the originals.
    """
    channel_dir = os.path.join(config.CHANNELS_DIR, "shayari_official")
    os.makedirs(channel_dir, exist_ok=True)

    # Files to migrate: (source, destination)
    migrations = [
        (os.path.join(config.BASE_DIR, "client_secrets.json"),
         os.path.join(channel_dir, "client_secrets.json")),
        (os.path.join(config.BASE_DIR, "token.json"),
         os.path.join(channel_dir, "token.json")),
        (os.path.join(config.BASE_DIR, "shayari_collection.json"),
         os.path.join(channel_dir, "shayari_collection.json")),
    ]

    migrated = []
    for src, dst in migrations:
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            migrated.append(os.path.basename(src))
            print(f"  ✅ Migrated: {os.path.basename(src)} → {dst}")
        elif os.path.exists(dst):
            print(f"  ⏭ Already exists: {dst}")
        else:
            print(f"  ⚠ Source not found: {src}")

    if migrated:
        print(f"\n  📁 Migration complete! {len(migrated)} file(s) copied to {channel_dir}")
        print("  💡 Original files are still in place — you can remove them later.")
    else:
        print("\n  ℹ Nothing to migrate — all files already in place.")


def print_channel_summary(channels: list[Channel] | None = None) -> None:
    """Print a formatted summary of all channels."""
    if channels is None:
        channels = load_channels()

    print(f"\n{'='*60}")
    print(f"  📺 CONFIGURED CHANNELS ({len(channels)} total)")
    print(f"{'='*60}")

    for ch in channels:
        status = "✅ Enabled" if ch.enabled else "❌ Disabled"
        issues = ch.validate()
        if issues:
            status = "⚠ Issues found"

        print(f"\n  [{ch.id}]")
        print(f"    Name      : {ch.name}")
        print(f"    Handle    : {ch.handle}")
        print(f"    Status    : {status}")
        print(f"    Watermark : {ch.watermark}")
        print(f"    Themes    : {', '.join(ch.themes) if ch.themes else 'all (no filter)'}")
        print(f"    Tags      : {len(ch.tags)} tags")
        print(f"    Secrets   : {ch.client_secrets}")
        print(f"    Collection: {ch.shayari_collection}")

        if issues:
            for issue in issues:
                print(f"    ⚠ {issue}")

    print(f"\n{'='*60}\n")


# ── Quick test / Migration helper ────────────────────────────
if __name__ == "__main__":
    import sys

    if "--migrate" in sys.argv:
        print("\n🔄 Migrating single-channel setup to multi-channel...\n")
        migrate_single_channel_setup()
    else:
        print_channel_summary()
