# Opus MVP Frontend

Minimal React frontend for the video clipping service.

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Make sure your FastAPI backend is running on `http://localhost:8000`

## Features

- Single-page UI for video clip generation
- YouTube URL input with validation
- Configurable clip duration and count
- Real-time job status polling (every 3 seconds)
- Video preview cards with download links
- Clean, responsive design

## API Integration

- **POST /generate-clips**: Submits video processing job
- **GET /jobs/{job_id}**: Polls job status and retrieves clips

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Tech Stack

- React 18
- Vite (build tool)
- Native fetch API (no axios)
- Basic CSS (no frameworks)
- HTML5 video elements