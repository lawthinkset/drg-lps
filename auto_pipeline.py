"""
Dragon Lapps YouTube & Facebook Automation Pipeline
1. Fetches dragon animation video from Google Drive (single folder)
2. Removes logo / watermark in the bottom-right corner via astroid inpainting
3. Auto-upscales to 1080p Full HD (Lanczos + Unsharp) if needed
4. Preserves native duration (NO LOOPING, e.g. 10s video) and original audio
5. Generates high-converting Dragon World SEO title, description, and hashtags via Pollinations AI
6. Publishes to YouTube (Film & Animation) and Dragon Lapps Facebook Page
7. Cleans up rendered video to conserve disk space
"""
import os
import sys
import re
import json
import random
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from google_drive_fetch import fetch_dragon_video
from video_generator import process_dragon_video

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


def save_published_entry(video_name, yt_video_id=None, fb_video_id=None, title=""):
    history = get_published_history()
    fb_page_id = os.getenv("FB_PAGE_ID", "1371314622722733")
    entry = {
        "video_file": os.path.basename(video_name),
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


def generate_dragon_metadata(video_path):
    """
    Generate high-converting SEO Dragon World Animation title, description, and tags
    directly based on the video name.
    """
    stem = os.path.splitext(os.path.basename(video_path))[0]
    # Clean up timestamp suffixes like _20261001044840
    clean_name = re.sub(r'_\d{10,}$', '', stem).replace('_', ' ').replace('-', ' ').strip().title()

    prompt = (
        f"You are the creative director for '{CHANNEL_NAME}', a popular video channel featuring "
        "EPIC DRAGON WORLD ANIMATIONS — breathtaking dragon visuals, mythical fantasy worlds, fire-breathing dragons, "
        "and ancient magical realms.\n\n"
        "STRICT GUIDELINES:\n"
        f"- The animation scene is: '{clean_name}'.\n"
        "- Content is strictly DRAGON ANIMATION, epic fantasy, mythical creatures, fire and magic.\n"
        "- Generate a high-CTR title (max 90 chars), e.g. "
        f"'{clean_name} 🐉 Epic Dragon World Animation (1080p)'\n"
        "- Generate an engaging, epic description (3-5 sentences) celebrating this dragon animation spectacle, "
        "inviting viewers to like, share, and subscribe to Dragon Lapps for daily epic dragon videos.\n"
        "- Include relevant hashtags: #dragon #dragonanimation #dragonworld #epicfantasy #dragonlapps #mythicaldragons #firedragon #epicanimation #shorts\n\n"
        "Return ONLY a valid JSON object without markdown fences, with this exact schema:\n"
        "{\n"
        '  "title": "<title under 90 chars>",\n'
        '  "description": "<epic description with hashtags>",\n'
        '  "tags": ["dragon", "dragon animation", "dragon world", "epic fantasy", "dragon lapps", "fantasy dragons", "dragon fire", "mythical dragons", "epic animation", "fire dragon", "dragon 3d", "dragon art", "ancient dragon"]\n'
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

    # Fallback templates
    title_choices = [
        f"{clean_name} 🐉 Epic Dragon World Animation (1080p)",
        f"🐉 {clean_name} · Breathtaking Dragon Animation (HD)",
        f"{clean_name} | Dragon Lapps Epic Fantasy Animation",
        f"🔥 {clean_name} · Ancient Dragon Legends (1080p HD)"
    ]
    title = random.choice(title_choices)

    desc = (
        f"🐉 Witness {clean_name} in stunning 1080p Full HD dragon animation!\n\n"
        "Step into the mythical dragon world where majestic beasts rule the skies, unleash blazing fire, "
        "and command ancient magical realms. Every scene is crafted to bring legendary fantasy to life.\n\n"
        "🔥 Subscribe to Dragon Lapps for daily epic dragon animations and fantasy spectacles!\n"
        "💬 Which mythical dragon is your favorite? Tell us in the comments! 🐉✨\n\n"
        "#dragon #dragonanimation #dragonworld #epicfantasy #dragonlapps #mythicaldragons #firedragon #epicanimation #shorts"
    )

    tags = [
        "dragon", "dragon animation", "dragon world", "epic fantasy", "dragon lapps",
        "fantasy dragons", "dragon fire", "mythical dragons", "epic animation",
        "dragon legends", "fantasy world", "fire dragon", "dragon 3d", "dragon art",
        "ancient dragon", "dragon video", "dragon 1080p", "dragon hd"
    ]

    return title, desc, tags


def run_pipeline(dry_run=False, video_override=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_video_dir = os.path.join(script_dir, "output_videos")
    os.makedirs(output_video_dir, exist_ok=True)

    print("\n" + "=" * 65)
    print(f"      DRAGON LAPPS ({CHANNEL_NAME}) - ANIMATION PUBLISHING PIPELINE")
    print("=" * 65)

    # Step 1: Fetch Video from Google Drive
    if video_override:
        vid_path = video_override
        is_repost = False
    else:
        vid_path, is_repost = fetch_dragon_video(allow_repost=ALLOW_REPOST)

    if not vid_path:
        print("[ERROR] Could not fetch required dragon video asset.")
        return False

    print(f"\n[STEP 1] Video Selected: {os.path.basename(vid_path)} (repost={is_repost})")

    # Step 2: Process Video (watermark removal + 1080p upscale, native duration, native audio)
    safe_name = "".join(c for c in os.path.splitext(os.path.basename(vid_path))[0] if c.isalnum() or c in (" ", "_", "-")).strip()
    final_video_path = os.path.join(output_video_dir, f"DragonLapps_{safe_name}.mp4")

    print(f"\n[STEP 2] Processing Video (Watermark Removal + 1080p Full HD)...")
    success = process_dragon_video(
        input_video=vid_path,
        output_path=final_video_path,
        remove_watermark=True,
        upscale_to_1080p=True
    )

    if not success:
        print("[ERROR] Video processing failed.")
        return False

    # Step 3: Generate Dragon Animation Metadata
    title, desc, tags = generate_dragon_metadata(vid_path)
    print(f"\n[STEP 3] Generated Metadata:")
    print(f"  • Title: {title}")
    print(f"  • Tags: {', '.join(tags[:6])}...")

    if dry_run:
        print(f"\n[DRY RUN] Completed. Processed video saved at: {final_video_path}")
        save_published_entry(vid_path, yt_video_id=None, fb_video_id=None, title=title)
        return True

    # Step 4: Publish to YouTube & Facebook
    video_id = None
    try:
        from publish_youtube import upload_to_youtube
        print(f"\n[STEP 4] Uploading Dragon Animation to YouTube (Film & Animation)...")
        video_id = upload_to_youtube(final_video_path, title, desc, tags=tags)
        if video_id:
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
        print(f"[FACEBOOK NOTE] Facebook upload error: {e_fb}")

    save_published_entry(vid_path, yt_video_id=video_id, fb_video_id=fb_video_id, title=title)

    # Step 5: Clean up output video to save disk space
    if os.path.exists(final_video_path):
        try:
            os.remove(final_video_path)
            print(f"[CLEANUP] Deleted processed video to save disk space: {final_video_path}")
        except Exception:
            pass

    return True if (video_id or fb_video_id) else False


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_pipeline(dry_run=is_dry)
