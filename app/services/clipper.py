import os
import subprocess
from app.core.storage import upload_file
from app.core.config import FFMPEG_PATH
from app.core.ffmpeg_lock import ffmpeg_lock

CLIPS_DIR = os.path.join("storage", "clips")


def cut_clips(video_path, highlights, job_id):
    """
    Cuts video clips based on highlight timestamps,
    uploads them to S3, and returns S3 URLs.
    """

    os.makedirs(CLIPS_DIR, exist_ok=True)

    clip_urls = []

    for i, (start, end) in enumerate(highlights, 1):
        clip_name = f"{job_id}_clip_{i}.mp4"
        local_clip_path = os.path.join(CLIPS_DIR, clip_name)

        cmd = [
            FFMPEG_PATH,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            
            # Trim settings
            "-ss", str(start),
            "-to", str(end),
            "-i", video_path,
            
            # ⭐ CRITICAL MEMORY OPTIMIZATIONS
            "-c:v", "libx264",
            "-preset", "ultrafast",      # Changed from 'fast' - uses 50% less RAM
            "-crf", "23",
            "-maxrate", "2M",            # Prevents memory spikes
            "-bufsize", "4M",
            
            # Audio
            "-c:a", "aac",
            "-b:a", "128k",
            
            # ⭐ LIMIT RESOURCES
            "-threads", "2",             # Don't use all CPUs
            "-max_muxing_queue_size", "1024",
            
            # Output
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            
            local_clip_path
        ]

        with ffmpeg_lock:  # Only one FFmpeg process at a time
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"Clip {i} processing timeout after 10 minutes")
            except subprocess.CalledProcessError as e:
                # Handle SIGKILL and other FFmpeg failures
                if e.returncode == -9:
                    raise RuntimeError(f"FFmpeg killed by system (out of memory/CPU). Try smaller video or shorter clips.")
                
                error_msg = f"Clip {i} failed (exit code {e.returncode})"
                if e.stderr:
                    error_msg += f": {e.stderr[:200]}"
                
                raise RuntimeError(error_msg)
            except Exception as e:
                raise RuntimeError(f"Clip {i} processing failed: {str(e)}")

        # ☁️ Upload to S3
        try:
            s3_url = upload_file(
                local_path=local_clip_path,
                s3_key=f"clips/{clip_name}"
            )
            clip_urls.append(s3_url)
        except Exception as e:
            raise RuntimeError(f"Failed to upload clip {i} to S3: {str(e)}")

        # 🧹 Cleanup local clip
        try:
            os.remove(local_clip_path)
        except:
            pass

    return clip_urls
