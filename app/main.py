from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from fastapi.staticfiles import StaticFiles
from app.store import jobs
from fastapi import HTTPException
from app.core.temp_manager import temp_manager
from app.core.request_limiter import request_limiter

app = FastAPI(title="Celer Clips MVP")

# Add request limiter middleware
app.middleware("http")(request_limiter)

# Cleanup old files on startup
temp_manager.cleanup_old_files("storage/uploads", max_age_hours=24)
temp_manager.cleanup_old_files("storage/audio", max_age_hours=24)
temp_manager.cleanup_old_files("storage/clips", max_age_hours=24)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


app.mount(
    "/clips",
    StaticFiles(directory="storage/clips"),
    name="clips"
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Celer Clips MVP API is running"}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail={"error": "Job not found", "job_id": job_id})
    
    job_data = jobs[job_id]
    response = {"job_id": job_id, "status": job_data["status"]}
    
    if job_data["status"] == "completed":
        response.update({"video": job_data.get("video"), "clips": job_data.get("clips", [])})
    elif job_data["status"] == "failed":
        response.update({"error": job_data.get("error", "Unknown error")})
    
    return response