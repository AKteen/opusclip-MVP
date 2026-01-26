from app.services.downloader import download_video
from app.services.audio import extract_audio
from app.services.highlights import detect_highlights
from app.services.clipper import cut_clips
from app.core.storage import upload_file
from app.store import jobs


def run_pipeline(video_url, clip_duration, clip_count, job_id):
    print(f"[{job_id}] Pipeline started")

    # 1️⃣ Download media locally
    paths = download_video(video_url, job_id)
    print(f"[{job_id}] Media downloaded")

    # 2️⃣ Extract audio from video
    audio_wav = extract_audio(paths["video"], job_id)
    print(f"[{job_id}] Audio extracted")

    # 3️⃣ AI highlight detection
    print(f"[{job_id}] Running AI highlight detection...")
    highlights = detect_highlights(
        audio_wav,
        clip_duration,
        clip_count
    )

    for i, (s, e) in enumerate(highlights, 1):
        print(f"[AI] Clip {i}: {s}s → {e}s (high audio energy)")

    # 4️⃣ Cut clips (VIDEO + AUDIO)
    print(f"[{job_id}] Clipping the video...")
    clip_urls = cut_clips(
    video_path=paths["video"],
    highlights=highlights,
    job_id=job_id
)


    print(f"[{job_id}] Generated {len(clip_urls)} clips")

    # 5️⃣ Upload original video to S3
    video_s3_url = upload_file(
        local_path=paths["video"],
        s3_key=f"videos/{job_id}.mp4"
    )
    print(f"[{job_id}] Original video uploaded")

    # 6️⃣ Mark job completed
    jobs[job_id] = {
        "status": "completed",
        "video": video_s3_url,
        "clips": clip_urls
    }

    print(f"[{job_id}] Pipeline complete")
