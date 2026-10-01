# 🐉 Dragon Lapps — Epic Dragon World Animation Bot

[![Auto Publish Dragon Videos](https://github.com/lawthinkset/drg-lps/actions/workflows/auto_publish.yml/badge.svg)](https://github.com/lawthinkset/drg-lps/actions/workflows/auto_publish.yml)

**Dragon Lapps** is a fully automated YouTube & Facebook publishing bot that delivers breathtaking **Epic Dragon World Animations** daily — fire-breathing dragons, ancient kingdoms, mythical realms, and legendary creatures — all in stunning 1080p Full HD.

---

## 🔥 What Dragon Lapps Publishes

- 🐉 **Epic Dragon Animation Videos** — majestic dragons soaring, fire breath, fantasy worlds
- 🏰 **Ancient Dragon Kingdom Scenes** — sweeping fantasy landscapes with castles and mountains
- ✨ **Magical Dragon Realms** — glowing effects, mystical atmospheres, legendary creatures
- 🎬 **1080p Full HD** — cinematic quality dragon content, every single day

---

## ⚙️ How It Works

```
Google Drive (Dragon Animation Assets)
    ↓
auto_pipeline.py
    ↓
[1] Fetch video + audio + image triplet
[2] Upscale to 1080p HD
[3] Generate Dragon Lapps thumbnail
[4] Render long-form video (1-hour loop)
[5] Generate AI-powered dragon-themed title + description (Pollinations AI)
[6] Publish to YouTube (Film & Animation category)
[7] Publish to Dragon Lapps Facebook Page
```

---

## 🚀 GitHub Actions — Daily Auto-Publish

The bot runs automatically every day at **9:00 AM UTC** via GitHub Actions.

### Required GitHub Secrets

Set these in `Settings → Secrets and variables → Actions`:

| Secret | Description |
|--------|-------------|
| `GOOGLE_DRIVE_VIDEO_FOLDER_ID` | Google Drive folder with dragon animation videos |
| `GOOGLE_DRIVE_AUDIO_FOLDER_ID` | Google Drive folder with epic background music |
| `GOOGLE_DRIVE_IMAGE_FOLDER_ID` | Google Drive folder with dragon artwork images |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Google Service Account JSON key |
| `YOUTUBE_CLIENT_ID` | YouTube OAuth2 Client ID |
| `YOUTUBE_CLIENT_SECRET` | YouTube OAuth2 Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | YouTube OAuth2 Refresh Token |
| `POLLINATIONS_API_KEY` | Pollinations AI API key (for title/description generation) |
| `FB_PAGE_ID` | Dragon Lapps Facebook Page ID |
| `FB_PAGE_ACCESS_TOKEN` | Dragon Lapps Facebook Page Access Token |

---

## 🛠️ Local Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python auto_pipeline.py --dry-run
```

---

## 📺 Dragon Lapps Channels

- 🎬 **YouTube**: Dragon Lapps
- 📘 **Facebook**: Dragon Lapps Page
- 🐉 **Theme**: Epic Dragon World Animations

---

## 📁 Project Structure

```
Dragon Lapps/
├── auto_pipeline.py        # Main automation pipeline
├── publish_youtube.py      # YouTube upload module
├── publish_facebook.py     # Facebook upload module
├── video_generator.py      # 1080p video renderer
├── thumbnail_generator.py  # Custom thumbnail creator
├── google_drive_fetch.py   # Asset fetcher from Google Drive
├── published_videos.json   # Publication history log
├── requirements.txt        # Python dependencies
├── .env                    # Local secrets (never commit!)
└── .github/workflows/
    └── auto_publish.yml    # Daily GitHub Actions workflow
```

---

*Powered by Pollinations AI · Meta Graph API · YouTube Data API v3*
