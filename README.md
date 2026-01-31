# Celer Clips
Live On ; marketingautoclips-production.up.railway.app

# 🎬 Video Highlight & Clip Generation MVP

A backend MVP that processes long-form videos and automatically generates short highlight clips using audio energy analysis and FFmpeg.  
Designed to work via API and integrate cleanly with automation tools like Make.com.

---

## 🚀 Overview

This project provides an end-to-end media processing pipeline that:

- Accepts a downloadable video URL (Dropbox / Drive / S3 / direct links)
- Downloads and processes the video asynchronously
- Extracts audio and detects high-energy segments
- Cuts multiple short clips using FFmpeg
- Uploads generated clips to Amazon S3
- Returns clip URLs via a polling-based API

The system is intentionally designed as an MVP: simple, debuggable, and production-adjacent, while remaining extensible for future AI layers.

---

## 🎯 Intended Use

- MVP validation for video clipping products
- Automation workflows using Make.com
- Internal tools for short-form content generation
- Founders testing video-to-clips pipelines before scaling

---

## 🏗️ Architecture & Processing Flow

### High-level flow

Client / Make.com  
→ POST `/generate-clips`  
→ Immediate response with `job_id`  
→ Background processing pipeline  
→ GET `/jobs/{job_id}` (polling)  
→ Clip URLs returned when complete

### Processing steps

1. Download video locally
2. Extract audio using FFmpeg
3. Load audio and detect highlight timestamps
4. Cut video clips using FFmpeg seek-based slicing
5. Upload clips to S3
6. Clean up local video and audio files

---

## 🧰 Tech Stack

### Backend
- Python 3.11
- FastAPI
- Uvicorn

### Media
- FFmpeg
- Librosa
- NumPy

### Storage
- Amazon S3

### Deployment
- Docker
- Tested on Render and Railway
- Portable to EC2 / ECS

### Automation
- Make.com (HTTP + router-based polling)

---

## 📡 API Endpoints

### Generate clips

POST `/generate-clips`

```json
{
  "video_url": "https://downloadable-video-link.mp4",
  "clip_duration": 40,
  "clip_count": 5
}
````

# Response


```
{
  "job_id": "uuid",
  "status": "processing"
}
```

Get job status

```
GET /jobs/{job_id}
```

While processing:

```
{
  "status": "processing"
}
```

when completed: 

```
{
  "status": "completed",
  "video": "s3-original-video-url",
  "clips": [
    "s3-clip-url-1",
    "s3-clip-url-2"
  ]
}
```

# Make.com Integration (Recommended)

-HTTP (POST) → /generate-clips

-Store job_id

-HTTP (GET) → /jobs/{job_id}

-Router:

-Route A: status == completed

-Route B: status != completed

-Route B:

-Sleep (10–20 seconds)

-HTTP (GET) /jobs/{job_id}

-Loop back to router

-Route A:

-Parse JSON

-Iterate clip URLs

-Store in Airtable / DB / CMS

-Avoid aggressive repeaters. Use delay + router polling only.


# Local Development Requirements

Python 3.11+

FFmpeg installed and available in PATH

AWS credentials for S3 uploads

Run locally
uvicorn app.main:app --reload


Swagger UI:

```
http://localhost:8000/docs
```
# Local Development
Requirements

Python 3.11+

FFmpeg installed and available in PATH

AWS credentials for S3 uploads

Run locally
uvicorn app.main:app --reload


Swagger UI:
```
http://localhost:8000/docs
```

# Known MVP Constraints

Single-job-at-a-time processing

Large files require sufficient RAM

Audio-based highlight detection only

Not true streaming or chunk-based processing

# Planned Improvements

Streaming / chunk-based processing

Semantic highlight detection (LLMs)

Distributed workers (SQS / ECS / Celery)

Signed upload URLs

Parallel clip generation


# Authorship

Initial MVP backend, processing pipeline, and deployment implemented by Aditya (Github : AKteen).

# License

Internal MVP usage. Licensing TBD.


