import os
import subprocess
import time

from app.core.storage import upload_file
from app.core.config import FFMPEG_PATH
from app.core.ffmpeg_lock import (
    ffmpeg_semaphore,
    cleanup_hung_processes,
    kill_process_tree,
    register_process,
    unregister_process,
)
from app.core.memory_limiter import run_ffmpeg_with_limits
from app.core.temp_manager import temp_manager

CLIPS_DIR = os.path.join("storage", "clips")


def _run_ffmpeg(cmd, clip_key, env=None):
    process = run_ffmpeg_with_limits(cmd, timeout=600, env=env)
    register_process(clip_key, process)

    try:
        _, stderr = process.communicate(timeout=600)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, cmd, stderr=stderr
            )
    finally:
        unregister_process(clip_key)


def cut_clips(video_path, highlights, job_id):
    os.makedirs(CLIPS_DIR, exist_ok=True)
    clip_urls = []

    for i, (start, end) in enumerate(highlights, 1):
        duration = max(0.1, float(end) - float(start))

        clip_name = f"{job_id}_clip_{i}.mp4"
        local_clip_path = os.path.join(CLIPS_DIR, clip_name)
        temp_manager.add_temp_file(local_clip_path)

        clip_key = f"{job_id}_clip_{i}"
        cleanup_hung_processes()

        # ---------------------------
        # PASS 1️⃣ SAFE STREAM COPY
        # (accurate seek, low memory)
        # ---------------------------
        copy_cmd = [
            FFMPEG_PATH,
            "-y",
            "-hide_banner",
            "-loglevel", "warning",
            "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),
            "-map", "0",
            "-c", "copy",
            local_clip_path,
        ]

        # ---------------------------
        # PASS 2️⃣ SAFE TRANSCODE (AV1)
        # ---------------------------
        transcode_cmd = [
            FFMPEG_PATH,
            "-y",
            "-hide_banner",
            "-loglevel", "warning",
            "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),
            "-map", "0:v:0",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "30",
            "-c:a", "aac",
            "-b:a", "96k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-threads", "1",
            local_clip_path,
        ]

        with ffmpeg_semaphore:
            try:
                _run_ffmpeg(copy_cmd, clip_key)
            except Exception:
                # FORCE dav1d single-thread (ACTUALLY WORKS NOW)
                env = os.environ.copy()
                env["DAV1D_NUM_THREADS"] = "1"

                try:
                    _run_ffmpeg(transcode_cmd, clip_key, env=env)
                except subprocess.CalledProcessError as e:
                    stderr = (
                        e.stderr.decode(errors="ignore")
                        if isinstance(e.stderr, bytes)
                        else str(e.stderr)
                    )
                    raise RuntimeError(
                        f"Clip {i} failed.\nFFmpeg error:\n{stderr}"
                    )

        s3_url = upload_file(
            local_path=local_clip_path,
            s3_key=f"clips/{clip_name}"
        )
        clip_urls.append(s3_url)

        temp_manager.cleanup_file(local_clip_path)

    return clip_urls
