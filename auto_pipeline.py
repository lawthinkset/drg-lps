"""
Dragon Lapps YouTube Automation Pipeline
Full End-to-End Long-Form Video Orchestrator:
1. Fetches Dragon Animation Video, Audio, Image triplets from Google Drive (or local folders)
2. Auto-upscales to 1080p Full HD (Lanczos + Unsharp)
3. Generates high-CTR 1280x720 custom Dragon Lapps thumbnail
4. Renders 1-Hour Full HD Video (Forward + Reverse ping-pong seamless loop)
5. Generates high-converting SEO metadata for Dragon World Animations & publishes to YouTube
6. Automatically cleans up rendered video to conserve disk space
"""
import os
import sys
import json
import glob
import random
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from google_drive_fetch import fetch_assets_triplet
from thumbnail_generator import create_lofi_thumbnail, LOFI_HOOKS
from video_generator import build_lofi_longform_video

PUBLISHED_LOG = "published_videos.json"
ALLOW_REPOST = os.getenv("ALLOW_REPOST", "true").lower() == "true"
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Dragon Lapps")
POLLINATIONS_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gemini-fast")
GEN_API = "https://gen.pollinations.ai"


def get_published_history():
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_published_entry(video_name, audio_name, image_name, yt_video_id=None, fb_video_id=None, title=""):
    history = get_published_history()
    fb_page_id = os.getenv("FB_PAGE_ID", "")
    entry = {
        "video_file": os.path.basename(video_name),
        "audio_file": os.path.basename(audio_name),
        "image_file": os.path.basename(image_name) if image_name else "",
        "youtube_id": yt_video_id,
        "youtube_url": f"https://youtu.be/{yt_video_id}" if yt_video_id else "LOCAL_RENDER",
        "facebook_id": fb_video_id,
        "facebook_url": f"https://www.facebook.com/{fb_page_id}/videos/{fb_video_id}" if fb_video_id else None,
        "title": title,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    history.append(entry)
    with open(PUBLISHED_LOG, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"[LOG] Saved publication record to {PUBLISHED_LOG}")


def generate_youtube_metadata(audio_path, video_path):
    """
    Generate high-converting SEO Dragon World Animation title, description, and tags.
    Explicitly focused on Dragon Animations, Dragon World, Fantasy, Epic visuals.
    """
    base_name = os.path.splitext(os.path.basename(audio_path))[0].replace("_", " ").title()

    prompt = (
        f"You are the creative director for '{CHANNEL_NAME}', a popular YouTube channel featuring "
        "EPIC DRAGON WORLD ANIMATIONS — stunning dragon visuals, fantasy worlds, fire-breathing dragons, "
        "ancient kingdoms, and magical dragon realms.\n\n"
        "STRICT GUIDELINES:\n"
        "- The content is strictly DRAGON ANIMATIONS, epic fantasy dragon worlds, fire, magic, ancient legends, and majestic creatures.\n"
        "- Focus on awe, wonder, epic fantasy, and the mythical world of dragons.\n"
        "- Generate a high-CTR YouTube title (max 95 chars) formatted for dragon animation videos, e.g. "
        f"'Epic Dragon World | {base_name} · Fire, Magic & Ancient Legends (1080p HD Animation)'\n"
        "- Generate an engaging, epic, atmospheric description (4-6 sentences) inviting viewers to witness "
        "the breathtaking beauty of dragon animations, explore ancient dragon kingdoms, watch fire-breathing dragons soar, "
        f"and subscribe to {CHANNEL_NAME} for more epic dragon content.\n"
        "- Include relevant hashtags: #dragon #dragonanimation #dragonworld #epicfantasy #dragonlapps #fantasydragons #dragonfire #mythicaldragons #epicanimation\n\n"
        f"Audio track: '{base_name}'. Visual asset: '{os.path.basename(video_path)}'.\n\n"
        "Return ONLY a valid JSON object without markdown fences, with this exact schema:\n"
        "{\n"
        '  "title": "<title under 95 chars>",\n'
        '  "description": "<rich description>",\n'
        '  "tags": ["dragon", "dragon animation", "dragon world", "epic fantasy", "dragon lapps", "fantasy dragons", "dragon fire", "mythical dragons", "epic animation", "dragon legends", "fantasy world", "fire dragon", "dragon 3d", "dragon art", "ancient dragon"]\n'
        "}"
    )

    if POLLINATIONS_KEY:
        try:
            res = requests.post(
                f"{GEN_API}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {POLLINATIONS_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": AI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.85
                },
                timeout=30
            )
            if res.status_code == 200:
                raw = res.json()["choices"][0]["message"]["content"].strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data = json.loads(raw.strip())
                title = data.get("title", "").strip().replace('"', '')
                desc = data.get("description", "").strip()
                tags = data.get("tags", [])

                if title and desc:
                    return title, desc, tags
        except Exception as e:
            print(f"[METADATA NOTE] Pollinations AI fallback: {e}")

    # Curated high-converting dragon animation fallback templates
    titles_templates = [
        f"Epic Dragon World | {base_name} · Fire, Magic & Ancient Legends (1080p HD Animation)",
        f"🐉 Dragon Realms Unleashed | {base_name} · Breathtaking Dragon Animation (4K Fantasy)",
        f"Majestic Dragon Soars | {base_name} · Epic Fantasy Dragon World Animation",
        f"Ancient Dragon Kingdom | {base_name} · Fire & Magic Dragon World (1080p HD)",
        f"🔥 Dragon Fire & Fury | {base_name} · Epic Dragon World Animation (Fantasy 1080p)",
        f"Legendary Dragon Chronicles | {base_name} · Epic Fantasy Animation (Dragon World HD)"
    ]
    title = random.choice(titles_templates)

    desc = (
        f"🐉 Welcome to Dragon Lapps — your gateway to the breathtaking world of epic dragon animations!\n\n"
        f"In this video, witness the awe-inspiring power of '{base_name}' set against sweeping dragon world visuals. "
        f"Watch majestic dragons soar across ancient kingdoms, unleash their fiery breath upon mythical landscapes, "
        f"and dominate the skies with unrivaled grace and power. Every frame is crafted to immerse you in the ultimate fantasy dragon experience.\n\n"
        f"🔥 ABOUT DRAGON LAPPS:\n"
        f"Dragon Lapps is your premium destination for stunning dragon animations, epic fantasy dragon worlds, "
        f"and mythical creature spectacles. From fire-breathing behemoths to ancient dragon legends — we bring the dragon world to life.\n\n"
        f"✨ What You'll See:\n"
        f"• Majestic dragons soaring through dramatic fantasy skies\n"
        f"• Breathtaking fire breath and magical dragon abilities\n"
        f"• Ancient dragon kingdoms and legendary mythical worlds\n"
        f"• Stunning 1080p Full HD dragon animation quality\n\n"
        f"🎬 New dragon animations released regularly — Subscribe now!\n"
        f"🔔 Hit the bell so you never miss an epic dragon video from Dragon Lapps!\n"
        f"💬 Which dragon is your favorite? Tell us in the comments below! 🐉🔥\n\n"
        f"#dragon #dragonanimation #dragonworld #epicfantasy #dragonlapps #fantasydragons #dragonfire #mythicaldragons #epicanimation"
    )

    tags = [
        "dragon", "dragon animation", "dragon world", "epic fantasy", "dragon lapps",
        "fantasy dragons", "dragon fire", "mythical dragons", "epic animation",
        "dragon legends", "fantasy world", "fire dragon", "dragon 3d", "dragon art",
        "ancient dragon", "dragon video", "dragon 1080p", "dragon hd"
    ]

    return title, desc, tags


