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


def _authenticate(
    client_secrets_path: str | None = None,
    token_path: str | None = None,
) -> object:
    """
    Authenticate with YouTube using OAuth 2.0.
    First run opens browser for login; subsequent runs use saved token.

    Parameters
    ----------
    client_secrets_path : str, optional
        Path to the channel's client_secrets.json. Defaults to config.CLIENT_SECRETS_FILE.
    token_path : str, optional
        Path to the channel's token.json. Defaults to config.TOKEN_FILE.
    """
    if client_secrets_path is None:
        client_secrets_path = config.CLIENT_SECRETS_FILE
    if token_path is None:
        token_path = config.TOKEN_FILE

    creds = None

    # Load saved token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, config.YOUTUBE_SCOPES)

    # If no valid creds, do the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  🔄 Refreshing YouTube token…")
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError(
                    f"YouTube OAuth file not found: {client_secrets_path}\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials"
                )
            print("  🌐 Opening browser for YouTube authentication…")
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_path, config.YOUTUBE_SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        print("  ✅ YouTube authentication successful!")

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy: str = "public",
    category_id: str | None = None,
    client_secrets_path: str | None = None,
    token_path: str | None = None,
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
    category_id : str, optional
        YouTube category ID. Defaults to config.YOUTUBE_CATEGORY_ID.
    client_secrets_path : str, optional
        Path to channel-specific client_secrets.json.
    token_path : str, optional
        Path to channel-specific token.json.

    Returns
    -------
    str or None : YouTube video ID if successful, None otherwise.
    """
    if not os.path.exists(video_path):
        print(f"  ❌ Video file not found: {video_path}")
        return None

    youtube = _authenticate(
        client_secrets_path=client_secrets_path,
        token_path=token_path,
    )

    # Ensure #Shorts is in the title
    if "#Shorts" not in title:
        title = f"{title} #Shorts"

    if tags is None:
        tags = config.YOUTUBE_DEFAULT_TAGS.copy()
    if category_id is None:
        category_id = config.YOUTUBE_CATEGORY_ID

    # Build the request body
    body = {
        "snippet": {
            "title": title[:100],  # YouTube max title length
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
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
    import sys
    # Test authentication — optionally pass channel credentials
    print("Testing YouTube authentication…")
    if len(sys.argv) >= 3:
        yt = _authenticate(client_secrets_path=sys.argv[1], token_path=sys.argv[2])
    else:
        yt = _authenticate()
    print("✅ Authentication works! Ready to upload.")
