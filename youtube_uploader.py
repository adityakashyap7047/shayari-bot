"""
YouTube Uploader — uploads Shorts via YouTube Data API v3 with OAuth 2.0.
"""

from __future__ import annotations

import os
import json
import time
import http.client
import httplib2
import random

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

import config


# Retry configuration
MAX_RETRIES = 5
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                         http.client.IncompleteRead, http.client.ImproperConnectionState,
                         http.client.CannotSendRequest, http.client.CannotSendHeader,
                         http.client.ResponseNotReady, http.client.BadStatusLine)


def _authenticate() -> object:
    """
    Authenticate with YouTube using OAuth 2.0.
    First run opens browser for login; subsequent runs use saved token.
    """
    creds = None

    # Load saved token
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.YOUTUBE_SCOPES)

    # If no valid creds, do the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  🔄 Refreshing YouTube token…")
            creds.refresh(Request())
        else:
            if not os.path.exists(config.CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"YouTube OAuth file not found: {config.CLIENT_SECRETS_FILE}\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials"
                )
            print("  🌐 Opening browser for YouTube authentication…")
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CLIENT_SECRETS_FILE, config.YOUTUBE_SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(config.TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("  ✅ YouTube authentication successful!")

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy: str = "public",
) -> str | None:
    """
    Upload a video to YouTube as a Short.

    Parameters
    ----------
    video_path : str
        Path to the .mp4 file.
    title : str
        Video title (will have #Shorts appended).
    description : str
        Video description.
    tags : list[str], optional
        Video tags. Defaults to config.YOUTUBE_DEFAULT_TAGS.
    privacy : str
        "public", "unlisted", or "private".

    Returns
    -------
    str or None : YouTube video ID if successful, None otherwise.
    """
    if not os.path.exists(video_path):
        print(f"  ❌ Video file not found: {video_path}")
        return None

    youtube = _authenticate()

    # Ensure #Shorts is in the title
    if "#Shorts" not in title:
        title = f"{title} #Shorts"

    if tags is None:
        tags = config.YOUTUBE_DEFAULT_TAGS.copy()

    # Build the request body
    body = {
        "snippet": {
            "title": title[:100],  # YouTube max title length
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": config.YOUTUBE_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Create the upload request
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,  # 1 MB chunks
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    print(f"  📤 Uploading: {title}")
    video_id = _resumable_upload(request)

    if video_id:
        print(f"  ✅ Upload complete! https://youtube.com/shorts/{video_id}")
    else:
        print("  ❌ Upload failed after all retries.")

    return video_id


def _resumable_upload(request) -> str | None:
    """Execute a resumable upload with retry logic."""
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  📤 Uploading… {pct}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: {e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = str(e)

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                print(f"  ❌ Upload failed: {error}")
                return None
            sleep_seconds = random.random() * (2 ** retry)
            print(f"  ⚠ Retry {retry}/{MAX_RETRIES} in {sleep_seconds:.1f}s — {error}")
            time.sleep(sleep_seconds)
            error = None

    if response:
        return response.get("id")
    return None


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    # Test authentication only
    print("Testing YouTube authentication…")
    yt = _authenticate()
    print("✅ Authentication works! Ready to upload.")
