from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from typing import List, Optional
import requests
from dotenv import load_dotenv

from services.job_manager import create_job, update_job_status, get_job_status
from services.tts import generate_audio
from services.alignment import get_word_timings
from services.video_render import render_video

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files for CSS/JS
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class SceneItem(BaseModel):
    image_name: str
    text: Optional[str] = ""


class GenerateRequest(BaseModel):
    scenes: Optional[List[SceneItem]] = None
    image_name: Optional[str] = None
    text: Optional[str] = ""
    style: Optional[str] = "sticker"  # "sticker" or "aged_paper"


# Root route — serve index.html
@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/sticker")
async def sticker_page():
    sticker_path = os.path.join(STATIC_DIR, "sticker.html")
    with open(sticker_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)



@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PNG/JPG allowed.")

    file.file.seek(0, 2)
    size = file.file.tell()
    if size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    file.file.seek(0)

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(TEMP_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    return {"image_name": filename}


# Human-readable step labels for the frontend
STEP_LABELS = {
    "pending": "Waiting in queue...",
    "generating_audio": "Generating audio...",
    "aligning": "Aligning words to audio...",
    "rendering": "Rendering video...",
    "completed": "Done!",
    "failed": "Generation failed",
}


def run_pipeline(job_id: str, scenes: list, style: str = "sticker"):
    try:
        colab_url = os.getenv("COLAB_URL")
        space = os.getenv("WHISPERX_SPACE")
        if not colab_url and not space:
            raise ValueError("Neither COLAB_URL nor WHISPERX_SPACE set in .env")

        output_path = os.path.join(OUTPUTS_DIR, f"{job_id}.mp4")
        num_scenes = len(scenes)

        scenes_data = []
        for i, scene in enumerate(scenes):
            image_name = scene.image_name
            text = (scene.text or "").strip()
            image_path = os.path.join(TEMP_DIR, image_name)

            # Audio & Alignment takes up 0% - 50% total progress
            scene_progress_base = int((i / num_scenes) * 45)

            if text:
                audio_path = os.path.join(TEMP_DIR, f"{job_id}_scene_{i}.mp3")
                update_job_status(job_id, f"generating_audio (scene {i+1})", progress=scene_progress_base + 5)
                generate_audio(text, audio_path)

                update_job_status(job_id, f"aligning (scene {i+1})", progress=scene_progress_base + 15)
                timings = get_word_timings(audio_path, colab_url, text=text)
            else:
                # Textless scene — 2 seconds static display
                audio_path = None
                timings = {"words": []}

            scenes_data.append({
                "image_path": image_path,
                "audio_path": audio_path,
                "word_timings": timings,
                "text": text
            })

        update_job_status(job_id, "rendering", progress=50)

        def progress_cb(pct):
            update_job_status(job_id, "rendering", progress=pct)

        render_video(scenes_data, output_path, style=style, progress_callback=progress_cb)

        update_job_status(job_id, "completed", progress=100, output_path=output_path)
    except Exception as e:
        update_job_status(job_id, "failed", progress=0, error=str(e))
    finally:
        # Cleanup temporary audio files created for this job
        for i in range(len(scenes)):
            temp_audio = os.path.join(TEMP_DIR, f"{job_id}_scene_{i}.mp3")
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except Exception:
                    pass


@app.post("/api/generate")
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    if req.scenes:
        scenes = req.scenes
    elif req.image_name:
        scenes = [SceneItem(image_name=req.image_name, text=req.text or "")]
    else:
        raise HTTPException(status_code=400, detail="Must provide scenes or image_name")

    # Verify all images exist
    for scene in scenes:
        image_path = os.path.join(TEMP_DIR, scene.image_name)
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail=f"Image {scene.image_name} not found. Upload first.")

    style = req.style or "sticker"
    if style not in ("sticker", "aged_paper"):
        raise HTTPException(status_code=400, detail="Invalid style. Use 'sticker' or 'aged_paper'.")

    job_id = create_job()
    background_tasks.add_task(run_pipeline, job_id, scenes, style)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def status(job_id: str):
    job = get_job_status(job_id)
    job["step"] = STEP_LABELS.get(job.get("status", ""), "Processing...")
    return job


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job = get_job_status(job_id)
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    return FileResponse(
        job["output_path"],
        media_type="video/mp4",
        filename=f"{job_id}.mp4"
    )


@app.get("/api/health-colab")
async def health_colab():
    space = os.getenv("WHISPERX_SPACE")
    if space:
        return {"status": "online"}

    colab_url = os.getenv("COLAB_URL")
    if not colab_url:
        return {"status": "offline", "message": "COLAB_URL not configured"}

    try:
        resp = requests.get(f"{colab_url.rstrip('/')}/health", timeout=5)
        if resp.status_code == 200:
            return {"status": "online"}
        return {"status": "offline"}
    except Exception:
        return {"status": "offline", "message": "Could not connect to Colab"}

try:
    import gradio as gr
    with gr.Blocks(title="Sticker Video Generator") as demo:
        gr.HTML("<iframe src='/static/index.html' style='width:100%; height:900px; border:none;'></iframe>")

    app = gr.mount_gradio_app(app, demo, path="/")
except Exception as e:
    pass


