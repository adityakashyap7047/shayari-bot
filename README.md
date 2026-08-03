# YouTube Shayari Reel Automation

Fully automated pipeline that generates Hinglish shayari reels using AI, creates videos with animated text on a black background with background music, and uploads them to YouTube as Shorts every 3 hours.

## Features

- **AI-Powered Shayari** - Gemini AI generates unique Hinglish shayari every time
- **Auto Video Creation** - Black background, animated text pop-up, background music
- **Auto YouTube Upload** - Uploads as YouTube Shorts with optimized metadata
- **Scheduled Automation** - Runs every 3 hours automatically
- **Custom Background Music** - Drop your own music files in the `bg_music/` folder
- **Watermark** - `@shyariofficial-k2q` branded on every reel

---

## Setup Guide

### Step 1: Install Python Dependencies

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Install ImageMagick

MoviePy requires ImageMagick for text rendering.

1. Download from: https://imagemagick.org/script/download.php
2. During installation, **check "Install legacy utilities"**
3. Make sure it's added to your system PATH

### Step 3: Get Gemini API Key

1. Go to: https://aistudio.google.com/
2. Create a free API key
3. Open `.env` and replace `your_gemini_api_key_here` with your key

### Step 4: Set Up YouTube API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Go to **APIs & Services > Credentials**
5. Create **OAuth 2.0 Client ID** (select "Desktop App")
6. Download the JSON file and save it as `client_secrets.json` in the project root
7. Go to **OAuth consent screen** > Add your Google account as a **Test User**

### Step 5: Add Background Music

Drop your `.mp3` or `.wav` files in the `bg_music/` folder:

```
bg_music/
├── soft_music_1.mp3
├── lofi_beat.mp3
└── instrumental.wav
```

The system randomly picks a track for each reel.

---

## Usage

### Start Automation (runs every 3 hours)
```bash
python main.py
```

### Generate & Upload One Reel Now
```bash
python main.py --once
```

### Generate Video Only (no upload - for testing)
```bash
python main.py --generate-only
```

### Test YouTube Authentication
```bash
python main.py --test-auth
```

---

## Project Structure

```
youtube rell automation/
├── .env                    <- Your API keys
├── config.py               <- All settings (video size, timing, themes)
├── requirements.txt        <- Python dependencies
├── client_secrets.json     <- YouTube OAuth (you create this)
│
├── bg_music/               <- DROP YOUR MUSIC HERE
│   └── your_music.mp3
│
├── output/                 <- Generated videos (auto-created)
│
├── shayari_generator.py    <- AI shayari generation (Hinglish)
├── video_creator.py        <- Video creation with MoviePy
├── youtube_uploader.py     <- YouTube API upload
├── scheduler.py            <- 3-hour scheduling loop
└── main.py                 <- Entry point
```

---

## Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `VIDEO_DURATION` | 25s | Length of each reel |
| `SCHEDULE_INTERVAL_HOURS` | 3 | Hours between uploads |
| `SHAYARI_FONT_SIZE` | 62 | Main text size |
| `WATERMARK_TEXT` | @shyariofficial-k2q | Your brand |
| `TEXT_COLOR` | white | Shayari text color |
| `FADE_DURATION` | 0.8s | Text fade-in speed |

---

## 24/7 MOBILE SE CHALANE KA TARIKA (Run from Phone)

Apne PC ko 24/7 on rakhne ki zarurat nahi hai. **PythonAnywhere** (free cloud server) use karo jo phone ke browser se chal jayega.

### Method: PythonAnywhere (FREE - Phone se manage karo)

#### Step 1: Account banao
1. Phone ka browser kholo (Chrome/Safari)
2. Jao: **https://www.pythonanywhere.com**
3. "Start for free" pe click karo
4. Account banao (email + password)

#### Step 2: Files upload karo
1. Login ke baad **"Files"** tab pe jao
2. Ek naya folder banao: `shayari_bot`
3. In files ko ek-ek karke upload karo:
   - `config.py`
   - `shayari_generator.py`
   - `video_creator.py`
   - `youtube_uploader.py`
   - `scheduler.py`
   - `main.py`
   - `requirements.txt`
   - `.env` (apna Gemini API key daalke)
   - `client_secrets.json` (YouTube OAuth file)
