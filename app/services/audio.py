import subprocess
import os
from app.core.config import FFMPEG_PATH

AUDIO_OUT = os.path.join("storage", "audio")

os.makedirs(AUDIO_OUT, exist_ok=True)

def extract_audio(audio_input: str, job_id: str) -> str:
    wav_path = os.path.join(AUDIO_OUT, f"{job_id}.wav")

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", audio_input,
        "-ac", "1",
        "-ar", "16000",
        wav_path
    ]

    subprocess.run(cmd, check=True)
    return wav_path
