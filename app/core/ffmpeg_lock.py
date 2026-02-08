import threading
import signal
import os
import time

# ---- GLOBAL LIMITS ----
# Only ONE FFmpeg process at a time (very important in low-RAM deploys)
ffmpeg_semaphore = threading.Semaphore(1)

# Track active FFmpeg processes safely
active_processes = {}
_active_lock = threading.Lock()


def kill_process_tree(pid: int):
    """Force kill FFmpeg process and its children safely"""
    try:
        if os.name == "nt":
            # Windows
            os.system(f"taskkill /F /T /PID {pid}")
        else:
            # Unix/Linux (process group kill)
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:
        pass


def cleanup_hung_processes(max_age_seconds: int = 900):
    """
    Kill FFmpeg processes running longer than allowed.
    Uses locking to avoid race conditions.
    """
    now = time.time()

    with _active_lock:
        stale_keys = []

        for job_id, (process, start_time) in active_processes.items():
            if now - start_time > max_age_seconds:
                try:
                    kill_process_tree(process.pid)
                except Exception:
                    pass
                stale_keys.append(job_id)

        for key in stale_keys:
            active_processes.pop(key, None)


def register_process(key: str, process):
    """Register a running FFmpeg process"""
    with _active_lock:
        active_processes[key] = (process, time.time())


def unregister_process(key: str):
    """Unregister FFmpeg process after completion"""
    with _active_lock:
        active_processes.pop(key, None)