4. `bg_music` folder banao aur music files upload karo

#### Step 3: Dependencies install karo
1. **"Consoles"** tab pe jao
2. **"Bash"** pe click karo (new console khulega)
3. Ye commands type karo:
```bash
cd shayari_bot
pip install --user -r requirements.txt
```

#### Step 4: Pehle test karo
Console mein ye run karo:
```bash
cd shayari_bot
python main.py --generate-only
```
Agar video ban gaya = sab sahi hai!

#### Step 5: YouTube auth setup karo
Ye step sirf PC pe karna padega (ek baar):
1. PC pe project folder mein jaake run karo: `python main.py --test-auth`
2. Browser khulega, Google login karo
3. `token.json` file ban jayegi
4. Is `token.json` ko PythonAnywhere pe upload karo `shayari_bot` folder mein

#### Step 6: Scheduled Task set karo (24/7 automation!)
1. PythonAnywhere pe **"Tasks"** tab pe jao
2. **"Scheduled tasks"** mein:
   - Time set karo (e.g., `00:00` for midnight)
   - Command box mein likho:
   ```
   cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   ```
3. **"Create"** pe click karo

4. **Har 3 ghante ke liye**, 8 tasks banao alag-alag time pe:
   ```
   00:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   03:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   06:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   09:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   12:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   15:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   18:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   21:00  ->  cd /home/YOUR_USERNAME/shayari_bot && python main.py --once
   ```

> **NOTE:** Free PythonAnywhere account mein 1 scheduled task milta hai. Agar har 3 ghante chahiye toh Paid plan ($5/month) lena padega. Free mein din mein 1 baar upload hoga.

#### Phone se monitor karo
- PythonAnywhere ka **"Files"** tab kholo
- `output/` folder mein generated videos dikhenge
- `automation.log` file mein sab logs dikhenge
- **"Tasks"** tab pe task status dikh jayega

---

### Alternative: GitHub Actions (100% FREE, unlimited tasks)

Agar PythonAnywhere paid nahi chahiye, toh **GitHub Actions** use karo - bilkul FREE:

#### Step 1: GitHub repo banao
1. Phone pe GitHub app install karo
2. Naya repository banao: `shayari-bot`
3. Saari files upload karo

#### Step 2: Secrets add karo
Repository Settings > Secrets and Variables > Actions:
- `GEMINI_API_KEY` = apna Gemini key
- `YOUTUBE_TOKEN` = token.json ka content (pehle PC pe generate karo)
- `CLIENT_SECRETS` = client_secrets.json ka content

#### Step 3: Workflow file banao
`.github/workflows/shayari.yml` file banao:
```yaml
name: Shayari Reel Automation
on:
  schedule:
    - cron: '0 */3 * * *'   # Har 3 ghante
  workflow_dispatch:          # Manual bhi chala sakte ho

jobs:
  generate-and-upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Setup credentials
        run: |
          echo "${{ secrets.CLIENT_SECRETS }}" > client_secrets.json
          echo "${{ secrets.YOUTUBE_TOKEN }}" > token.json
          echo "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" > .env

      - name: Run pipeline
        run: python main.py --once
```

GitHub Actions free mein **2000 minutes/month** deta hai. Har run ~5 min = ~400 runs/month = kaafi hai!

---

## Important Notes

- **YouTube API Quota**: Free tier allows ~6 uploads/day. Every 3 hours = 8/day. Request a quota increase if needed, or change `SCHEDULE_INTERVAL_HOURS` to 4.
- **First Run**: YouTube authentication will open your browser for login. After that, it saves the token automatically.
- **Copyright**: Use royalty-free music only to avoid YouTube copyright strikes.
- **Hinglish Output**: Shayari will be generated in Roman script like "Dil ke tukde hazaar hue" instead of Devanagari.

---

## License

For personal use. (c) @shyariofficial-k2q
