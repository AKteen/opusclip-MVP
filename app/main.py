from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from fastapi.staticfiles import StaticFiles
from app.store import jobs
from fastapi import HTTPException

app = FastAPI(title="Celer Clips MVP")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]