import os
import subprocess
import signal


# ---- CONSTANTS ----
MAX_MEMORY_BYTES = 768 * 1024 * 1024   # 768 MB (512 was too tight for ffmpeg)
MAX_CPU_SECONDS = 300                  # 5 minutes CPU time


def run_ffmpeg_with_limits(cmd, timeout=300):
    """
    Run FFmpeg with sane memory + CPU limits.
    Avoids random SIGKILL due to over-aggressive limits.
    """

    def preexec_fn():
        # Linux / Unix only
        if os.name != "nt":
            try:
                import resource

                # Address space (virtual memory)
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES)
                )

                # CPU time limit
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (MAX_CPU_SECONDS, MAX_CPU_SECONDS)
                )

                # Lower priority slightly
                os.nice(5)

                # New process group (so we can kill tree safely)
                os.setsid()
            except Exception:
                pass

    # ❌ DO NOT add thread_queue_size blindly (causes memory spikes)
    # ❌ DO NOT mutate FFmpeg cmd here

    popen_kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }

    if os.name != "nt":
        popen_kwargs["preexec_fn"] = preexec_fn
    else:
        # Windows: create new process group so kill works
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(cmd, **popen_kwargs)
