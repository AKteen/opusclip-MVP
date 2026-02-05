import subprocess
import os
from app.core.config import FFMPEG_PATH
from app.core.ffmpeg_lock import ffmpeg_lock

AUDIO_OUT = os.path.join("storage", "audio")

os.makedirs(AUDIO_OUT, exist_ok=True)

def extract_audio(audio_input: str, job_id: str) -> str:
    wav_path = os.path.join(AUDIO_OUT, f"{job_id}.wav")

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-threads", "2",  # Limit CPU threads
        "-i", audio_input,
        "-ac", "1",
        "-ar", "16000",
        "-preset", "ultrafast",  # Fastest processing
        "-max_muxing_queue_size", "1024",  # Limit memory usage
        wav_path
    ]

    with ffmpeg_lock:  # Only one FFmpeg process at a time
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
            return wav_path
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Audio extraction timeout after 5 minutes")
        except subprocess.CalledProcessError as e:
            # Handle SIGKILL and other FFmpeg failures
            if e.returncode == -9:
                raise RuntimeError(f"FFmpeg killed by system (out of memory/CPU). Try smaller video.")
            
            error_msg = f"FFmpeg failed (exit code {e.returncode})"
            if e.stderr:
                error_msg += f": {e.stderr[:200]}"  # Limit error message length
            
            raise RuntimeError(error_msg)
        except Exception as e:
            raise RuntimeError(f"Audio extraction failed: {str(e)}")
