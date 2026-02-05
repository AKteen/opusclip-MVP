import resource
import os
import subprocess

def set_memory_limit():
    """Set memory limit for current process (512MB)"""
    try:
        # Set virtual memory limit to 512MB
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    except:
        pass  # Ignore if not supported on platform

def run_ffmpeg_with_limits(cmd, timeout=300):
    """Run FFmpeg with memory and CPU limits"""
    def preexec_fn():
        # Set memory limit for child process
        try:
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
            # Set CPU time limit (5 minutes)
            resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
            # Lower process priority
            os.nice(10)
        except:
            pass
    
    # Add memory-specific FFmpeg options
    memory_limited_cmd = cmd + [
        "-threads", "1",  # Single thread to reduce memory
        "-thread_queue_size", "512",  # Smaller queue
    ]
    
    if os.name != 'nt':  # Unix/Linux only
        return subprocess.Popen(
            memory_limited_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec_fn
        )
    else:  # Windows
        return subprocess.Popen(
            memory_limited_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )