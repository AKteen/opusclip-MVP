import os
import subprocess
from app.core.storage import upload_file
from app.core.config import FFMPEG_PATH
from app.core.ffmpeg_lock import ffmpeg_semaphore, active_processes, cleanup_hung_processes
from app.core.memory_limiter import run_ffmpeg_with_limits
from app.core.temp_manager import temp_manager

CLIPS_DIR = os.path.join("storage", "clips")


def cut_clips(video_path, highlights, job_id):
    os.makedirs(CLIPS_DIR, exist_ok=True)
    clip_urls = []

    for i, (start, end) in enumerate(highlights, 1):
        clip_name = f"{job_id}_clip_{i}.mp4"
        local_clip_path = os.path.join(CLIPS_DIR, clip_name)
        temp_manager.add_temp_file(local_clip_path)

        cmd = [
            FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(start), "-to", str(end), "-i", video_path,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-maxrate", "2M", "-bufsize", "4M",
            "-c:a", "aac", "-b:a", "128k",
            "-threads", "1", "-max_muxing_queue_size", "1024",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            local_clip_path
        ]

        with ffmpeg_semaphore:
            cleanup_hung_processes()
            process = None
            try:
                import time
                process = run_ffmpeg_with_limits(cmd, timeout=600)
                active_processes[f"{job_id}_clip_{i}"] = (process, time.time())
                
                stdout, stderr = process.communicate(timeout=600)
                
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd, stderr)
                    
            except subprocess.TimeoutExpired:
                if process:
                    from app.core.ffmpeg_lock import kill_process_tree
                    kill_process_tree(process.pid)
                raise RuntimeError(f"Clip {i} processing timeout after 10 minutes")
            except subprocess.CalledProcessError as e:
                if e.returncode == -9:
                    raise RuntimeError(f"FFmpeg killed by system (out of memory/CPU). Try smaller video or shorter clips.")
                
                error_msg = f"Clip {i} failed (exit code {e.returncode})"
                if e.stderr:
                    error_msg += f": {e.stderr[:200]}"
                
                raise RuntimeError(error_msg)
            except Exception as e:
                raise RuntimeError(f"Clip {i} processing failed: {str(e)}")
            finally:
                clip_key = f"{job_id}_clip_{i}"
                if clip_key in active_processes:
                    del active_processes[clip_key]

        # Upload to S3
        try:
            s3_url = upload_file(local_path=local_clip_path, s3_key=f"clips/{clip_name}")
            clip_urls.append(s3_url)
        except Exception as e:
            raise RuntimeError(f"Failed to upload clip {i} to S3: {str(e)}")

        # Cleanup local clip
        temp_manager.cleanup_file(local_clip_path)

    return clip_urls
