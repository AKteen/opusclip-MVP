import os
import subprocess
from highlights_audio import get_highlights

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
YTDLP = "yt-dlp"

INPUT_DIR = "input"
OUTPUT_DIR = "output"
CLIPS_DIR = "output/clips"

VIDEO_FILE = os.path.join(INPUT_DIR, "video.mp4")
AUDIO_WAV = os.path.join(OUTPUT_DIR, "audio.wav")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)


def run(cmd):
    subprocess.run(cmd, check=True)


def download_youtube(url):
    print("▶ Downloading YouTube video (Stable Mode)...")

    run([
        YTDLP,
        "--ffmpeg-location", FFMPEG,
        # REMOVED --download-sections to avoid 403 errors
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", VIDEO_FILE,
        url
    ])

    print("✅ Download complete")


def extract_audio():
    print("▶ Extracting WAV audio...")

    run([
        FFMPEG,
        "-y",
        "-i", VIDEO_FILE,
        AUDIO_WAV
    ])

    print("✅ Audio extracted")


def cut_clips(highlights):
    print(f"▶ Cutting {len(highlights)} clips...")

    for i, (start, end) in enumerate(highlights, 1):
        out = f"{CLIPS_DIR}/clip{i}.mp4"

        cmd = [
            FFMPEG,
            "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", VIDEO_FILE,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-shortest",
            out
        ]

        print(f"  • Clip {i}: {start}s → {end}s")
        run(cmd)

    print("✅ All clips created")


def main():
    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("❌ No URL provided")
        return

    download_youtube(url)
    extract_audio()

    highlights = get_highlights()
    print(f"✅ {len(highlights)} highlights found")

    cut_clips(highlights)

    print("\n🎉 PIPELINE COMPLETE")
    print("Clips available in: output/clips/")


if __name__ == "__main__":
    main()
