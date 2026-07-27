import json
import subprocess
import os
import math
import shutil
from PIL import Image


def get_dominant_color(image_path: str) -> str:
    """Extract dominant vibrant color from sticker image."""
    try:
        img = Image.open(image_path).convert('RGBA')
        img = img.resize((50, 50))
        
        colors = []
        for x in range(img.width):
            for y in range(img.height):
                r, g, b, a = img.getpixel((x, y))
                if a < 128:
                    continue
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                if 40 <= brightness <= 220:
                    colors.append((r, g, b))
                    
        if not colors:
            return "#00E5FF"
            
        from collections import Counter
        most_common = Counter(colors).most_common(1)[0][0]
        r, g, b = most_common
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception as e:
        print(f"Color extraction error: {e}")
        return "#00E5FF"


def align_original_words_with_timestamps(original_text: str, whisper_words: list):
    """
    Guarantees 100% exact spelling from user input (preserving English/Latin letters and Arabic mixed text)
    while mapping the speech timing boundaries from WhisperX or fallback audio durations.
    """
    import re
    orig_words = [w.strip() for w in re.split(r'\s+', original_text) if w.strip()]
    if not orig_words:
        return []
    
    if not whisper_words:
        return [{"word": w, "start": i * 0.4, "end": (i + 1) * 0.4} for i, w in enumerate(orig_words)]

    # If whisper_words is a dict containing 'words'
    if isinstance(whisper_words, dict):
        whisper_words = whisper_words.get("words", [])

    total_duration = 5.0
    if whisper_words and isinstance(whisper_words, list) and len(whisper_words) > 0:
        last_item = whisper_words[-1]
        if isinstance(last_item, dict):
            total_duration = last_item.get("end", 5.0)

    result = []
    num_orig = len(orig_words)
    num_whisp = len(whisper_words) if isinstance(whisper_words, list) else 0

    for i, word in enumerate(orig_words):
        if num_whisp > 0:
            whisp_idx = min(int((i / num_orig) * num_whisp), num_whisp - 1)
            w_obj = whisper_words[whisp_idx] if isinstance(whisper_words[whisp_idx], dict) else {}
            start = w_obj.get("start", (i / num_orig) * total_duration)
            end = w_obj.get("end", ((i + 1) / num_orig) * total_duration)
        else:
            start = (i / num_orig) * total_duration
            end = ((i + 1) / num_orig) * total_duration

        if end <= start:
            end = start + 0.2
            
        # Always output the EXACT original user word string
        result.append({
            "word": word,
            "start": start,
            "end": end
        })
        
    return result


def _ffmpeg_silent_scene(image_path: str, out_path: str, duration: float = 2.0) -> bool:
    """Render a static image as video via FFmpeg directly — ~2s, no Chromium needed."""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", os.path.abspath(image_path),
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black",
            os.path.abspath(out_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"FFmpeg silent scene error: {e}")
        return False


