import uuid
from typing import Dict, Any

jobs: Dict[str, Dict[str, Any]] = {}

def create_job() -> str:
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "progress": 0, "output_path": None, "error": None}
    return job_id

def update_job_status(job_id: str, status: str, progress: int = None, output_path: str = None, error: str = None):
    if job_id in jobs:
        jobs[job_id]["status"] = status
        if progress is not None:
            jobs[job_id]["progress"] = progress
        if output_path:
            jobs[job_id]["output_path"] = output_path
        if error:
            jobs[job_id]["error"] = error

def get_job_status(job_id: str) -> Dict[str, Any]:
    job = jobs.get(job_id)
    if not job:
        return {"status": "not_found", "progress": 0}
    return {
        "status": job.get("status", "pending"),
        "progress": job.get("progress", 0),
        "output_path": job.get("output_path"),
        "error": job.get("error")
    }
