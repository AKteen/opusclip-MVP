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


def cut_clips(video_path, highlights, job_id):
    os.makedirs(CLIPS_DIR, exist_ok=True)
    clip_urls = []

    for i, (start, end) in enumerate(highlights, 1):
        # ---- SAFE DURATION (NO -to ANYMORE) ----
        duration = max(0.1, float(end) - float(start))

        clip_name = f"{job_id}_clip_{i}.mp4"
        local_clip_path = os.path.join(CLIPS_DIR, clip_name)
        temp_manager.add_temp_file(local_clip_path)

        # ---- STABLE FFmpeg COMMAND ----
        cmd = [
            FFMPEG_PATH,
            "-y",
            "-hide_banner",
            "-loglevel", "warning",

            "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),

            # Safe stream mapping
            "-map", "0:v:0",
            "-map", "0:a?",

            # Video
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",

            # Audio (only if exists)
            "-c:a", "aac",
            "-b:a", "96k",

            # Output safety
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-threads", "1",

            local_clip_path,
        ]

        # Cleanup old stuck FFmpeg jobs (does not need semaphore)
        cleanup_hung_processes()

        with ffmpeg_semaphore:
            process = None
            clip_key = f"{job_id}_clip_{i}"

            try:
                process = run_ffmpeg_with_limits(cmd, timeout=600)
                register_process(clip_key, process)

                stdout, stderr = process.communicate(timeout=600)

                if process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        process.returncode,
                        cmd,
                        stderr=stderr
                    )

            except subprocess.TimeoutExpired:
                if process:
                    kill_process_tree(process.pid)
                raise RuntimeError(f"Clip {i} processing timeout after 10 minutes")

            except subprocess.CalledProcessError as e:
                if e.returncode == -9:
                    raise RuntimeError(
                        "FFmpeg killed by system (out of memory / CPU limits). "
                        "Try shorter clips or smaller videos."
                    )

                stderr_text = ""
                if e.stderr:
                    stderr_text = (
                        e.stderr.decode(errors="ignore")
                        if isinstance(e.stderr, bytes)
                        else str(e.stderr)
                    )

                raise RuntimeError(
                    f"Clip {i} failed "
                    f"(start={start}, duration={duration}, exit={e.returncode}).\n"
                    f"FFmpeg error:\n{stderr_text}"
                )

            except Exception as e:
                raise RuntimeError(f"Clip {i} processing failed: {str(e)}")

            finally:
                unregister_process(clip_key)

        # ---- Upload to S3 ----
        try:
            s3_url = upload_file(
                local_path=local_clip_path,
                s3_key=f"clips/{clip_name}"
            )
            clip_urls.append(s3_url)
        except Exception as e:
            raise RuntimeError(f"Failed to upload clip {i} to S3: {str(e)}")

        # ---- Cleanup ----
        temp_manager.cleanup_file(local_clip_path)

    return clip_urls