def _ffmpeg_concat(video_paths: list, out_path: str) -> bool:
    """Concatenate multiple MP4 files into one using FFmpeg concat demuxer."""
    try:
        list_file = out_path + ".concat.txt"
        with open(list_file, "w") as f:
            for p in video_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            os.path.abspath(out_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        try:
            os.remove(list_file)
        except Exception:
            pass
        return result.returncode == 0
    except Exception as e:
        print(f"FFmpeg concat error: {e}")
        return False


def render_video(scenes_data: list, output_path: str, style: str = "sticker", progress_callback=None):
    """
    Render all scenes via Remotion (gradient preserved for every scene).
    Speed optimizations: /tmp asset symlinking, /tmp props, Node max memory, Chromium fast flags.
    """
    remotion_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "remotion")
    remotion_public = os.path.join(remotion_dir, "public")

    # --- OPTIMIZATION 1: Route public/temp I/O through /tmp to bypass Drive FUSE latency ---
    if os.name != "nt":
        tmp_assets = "/tmp/remotion_public_temp"
        remotion_public_temp = tmp_assets
        drive_link = os.path.join(remotion_public, "temp")
        # Recreate /tmp assets dir fresh
        if os.path.exists(tmp_assets):
            shutil.rmtree(tmp_assets, ignore_errors=True)
        os.makedirs(tmp_assets, exist_ok=True)
        # Create/refresh symlink: remotion/public/temp → /tmp/remotion_public_temp
        if os.path.islink(drive_link):
            os.unlink(drive_link)
        elif os.path.exists(drive_link):
            shutil.rmtree(drive_link, ignore_errors=True)
        try:
            os.symlink(tmp_assets, drive_link)
        except Exception as e:
            print(f"Symlink warning (falling back to Drive): {e}")
            remotion_public_temp = drive_link
            os.makedirs(remotion_public_temp, exist_ok=True)
    else:
        remotion_public_temp = os.path.join(remotion_public, "temp")
        if os.path.exists(remotion_public_temp):
            try:
                shutil.rmtree(remotion_public_temp)
            except Exception:
                pass
        os.makedirs(remotion_public_temp, exist_ok=True)

    scenes_props = []

    for scene in scenes_data:
        image_path = scene["image_path"]
        audio_path = scene.get("audio_path")
        word_timings = scene.get("word_timings", {})
        original_text = scene.get("text", "")
        
        image_name = os.path.basename(image_path)
        target_image_path = os.path.join(remotion_public_temp, image_name)
        shutil.copy(image_path, target_image_path)

        dominant_color = get_dominant_color(image_path)

        if audio_path and os.path.exists(audio_path):
            audio_name = os.path.basename(audio_path)
            target_audio_path = os.path.join(remotion_public_temp, audio_name)
            shutil.copy(audio_path, target_audio_path)
            audio_src = f"temp/{audio_name}"

            raw_words = word_timings.get('words', [])
            
            # Use original user text matched to timings for 100% spelling precision
            aligned_words = align_original_words_with_timestamps(original_text, raw_words)
            
            converted_words = []
            for w in aligned_words:
                converted_words.append({
                    "word": w.get("word", "").strip(),
                    "startMs": int(w.get("start", 0) * 1000),
                    "endMs": int(w.get("end", 0) * 1000),
                })
            
            if converted_words:
                last_end_ms = converted_words[-1]["endMs"]
            else:
                last_end_ms = 5000
            
            duration_in_frames = max(30, math.ceil((last_end_ms / 1000) * 30) + 15)
        else:
            # Textless scene — static 2 seconds (60 frames)
            audio_src = ""
            converted_words = []
            duration_in_frames = 60

        scenes_props.append({
            "audioSrc": audio_src,
            "imageSrc": f"temp/{image_name}",
            "wordTimings": converted_words,
            "durationInFrames": duration_in_frames,
            "captionGlowColor": dominant_color,
            "backgroundColors": {
                "color": dominant_color,
                "dark": "#0a0a0a"
            }
        })

    props = {"scenes": scenes_props}

    # --- OPTIMIZATION 2: Write props to /tmp instead of Drive ---
    if os.name != "nt":
        props_file = f"/tmp/remotion_props_{os.path.basename(output_path)}.json"
    else:
        props_file = output_path + ".props.json"
    with open(props_file, 'w', encoding='utf-8') as f:
        json.dump(props, f, ensure_ascii=False)

    # Select Remotion composition based on style
    composition_id = "AgedPaperVideo" if style == "aged_paper" else "StickerVideo"

    # Use fast local /tmp on Linux (Colab) to avoid Google Drive FUSE I/O latency
    if os.name != "nt":
        remotion_tmp = "/tmp/remotion_fast_tmp"
    else:
        remotion_tmp = os.path.join(os.path.dirname(remotion_dir), "remotion_tmp")

    # Clean old temporary files to keep /tmp fresh and free
    if os.path.exists(remotion_tmp):
        try:
            shutil.rmtree(remotion_tmp, ignore_errors=True)
        except Exception:
            pass
    os.makedirs(remotion_tmp, exist_ok=True)

    env = os.environ.copy()
    env["TMPDIR"] = remotion_tmp
    env["TEMP"] = remotion_tmp
    env["TMP"] = remotion_tmp
    # --- OPTIMIZATION 3: Give Node.js more memory to prevent GC pause stalls ---
    env["NODE_OPTIONS"] = "--max-old-space-size=4096"

    gl_option = "angle" if os.name == "nt" else "swangle"

    # Find executable: direct node JS file, global remotion executable, or npx fallback
    remotion_js = os.path.join(remotion_dir, "node_modules", "@remotion", "cli", "bin", "remotion.js")
    if not os.path.exists(remotion_js):
        remotion_js = os.path.join(remotion_dir, "node_modules", "remotion", "bin", "remotion.js")

    if os.path.exists(remotion_js):
        base_cmd = ["node", remotion_js]
    elif shutil.which("remotion"):
        base_cmd = ["remotion"]
    else:
        base_cmd = ["npx.cmd" if os.name == "nt" else "npx", "remotion"]

    # Render directly to local /tmp file first to avoid Drive FUSE latency
    if os.name != "nt":
        fast_output_path = f"/tmp/fast_render_{os.path.basename(output_path)}"
    else:
        fast_output_path = output_path + ".fast.mp4"

    cmd = base_cmd + [
        "render",
        composition_id,
        "--props", os.path.abspath(props_file),
        os.path.abspath(fast_output_path),
        "--codec", "h264",
        "--preset", "ultrafast",
        "--crf", "28",
        "--concurrency", "2",
        "--width", "720",
        "--height", "1280",
        "--pixel-format", "yuv420p",
        "--gl", gl_option,
        # Sandbox & security (required for rootless Colab)
        "--chromium-flag=--no-sandbox",
        "--chromium-flag=--disable-setuid-sandbox",
        "--chromium-flag=--disable-dev-shm-usage",
        # --- OPTIMIZATION 4: Chromium startup speed flags (zero quality impact) ---
        "--chromium-flag=--disable-extensions",
        "--chromium-flag=--disable-background-networking",
        "--chromium-flag=--disable-sync",
        "--chromium-flag=--disable-translate",
        "--chromium-flag=--no-first-run",
        "--chromium-flag=--disable-default-apps",
        "--chromium-flag=--disable-component-update",
        "--chromium-flag=--disable-domain-reliability",
        "--chromium-flag=--safebrowsing-disable-auto-update",
        "--chromium-flag=--metrics-recording-only",
        "--chromium-flag=--disable-client-side-phishing-detection",
        "--chromium-flag=--disable-hang-monitor"
    ]

    # Use system installed Chromium on Linux/Colab to bypass Google Drive FUSE permission denied
    browser_exe = os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    if not browser_exe or not os.path.exists(browser_exe):
        for candidate in ["/usr/bin/chromium-browser", "/usr/bin/chromium", "/usr/bin/google-chrome"]:
            if os.path.exists(candidate):
                browser_exe = candidate
                break

    if browser_exe and os.path.exists(browser_exe):
        cmd.extend(["--browser-executable", browser_exe])

    process = subprocess.Popen(
        cmd,
        cwd=remotion_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env
    )

    import re
    last_rendered_percent = 50
    output_lines = []

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            output_lines.append(line.strip())
            matches = re.findall(r'(\d{1,3})%', line)
            if matches and progress_callback:
                try:
                    render_percent = int(matches[-1])
                    if 0 <= render_percent <= 100:
                        # Smooth progress: render maps linearly to 50% -> 95% for realistic visual progress
                        total_percent = 50 + int((render_percent / 100.0) * 45)
                        if total_percent != last_rendered_percent:
                            last_rendered_percent = total_percent
                            progress_callback(total_percent)
                except ValueError:
                    pass

    if process.returncode != 0:
        error_summary = "\n".join(output_lines[-15:]) if output_lines else "Unknown error"
        raise RuntimeError(f"Remotion render failed (code {process.returncode}):\n{error_summary}")

    # Move completed video instantly from local /tmp to output path
    try:
        shutil.move(fast_output_path, os.path.abspath(output_path))
    except Exception as e:
        if os.path.exists(fast_output_path):
            shutil.copy(fast_output_path, os.path.abspath(output_path))
