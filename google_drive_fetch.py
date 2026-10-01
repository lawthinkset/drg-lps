"""
Google Drive Integration Module for Dragon Lapps
Downloads Dragon Animation Videos from the single Dragon Google Drive folder.
Supports:
- Unpublished video priority
- Weighted Least-Recently-Used (LRU) selection for infinite circulation
- Local input_videos folder fallback
"""
import os
import io
import json
import sys
import glob
import random
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

GOOGLE_DRIVE_FOLDER_ID = (
    os.getenv("GOOGLE_DRIVE_FOLDER_ID") or
    os.getenv("GOOGLE_DRIVE_VIDEO_FOLDER_ID") or
    "10D0j0siAtZC2zBXJvcJ76TdMNxQLVWQD"
).strip()

GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY", "service_account.json")
LOCAL_VIDEO_DIR = os.getenv("LOCAL_VIDEO_DIR", "input_videos")
PUBLISHED_LOG = "published_videos.json"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_drive_service():
    """Build and return an authorized Google Drive v3 service instance."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("[DRIVE] Google API libraries not installed.")
        return None

    if not GOOGLE_SERVICE_ACCOUNT_KEY:
        return None

    try:
        key_str = GOOGLE_SERVICE_ACCOUNT_KEY.strip()
        if key_str.startswith("{"):
            info = json.loads(key_str)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            return build("drive", "v3", credentials=credentials)
        elif os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
            credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_KEY, scopes=SCOPES)
            return build("drive", "v3", credentials=credentials)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sa_path = os.path.join(script_dir, GOOGLE_SERVICE_ACCOUNT_KEY)
            if os.path.exists(sa_path):
                credentials = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
                return build("drive", "v3", credentials=credentials)
            return None
    except Exception as e:
        print(f"[DRIVE ERROR] Failed to initialize Google Drive: {e}")
        return None


def list_files_in_folder(folder_id, extensions=None):
    """List non-trashed files inside the Google Drive folder."""
    if not folder_id or folder_id.startswith("your_"):
        return []
    service = get_drive_service()
    if not service:
        return []
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, size)",
            pageSize=100
        ).execute()
        files = results.get("files", [])
        if extensions:
            filtered = []
            for f in files:
                name = f.get("name", "").lower()
                if any(name.endswith(ext) for ext in extensions):
                    filtered.append(f)
            return filtered
        return files
    except Exception as e:
        print(f"[DRIVE ERROR] Error listing files in folder {folder_id}: {e}")
        return []


def download_file(file_id, dest_path):
    """Downloads a single video file from Google Drive."""
    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        return False
    service = get_drive_service()
    if not service:
        return False
    try:
        request = service.files().get_media(fileId=file_id)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        with io.FileIO(dest_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=10 * 1024 * 1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return True
    except Exception as e:
        print(f"[DRIVE ERROR] Error downloading {file_id}: {e}")
        return False


def get_usage_counts():
    """Returns usage counts for published video files."""
    vid_counts = {}
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    v = (item.get("video_file") or "").strip().lower()
                    if v:
                        vid_counts[v] = vid_counts.get(v, 0) + 1
        except Exception:
            pass
    return vid_counts


def pick_weighted_lru(candidates, usage_counts, key_fn, allow_repost=True):
    """Selects video with strict priority on unpublished items, then weighted LRU."""
    if not candidates:
        return None, False

    unseen = [c for c in candidates if key_fn(c).strip().lower() not in usage_counts]
    if unseen:
        return unseen[0], False

    if allow_repost:
        weights = [
            max(1, 1000 // (3 ** min(usage_counts.get(key_fn(c).strip().lower(), 0), 6)))
            for c in candidates
        ]
        return random.choices(candidates, weights=weights, k=1)[0], True

    return None, False


def fetch_dragon_video(allow_repost=True):
    """
    Fetches ONE dragon animation video from Google Drive or local input_videos.
    Returns: (video_path, is_repost)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    vid_dir = os.path.join(script_dir, LOCAL_VIDEO_DIR)
    os.makedirs(vid_dir, exist_ok=True)

    drive_service = get_drive_service()
    drive_ready = (drive_service is not None) and bool(GOOGLE_DRIVE_FOLDER_ID) and not GOOGLE_DRIVE_FOLDER_ID.startswith("your_")

    if drive_ready:
        print(f"[DRIVE] Querying Dragon Google Drive folder ({GOOGLE_DRIVE_FOLDER_ID})...")
        v_drive = list_files_in_folder(GOOGLE_DRIVE_FOLDER_ID, extensions=[".mp4", ".mov", ".mkv"])
    else:
        v_drive = []

    local_vids = sorted(glob.glob(os.path.join(vid_dir, "*.mp4")) + glob.glob(os.path.join(vid_dir, "*.mov")))
    vid_counts = get_usage_counts()

    sel_video_path = None
    is_repost = False

    if v_drive:
        chosen_v, is_repost = pick_weighted_lru(v_drive, vid_counts, lambda x: x["name"], allow_repost=allow_repost)
        if chosen_v:
            dest_v = os.path.join(vid_dir, chosen_v["name"])
            if not os.path.exists(dest_v):
                print(f"[DRIVE] Downloading dragon animation video: {chosen_v['name']}...")
                download_file(chosen_v["id"], dest_v)
            sel_video_path = dest_v
    elif local_vids:
        sel_video_path, is_repost = pick_weighted_lru(local_vids, vid_counts, os.path.basename, allow_repost=allow_repost)

    if not sel_video_path:
        print("[ERROR] No dragon animation videos found in Google Drive or local input_videos folder.")
        return None, False

    return sel_video_path, is_repost


if __name__ == "__main__":
    v, rep = fetch_dragon_video()
    print(f"Selected Video: {v} (repost: {rep})")
