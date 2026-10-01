# 🐉 Dragon Lapps — Epic Dragon World Animation Bot

[![Auto Publish Dragon Videos](https://github.com/lawthinkset/drg-lps/actions/workflows/auto_publish.yml/badge.svg)](https://github.com/lawthinkset/drg-lps/actions/workflows/auto_publish.yml)

**Dragon Lapps** is a streamlined, automated YouTube & Facebook publishing bot that delivers breathtaking **Dragon World Animations** daily directly from Google Drive in 1080p Full HD with watermark removal.

---

## ⚡ How It Works

```
Google Drive (Single Dragon Video Folder)
    ↓
auto_pipeline.py
    ↓
[1] Fetch dragon animation video (.mp4)
[2] Remove watermark / logo via astroid inpainting
[3] Auto-upscale to 1080p Full HD (Lanczos + Unsharp)
[4] Preserve native video duration (e.g. 10s video, NO looping) & native audio
[5] Generate AI dragon-themed title + description (Pollinations AI)
[6] Publish directly to YouTube (Film & Animation)
[7] Publish directly to Dragon Lapps Facebook Page
```

---

## 🚀 GitHub Actions Setup

The bot runs automatically on schedule or on demand via `workflow_dispatch`.

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GOOGLE_DRIVE_FOLDER_ID` | Single Google Drive folder with dragon animation videos |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Google Service Account JSON key |
| `POLLINATIONS_API_KEY` | Pollinations AI API key (for title/description generation) |
| `FB_PAGE_ID` | Dragon Lapps Facebook Page ID |
| `FB_PAGE_ACCESS_TOKEN` | Dragon Lapps Facebook Page Access Token |
| `YOUTUBE_CLIENT_ID` | YouTube OAuth2 Client ID |
| `YOUTUBE_CLIENT_SECRET` | YouTube OAuth2 Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | YouTube OAuth2 Refresh Token |

---

## 🛠️ Local Testing

```bash
python auto_pipeline.py --dry-run
```

---

## 📁 Project Structure

```
Dragon Lapps/
├── auto_pipeline.py        # Main automation pipeline (native duration, no loop)
├── video_generator.py      # Watermark inpainter & 1080p upscaler
├── google_drive_fetch.py   # Single-folder Google Drive fetcher
├── publish_youtube.py      # YouTube upload module (Film & Animation)
├── publish_facebook.py     # Facebook Page upload module
├── published_videos.json   # Published videos history log
├── requirements.txt        # Python dependencies
├── .env                    # Local credentials (never committed)
└── .github/workflows/
    └── auto_publish.yml    # Daily GitHub Actions workflow
```
