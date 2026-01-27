import os
import sys
from dotenv import load_dotenv

# Load local environment variables
load_dotenv('.env.local')

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = current_dir

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Opus MVP locally...")
    print(f"📁 PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    print(f"🎬 FFMPEG_PATH: {os.environ.get('FFMPEG_PATH')}")
    print(f"☁️  AWS_REGION: {os.environ.get('AWS_REGION')}")
    print(f"🪣 S3_BUCKET: {os.environ.get('S3_BUCKET')}")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )