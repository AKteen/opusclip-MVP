import os
import subprocess
import signal


# ---- CONSTANTS ----
MAX_MEMORY_BYTES = 768 * 1024 * 1024   # 768 MB
MAX_CPU_SECONDS = 300                  # 5 minutes CPU time


def run_ffmpeg_with_limits(cmd, timeout=300, env=None):
    """
    Run FFmpeg with sane memory + CPU limits.
    Supports passing custom env (required for AV1 / dav1d control).
    """

    def preexec_fn():
        # Linux / Unix only
        if os.name != "nt":
            try:
                import resource

                # Limit virtual memory
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES)
                )

                # Limit CPU time
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (MAX_CPU_SECONDS, MAX_CPU_SECONDS)
                )

                # Lower priority slightly
                os.nice(5)

                # New process group (so killpg works)
                os.setsid()
            except Exception:
                pass

    popen_kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "env": env or os.environ.copy(),  # ✅ THIS WAS THE MISSING PIECE
    }

    if os.name != "nt":
        popen_kwargs["preexec_fn"] = preexec_fn
    else:
        # Windows: allow killing full process tree
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(cmd, **popen_kwargs)
