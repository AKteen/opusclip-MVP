

# Initial core media processing pipeline and MVP created by Aditya (Github : AKteen)

import logging
import time
import os

from app.services.downloader import download_video
from app.services.audio import extract_audio
from app.services.highlights import detect_highlights
from app.services.clipper import cut_clips
from app.core.storage import upload_file
from app.store import jobs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_pipeline(video_url, clip_duration, clip_count, job_id):
    start_time = time.time()
    logger.info(f"[{job_id}] Pipeline started for URL: {video_url}")
    
    try:
        # Update job status
        jobs[job_id] = {"status": "downloading", "progress": 10}
        
        # 1️⃣ Download media locally
        logger.info(f"[{job_id}] Step 1/6: Starting video download...")
        step_start = time.time()
        paths = download_video(video_url, job_id)
        logger.info(f"[{job_id}] Step 1/6: Media downloaded in {time.time() - step_start:.2f}s - Paths: {paths}")
        
        # Update job status
        jobs[job_id] = {"status": "extracting_audio", "progress": 25}
        
        # 2️⃣ Extract audio from video
        logger.info(f"[{job_id}] Step 2/6: Starting audio extraction...")
        step_start = time.time()
        audio_wav = extract_audio(paths["video"], job_id)
        logger.info(f"[{job_id}] Step 2/6: Audio extracted in {time.time() - step_start:.2f}s - Audio file: {audio_wav}")
        
        # Update job status
        jobs[job_id] = {"status": "detecting_highlights", "progress": 40}
        
        # 3️⃣ AI highlight detection
        logger.info(f"[{job_id}] Step 3/6: Starting AI highlight detection...")
        step_start = time.time()
        highlights = detect_highlights(audio_wav, clip_duration, clip_count)
        logger.info(f"[{job_id}] Step 3/6: Highlight detection completed in {time.time() - step_start:.2f}s - Found {len(highlights)} highlights")
        

        try:
            os.remove(audio_wav)
            logger.info(f"[{job_id}] Deleted audio file")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to delete audio file: {e}")

        jobs[job_id] = {"status": "cutting_clips", "progress": 65}


        for i, (s, e) in enumerate(highlights, 1):
            logger.info(f"[{job_id}] Highlight {i}: {s}s → {e}s (duration: {e-s}s)")
        
        # Update job status
        jobs[job_id] = {"status": "cutting_clips", "progress": 60}
        
        # 4️⃣ Cut clips (VIDEO + AUDIO)
        logger.info(f"[{job_id}] Step 4/6: Starting video clipping (this uses ffmpeg)...")
        step_start = time.time()
        clip_urls = cut_clips(
            video_path=paths["video"],
            highlights=highlights,
            job_id=job_id
        )
        logger.info(f"[{job_id}] Step 4/6: Video clipping completed in {time.time() - step_start:.2f}s - Generated {len(clip_urls)} clips")
        
        # Update job status
        jobs[job_id] = {"status": "uploading", "progress": 80}
        
        # 5️⃣ Upload original video to S3
        logger.info(f"[{job_id}] Step 5/6: Starting S3 upload...")
        step_start = time.time()
        video_s3_url = upload_file(
            local_path=paths["video"],
            s3_key=f"videos/{job_id}.mp4"
        )
        logger.info(f"[{job_id}] Step 5/6: Original video uploaded in {time.time() - step_start:.2f}s - S3 URL: {video_s3_url}")
        


        try:
            os.remove(paths["video"])
            logger.info(f"[{job_id}] Deleted original video file")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to delete video file: {e}")




        # 6️⃣ Mark job completed
        logger.info(f"[{job_id}] Step 6/6: Finalizing job...")
        jobs[job_id] = {
            "status": "completed",
            "progress": 100,
            "video": video_s3_url,
            "clips": clip_urls
        }
        
        total_time = time.time() - start_time
        logger.info(f"[{job_id}] Pipeline completed successfully in {total_time:.2f}s")
        
    except Exception as e:
        logger.error(f"[{job_id}] Pipeline failed: {str(e)}", exc_info=True)
        jobs[job_id] = {
            "status": "failed",
            "error": str(e)
        }
        raise
