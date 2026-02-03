from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, validator
import uuid
import hashlib
import requests

from app.services.pipeline import run_pipeline
from app.store import jobs

#Developed by Aditya , Github: AKteen

router = APIRouter()

# Configuration
MAX_FILE_SIZE_MB = 500
MAX_CONCURRENT_JOBS = 3

def get_file_size(url: str) -> int:
    try:
        response = requests.head(url, timeout=10)
        content_length = response.headers.get('content-length')
        return int(content_length) if content_length else 0
    except:
        return 0

def count_active_jobs() -> int:
    active_statuses = ["processing", "downloading", "extracting_audio", 
                      "detecting_highlights", "cutting_clips", "uploading"]
    return sum(1 for job in jobs.values() if job.get("status") in active_statuses)

class GenerateRequest(BaseModel):
    video_url: str
    clip_duration: int = 40
    clip_count: int = 5

    # ✅ ANY downloadable URL allowed
    @validator("video_url")
    def validate_video_url(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Video URL is required")
        if not v.startswith("http"):
            raise ValueError("Video URL must be a valid HTTP/HTTPS link")
        return v

    @validator("clip_duration")
    def validate_clip_duration(cls, v):
        if v < 10 or v > 300:
            raise ValueError("Clip duration must be between 10 and 300 seconds")
        return v

    @validator("clip_count")
    def validate_clip_count(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Clip count must be between 1 and 10")
        return v


@router.post("/generate-clips")
def generate_clips(payload: GenerateRequest, background_tasks: BackgroundTasks):
    try:
        # Check concurrent job limit
        if count_active_jobs() >= MAX_CONCURRENT_JOBS:
            raise HTTPException(status_code=429, detail="Server busy. Try again later.")
        
        # Validate file size
        file_size = get_file_size(payload.video_url)
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB allowed.")
        
        # Create deterministic job ID
        request_key = f"{payload.video_url}_{payload.clip_duration}_{payload.clip_count}"
        job_id = hashlib.md5(request_key.encode()).hexdigest()
        
        # Check if job already exists
        if job_id in jobs:
            current_status = jobs[job_id]["status"]
            if current_status in ["processing", "downloading", "extracting_audio", 
                                "detecting_highlights", "cutting_clips", "uploading", "completed"]:
                return {"job_id": job_id, "status": current_status}
            elif current_status == "failed":
                jobs[job_id] = {"status": "processing", "clips": []}
        else:
            jobs[job_id] = {"status": "processing", "clips": []}

        background_tasks.add_task(
            run_pipeline,
            payload.video_url,
            payload.clip_duration,
            payload.clip_count,
            job_id
        )

        return {"job_id": job_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})
