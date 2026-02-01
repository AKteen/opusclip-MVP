import os
import requests
import gdown

UPLOAD_DIR = os.path.join("storage", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def is_google_drive(url: str) -> bool:
    return "drive.google.com" in url


def is_dropbox(url: str) -> bool:
    return "dropbox.com" in url


def download_video(file_url: str, job_id: str) -> dict:
    print(f"[{job_id}] Downloading video from URL...")

    video_path = os.path.join(UPLOAD_DIR, f"{job_id}.mp4")

    # ✅ Google Drive
    if is_google_drive(file_url):
        print(f"[{job_id}] Detected Google Drive link")
        gdown.download(
            url=file_url,
            output=video_path,
            quiet=False,
            fuzzy=True
        )

    # ✅ Dropbox
    elif is_dropbox(file_url):
        print(f"[{job_id}] Detected Dropbox link")
        if "?dl=0" in file_url:
            file_url = file_url.replace("?dl=0", "?dl=1")

        with requests.get(file_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

    # ✅ Normal direct video URL
    else:
        print(f"[{job_id}] Detected direct file URL")
        with requests.get(file_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

    # Safety check
    if not os.path.exists(video_path) or os.path.getsize(video_path) < 100000:
        raise RuntimeError("Downloaded file is invalid or too small")

    print(f"[{job_id}] Video downloaded successfully")
    return {
        "video": video_path
    }
