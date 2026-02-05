import threading
import signal
import os
import time
import asyncio

# Global FFmpeg semaphore - only 1 FFmpeg process at a time
ffmpeg_semaphore = threading.Semaphore(1)
ffmpeg_lock = threading.Lock()  # Keep for backward compatibility
active_processes = {}  # Track active FFmpeg processes

def kill_process_tree(pid):
    """Force kill process and children"""
    try:
        if os.name == 'nt':  # Windows
            os.system(f'taskkill /F /T /PID {pid}')
        else:  # Unix/Linux
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except:
        pass

def cleanup_hung_processes():
    """Clean up processes that have been running too long"""
    current_time = time.time()
    for job_id, (process, start_time) in list(active_processes.items()):
        if current_time - start_time > 900:  # 15 minutes max
            try:
                kill_process_tree(process.pid)
                del active_processes[job_id]
            except:
                pass