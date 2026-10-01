"""
Dragon Lapps Video Processor
- Watermark / Logo removal in bottom-right corner using high-precision astroid geometry & inpainting
- Auto-upscale to 1080p Full HD (Lanczos + Unsharp) if needed
- Preserves original video duration (NO LOOPING, e.g. 10s video)
- Preserves native audio track
"""
import os
import sys
import json
import subprocess
import cv2
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_media_info(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,codec_name:format=duration",
        "-of", "json", str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    duration = float(data.get("format", {}).get("duration", 0))
    v_stream = next((s for s in data.get("streams", []) if s.get("width")), None)
    width = int(v_stream["width"]) if v_stream else 1920
    height = int(v_stream["height"]) if v_stream else 1080
    return width, height, duration


def is_nvenc_available():
    try:
        res = subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=1:size=64x64:rate=24", "-c:v", "h264_nvenc", "-f", "null", "-"],
            capture_output=True, text=True
        )
        return res.returncode == 0
    except Exception:
        return False


def inpaint_video_watermark(input_video, output_video):
    """
    Removes Google Flow / Gemini AI / AI logo watermarks across all frames
    using high-precision astroid geometry and Telea inpainting.
    """
    cap = cv2.VideoCapture(str(input_video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    p = 0.65
    centers = [
        (int(w * 0.9023), int(h * 0.8264), int(h * 0.050)),
        (int(w * 0.9317), int(h * 0.8750), int(h * 0.052))
    ]

    mask = np.zeros((h, w), dtype=np.uint8)
    kernel = np.ones((5, 5), np.uint8)
    for cx, cy, r in centers:
        y_min, y_max = max(0, cy - r - 15), min(h, cy + r + 15)
        x_min, x_max = max(0, cx - r - 15), min(w, cx + r + 15)
        vy, vx = np.ogrid[y_min:y_max, x_min:x_max]
        vdist = (np.abs(vx - cx) / r) ** p + (np.abs(vy - cy) / r) ** p
        mask_roi = np.zeros((y_max - y_min, x_max - x_min), dtype=np.uint8)
        mask_roi[vdist <= 1.0] = 255
        mask_roi = cv2.dilate(mask_roi, kernel, iterations=1)
        mask[y_min:y_max, x_min:x_max] = np.maximum(mask[y_min:y_max, x_min:x_max], mask_roi)

    nz = cv2.findNonZero(mask)
    if nz is not None:
        bx, by, bw, bh = cv2.boundingRect(nz)
    else:
        bx, by, bw, bh = 0, 0, w, h

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_video), fourcc, fps, (w, h))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        roi_frame = frame[by:by+bh, bx:bx+bw]
        roi_mask = mask[by:by+bh, bx:bx+bw]
        frame[by:by+bh, bx:bx+bw] = cv2.inpaint(roi_frame, roi_mask, 3, cv2.INPAINT_TELEA)
        out.write(frame)

    cap.release()
    out.release()
    return output_video


def process_dragon_video(input_video, output_path, remove_watermark=True, upscale_to_1080p=True):
    """
    Processes dragon animation video without looping:
    1. Removes bottom-right logo / watermark via inpainting
    2. Upscales to 1080p Full HD (if needed)
    3. Preserves original duration (e.g. 10 seconds) and native audio track
    """
    print("\n" + "=" * 60)
    print("PROCESSING DRAGON ANIMATION VIDEO (NO LOOP - NATIVE DURATION)")
    print("=" * 60)
    print(f"  Input: {os.path.basename(input_video)}")
    print(f"  Output: {output_path}")

    w, h, duration = get_media_info(input_video)
    print(f"  Resolution: {w}x{h} | Duration: {duration:.2f}s")

    temp_inpaint = os.path.join(SCRIPT_DIR, "temp_inpaint.mp4")

    source_video = input_video
    if remove_watermark:
        print("[VIDEO] Removing logo / watermark via astroid inpainting...")
        inpaint_video_watermark(input_video, temp_inpaint)
        source_video = temp_inpaint

    # Video filters for upscaling
    filters = []
    if upscale_to_1080p and (w < 1920 or h < 1080):
        print(f"[VIDEO] Auto-upscaling from {w}x{h} to 1920x1080 Full HD (Lanczos + Unsharp)...")
        filters.append("scale=1920:1080:flags=lanczos+accurate_rnd")
        filters.append("unsharp=5:5:0.8:5:5:0.0")

    vf_str = ",".join(filters) if filters else "null"

    # Codec selection
    if is_nvenc_available():
        vcodec_args = ["-c:v", "h264_nvenc", "-cq", "19", "-b:v", "14M"]
    else:
        vcodec_args = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast"]

    # Assemble final video with native audio from original video
    cmd = [
        "ffmpeg", "-y",
        "-i", str(source_video),
        "-i", str(input_video),
        "-vf", vf_str,
        "-map", "0:v:0",
        "-map", "1:a?",
        *vcodec_args,
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path)
    ]

    print(f"[VIDEO] Rendering 1080p output ({duration:.1f}s)...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        cmd_cpu = [
            "ffmpeg", "-y",
            "-i", str(source_video),
            "-i", str(input_video),
            "-vf", vf_str,
            "-map", "0:v:0",
            "-map", "1:a?",
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path)
        ]
        subprocess.run(cmd_cpu, check=True)

    # Cleanup temporary file
    if os.path.exists(temp_inpaint):
        try:
            os.remove(temp_inpaint)
        except Exception:
            pass

    print(f"[SUCCESS] Dragon animation video ready: {output_path}")
    return True
