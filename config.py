import os

# ============================================================
#  DIRECTORIES
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_MUSIC_DIR = os.path.join(BASE_DIR, "bg_music")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

# Create directories if they don't exist
for d in [BG_MUSIC_DIR, OUTPUT_DIR, FONTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
#  VIDEO SETTINGS  (YouTube Shorts = 9:16 vertical, ≤60s)
# ============================================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_DURATION = 25          # seconds per reel
FADE_DURATION = 0.8          # seconds for text fade-in
LINE_DISPLAY_TIME = 4.0      # seconds each shayari line stays visible
MUSIC_FADE_IN = 1.5          # seconds
MUSIC_FADE_OUT = 2.0         # seconds

# ============================================================
#  TEXT & WATERMARK
# ============================================================
WATERMARK_TEXT = "@shyariofficial-k2q"
SHAYARI_FONT_SIZE = 62       # main shayari text
WATERMARK_FONT_SIZE = 32
TEXT_COLOR = "white"
BG_COLOR = (0, 0, 0)         # pure black

# Font — Hinglish uses Roman script so any standard font works.
# You can place a custom .ttf in fonts/ and update the path below.
# Default: uses system Arial font (available on all Windows PCs)
SHAYARI_FONT = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arialbd.ttf")
WATERMARK_FONT = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arial.ttf")

# ============================================================
#  SHAYARI GENERATION
# ============================================================
SHAYARI_THEMES = [
    "pyaar (love)",
    "zindagi (life)",
    "motivation",
    "udaasi (sadness)",
    "dosti (friendship)",
    "nature",
    "tanhaai (loneliness)",
    "khwaab (dreams)",
    "waqt (time)",
    "intezaar (waiting)",
]

SHAYARI_HISTORY_FILE = os.path.join(BASE_DIR, "shayari_history.json")

# ============================================================
#  YOUTUBE UPLOAD
# ============================================================
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
YOUTUBE_CATEGORY_ID = "24"   # Entertainment

YOUTUBE_DEFAULT_TAGS = [
    "shayari", "hindi shayari", "shayari status",
    "hindi poetry", "urdu shayari", "love shayari",
    "motivation", "quotes", "reels", "shorts",
    "shayari reels", "whatsapp status",
]

# ============================================================
#  SCHEDULER
# ============================================================
SCHEDULE_INTERVAL_HOURS = 3   # upload every N hours
