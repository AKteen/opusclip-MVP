import os
import subprocess
from app.core.storage import upload_file
from app.core.config import FFMPEG_PATH

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
            "-ss", str(start),
            "-to", str(end),
            "-i", video_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            local_clip_path
        ]

        subprocess.run(cmd, check=True)

        # ☁️ Upload to S3
        s3_url = upload_file(
            local_path=local_clip_path,
            s3_key=f"clips/{clip_name}"
        )

        clip_urls.append(s3_url)

        # 🧹 Cleanup local clip
        try:
            os.remove(local_clip_path)
        except:
            pass

    return clip_urls
