import os
import subprocess
from app.core.config import FFMPEG_PATH


def _get_ffprobe_path() -> str:
    """
    Safely derive ffprobe path from ffmpeg path (Windows & Unix safe)
    """
    ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
    ffprobe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    return os.path.join(ffmpeg_dir, ffprobe_name)


def get_video_duration(video_path: str) -> float:
    ffprobe_path = _get_ffprobe_path()

    cmd = [
        ffprobe_path,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0