def run_pipeline(duration=3600, dry_run=False, video_override=None, audio_override=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_thumb_dir = os.path.join(script_dir, "output_thumbnails")
    output_video_dir = os.path.join(script_dir, "output_videos")

    os.makedirs(output_thumb_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)

    print("\n" + "=" * 65)
    print(f"      DRAGON LAPPS ({CHANNEL_NAME}) - EPIC DRAGON VIDEO AUTOMATION PIPELINE")
    print("=" * 65)

    # Step 1: Fetch triplet
    if video_override and audio_override:
        vid_path = video_override
        aud_path = audio_override
        img_path = None
        is_repost = False
    else:
        vid_path, aud_path, img_path, is_repost = fetch_assets_triplet(allow_repost=ALLOW_REPOST)

    if not vid_path or not aud_path:
        print("[ERROR] Could not fetch required video and audio assets.")
        return False

    print(f"\n[STEP 1] Assets Selected:")
    print(f"  • Video: {os.path.basename(vid_path)}")
    print(f"  • Audio: {os.path.basename(aud_path)}")
    print(f"  • Image: {os.path.basename(img_path) if img_path else 'Extracting frame from video'}")

    # If no thumbnail image, extract frame at 2s from video
    if not img_path or not os.path.exists(img_path):
        os.makedirs(os.path.join(script_dir, "input_images"), exist_ok=True)
        img_path = os.path.join(script_dir, "input_images", f"frame_{os.path.splitext(os.path.basename(vid_path))[0]}.jpg")
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:02", "-i", vid_path, "-frames:v", "1", img_path], check=True)

    # Step 2: Generate Thumbnail
    safe_name = "".join(c for c in os.path.splitext(os.path.basename(aud_path))[0] if c.isalnum() or c in (" ", "_", "-")).strip()
    thumb_output = os.path.join(output_thumb_dir, f"Thumb_{safe_name}.jpg")

    hook = random.choice(LOFI_HOOKS)
    print(f"\n[STEP 2] Creating 1280x720 Thumbnail with Hook: '{hook['main']}'...")
    create_lofi_thumbnail(img_path, thumb_output, main_text=hook["main"], sub_text=hook["sub"], badge_text=hook.get("badge"))

    # Step 3: Render Full Video
    dur_label = f"{duration // 60}min" if duration >= 60 else f"{duration}s"
    final_video_path = os.path.join(output_video_dir, f"DragonLapps_{safe_name}_{dur_label}.mp4")

    print(f"\n[STEP 3] Rendering {dur_label} 1080p HD Dragon Animation Video...")
    success = build_lofi_longform_video(
        input_video=vid_path,
        input_audio=aud_path,
        output_path=final_video_path,
        duration_seconds=duration,
        remove_watermark=True,
        upscale_to_1080p=True
    )

    if not success:
        print("[ERROR] Video generation failed.")
        return False

    # Step 4: Metadata & Publishing
    title, desc, tags = generate_youtube_metadata(aud_path, vid_path)
    print(f"\n[STEP 4] Generated YouTube Metadata:")
    print(f"  • Title: {title}")
    print(f"  • Tags: {', '.join(tags[:6])}...")

    if dry_run:
        print(f"\n[DRY RUN] Completed. Video saved at: {final_video_path}")
        print(f"[DRY RUN] Thumbnail saved at: {thumb_output}")
        save_published_entry(vid_path, aud_path, img_path, yt_video_id=None, fb_video_id=None, title=title)
        return True

    # Step 5: Upload to Platforms (YouTube & Facebook)
    video_id = None
    try:
        from publish_youtube import upload_to_youtube, set_video_thumbnail
        print(f"\n[STEP 5] Uploading Dragon Animation Video to YouTube...")
        video_id = upload_to_youtube(final_video_path, title, desc, tags=tags)
        if video_id:
            set_video_thumbnail(video_id, thumb_output)
            print(f"🎉 SUCCESS! Published to YouTube: https://youtu.be/{video_id}")
    except Exception as e:
        print(f"[YOUTUBE NOTE] YouTube API upload error: {e}")

    # Facebook Page Upload
    fb_video_id = None
    try:
        from publish_facebook import upload_to_facebook
        print(f"\n[facebook] Uploading to Dragon Lapps Facebook Page...")
        fb_res = upload_to_facebook(final_video_path, title, desc)
        fb_video_id = fb_res.get("id")
        print(f"🎉 SUCCESS! Published to Facebook: {fb_video_id}")
    except Exception as e_fb:
        print(f"[FACEBOOK NOTE] Facebook upload skipped or encountered error: {e_fb}")

    save_published_entry(vid_path, aud_path, img_path, yt_video_id=video_id, fb_video_id=fb_video_id, title=title)

    # Step 6: Cleanup rendered video to free disk space
    if os.path.exists(final_video_path):
        try:
            os.remove(final_video_path)
            print(f"[CLEANUP] Deleted rendered video to save disk space: {final_video_path}")
        except Exception:
            pass

    return True if (video_id or fb_video_id) else False


if __name__ == "__main__":
    dur = 3600
    is_dry = "--dry-run" in sys.argv
    for idx, arg in enumerate(sys.argv):
        if arg == "--duration" and idx + 1 < len(sys.argv):
            dur = int(sys.argv[idx + 1])
    run_pipeline(duration=dur, dry_run=is_dry)
