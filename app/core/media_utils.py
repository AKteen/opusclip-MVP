import subprocess
from app.core.config import FFMPEG_PATH

def get_video_duration(video_path: str) -> float:
    cmd = [
        FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0
