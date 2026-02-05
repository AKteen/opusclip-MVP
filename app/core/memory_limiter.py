import os
import subprocess

def set_memory_limit():
    """Set memory limit for current process (Windows compatible)"""
    try:
        if os.name != 'nt':  # Unix/Linux only
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    except:
        pass

def run_ffmpeg_with_limits(cmd, timeout=300):
    """Run FFmpeg with memory and CPU limits (cross-platform)"""
    def preexec_fn():
        try:
            if os.name != 'nt':  # Unix/Linux only
                import resource
                resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
                resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
                os.nice(10)
        except:
            pass
    
    # Add memory-specific FFmpeg options
    memory_limited_cmd = cmd + [
        "-thread_queue_size", "512",
    ]
    
    if os.name != 'nt':  # Unix/Linux
        return subprocess.Popen(
            memory_limited_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec_fn
        )
    else:  # Windows - no resource limits available
        return subprocess.Popen(
            memory_limited_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )