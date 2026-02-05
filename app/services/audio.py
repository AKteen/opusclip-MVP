import subprocess
import os
from app.core.config import FFMPEG_PATH
from app.core.ffmpeg_lock import ffmpeg_semaphore, active_processes, cleanup_hung_processes
from app.core.memory_limiter import run_ffmpeg_with_limits
from app.core.temp_manager import temp_manager

AUDIO_OUT = os.path.join("storage", "audio")

os.makedirs(AUDIO_OUT, exist_ok=True)

def extract_audio(audio_input: str, job_id: str) -> str:
    wav_path = os.path.join(AUDIO_OUT, f"{job_id}.wav")
    temp_manager.add_temp_file(wav_path)

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-threads", "1",  # Single thread for memory
        "-i", audio_input,
        "-ac", "1",
        "-ar", "16000",
        "-preset", "ultrafast",
        "-max_muxing_queue_size", "1024",
        wav_path
    ]

    # Use semaphore to limit concurrent FFmpeg processes
    ffmpeg_semaphore.acquire()
    try:
        cleanup_hung_processes()
        process = None
        try:
            import time
            process = run_ffmpeg_with_limits(cmd, timeout=300)
            active_processes[job_id] = (process, time.time())
            
            stdout, stderr = process.communicate(timeout=300)
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd, stderr)
            
            return wav_path
            
        except subprocess.TimeoutExpired:
            if process:
                from app.core.ffmpeg_lock import kill_process_tree
                kill_process_tree(process.pid)
            raise RuntimeError(f"Audio extraction timeout after 5 minutes")
        except subprocess.CalledProcessError as e:
            if e.returncode == -9:
                raise RuntimeError(f"FFmpeg killed by system (out of memory/CPU). Try smaller video.")
            
            error_msg = f"FFmpeg failed (exit code {e.returncode})"
            if e.stderr:
                error_msg += f": {e.stderr[:200]}"
            
            raise RuntimeError(error_msg)
        except Exception as e:
            raise RuntimeError(f"Audio extraction failed: {str(e)}")
        finally:
            if job_id in active_processes:
                del active_processes[job_id]
    finally:
        ffmpeg_semaphore.release()
