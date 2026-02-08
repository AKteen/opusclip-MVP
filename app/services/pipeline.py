# Initial core media processing pipeline and MVP created by Aditya (Github : AKteen)

import logging
import time
import os

from app.services.downloader import download_video
from app.services.audio import extract_audio
from app.services.highlights import detect_highlights
from app.services.clipper import cut_clips
from app.core.storage import upload_file
from app.core.media_utils import get_video_duration
from app.store import jobs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline(video_url, clip_duration, clip_count, job_id):
    start_time = time.time()
    logger.info(f"[{job_id}] Pipeline started for URL: {video_url}")

    try:
        # ---------------------------
        # 1️⃣ Download media
        # ---------------------------
        jobs[job_id] = {"status": "downloading", "progress": 10}

        logger.info(f"[{job_id}] Step 1/6: Starting video download...")
        step_start = time.time()
        paths = download_video(video_url, job_id)
        logger.info(
            f"[{job_id}] Step 1/6: Media downloaded in "
            f"{time.time() - step_start:.2f}s - Paths: {paths}"
        )

        # ---------------------------
        # 🔒 Pre-flight validation
        # ---------------------------
        video_duration = get_video_duration(paths["video"])
        logger.info(f"[{job_id}] Video duration detected: {video_duration:.2f}s")

        if video_duration <= 1.0:
            raise RuntimeError("Video too short or invalid to process")

        # ---------------------------
        # 2️⃣ Extract audio
        # ---------------------------
        jobs[job_id] = {"status": "extracting_audio", "progress": 25}

        logger.info(f"[{job_id}] Step 2/6: Starting audio extraction...")
        step_start = time.time()
        audio_wav = extract_audio(paths["video"], job_id)
        logger.info(
            f"[{job_id}] Step 2/6: Audio extracted in "
            f"{time.time() - step_start:.2f}s - Audio file: {audio_wav}"
        )

        # ---------------------------
        # 3️⃣ Detect highlights
        # ---------------------------
        jobs[job_id] = {"status": "detecting_highlights", "progress": 40}

        logger.info(f"[{job_id}] Step 3/6: Starting AI highlight detection...")
        step_start = time.time()
        highlights = detect_highlights(audio_wav, clip_duration, clip_count)
        logger.info(
            f"[{job_id}] Step 3/6: Highlight detection completed in "
            f"{time.time() - step_start:.2f}s - Found {len(highlights)} highlights"
        )

        # Audio cleanup ASAP
        try:
            os.remove(audio_wav)
            logger.info(f"[{job_id}] Deleted audio file")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to delete audio file: {e}")

        if not highlights:
            raise RuntimeError("No valid highlights detected from audio")

        for i, (s, e) in enumerate(highlights, 1):
            logger.info(
                f"[{job_id}] Highlight {i}: {s}s → {e}s "
                f"(duration: {round(e - s, 2)}s)"
            )

        # ---------------------------
        # 4️⃣ Cut clips
        # ---------------------------
        jobs[job_id] = {"status": "cutting_clips", "progress": 60}

        logger.info(f"[{job_id}] Step 4/6: Starting video clipping (ffmpeg)...")
        step_start = time.time()
        clip_urls = cut_clips(
            video_path=paths["video"],
            highlights=highlights,
            job_id=job_id
        )
        logger.info(
            f"[{job_id}] Step 4/6: Video clipping completed in "
            f"{time.time() - step_start:.2f}s - Generated {len(clip_urls)} clips"
        )

        # ---------------------------
        # 5️⃣ Upload original video
        # ---------------------------
        jobs[job_id] = {"status": "uploading", "progress": 80}

        logger.info(f"[{job_id}] Step 5/6: Starting S3 upload...")
        step_start = time.time()
        video_s3_url = upload_file(
            local_path=paths["video"],
            s3_key=f"videos/{job_id}.mp4"
        )
        logger.info(
            f"[{job_id}] Step 5/6: Original video uploaded in "
            f"{time.time() - step_start:.2f}s - S3 URL: {video_s3_url}"
        )

        try:
            os.remove(paths["video"])
            logger.info(f"[{job_id}] Deleted original video file")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to delete video file: {e}")

        # ---------------------------
        # 6️⃣ Finalize job
        # ---------------------------
        jobs[job_id] = {
            "status": "completed",
            "progress": 100,
            "video": video_s3_url,
            "clips": clip_urls
        }

        total_time = time.time() - start_time
        logger.info(
            f"[{job_id}] Pipeline completed successfully in "
            f"{total_time:.2f}s"
        )

    except Exception as e:
        logger.error(
            f"[{job_id}] Pipeline failed: {str(e)}",
            exc_info=True
        )

        # Cleanup on failure
        try:
            if 'paths' in locals() and os.path.exists(paths.get("video", "")):
                os.remove(paths["video"])
        except:
            pass

        try:
            if 'audio_wav' in locals() and os.path.exists(audio_wav):
                os.remove(audio_wav)
        except:
            pass

        error_message = str(e)
        if "killed by system" in error_message.lower():
            error_message = (
                "Video processing failed due to resource limits. "
                "Try a smaller video or shorter clips."
            )
        elif "timeout" in error_message.lower():
            error_message = (
                "Video processing timed out. "
                "Try a shorter video or reduce clip count."
            )

        jobs[job_id] = {
            "status": "failed",
            "error": error_message
        }

        logger.info(f"[{job_id}] Job marked as failed, API remains stable")
