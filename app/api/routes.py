from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, validator
import uuid

from app.services.pipeline import run_pipeline
from app.store import jobs

router = APIRouter()

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
        job_id = str(uuid.uuid4())

        jobs[job_id] = {
            "status": "processing",
            "clips": []
        }

        background_tasks.add_task(
            run_pipeline,
            payload.video_url,
            payload.clip_duration,
            payload.clip_count,
            job_id
        )

        return {
            "job_id": job_id,
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
