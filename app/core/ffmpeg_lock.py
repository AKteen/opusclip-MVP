import threading

# Global FFmpeg lock to prevent multiple concurrent processes
ffmpeg_lock = threading.Lock()