import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "opus-clips")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

# Debug: Print loaded config (remove in production)
print(f"🎬 FFMPEG_PATH loaded: {FFMPEG_PATH}")
print(f"☁️  AWS_REGION: {AWS_REGION}")
print(f"🪣 S3_BUCKET: {S3_BUCKET}")
