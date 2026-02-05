from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import time
import threading

class ConcurrentRequestLimiter:
    def __init__(self, max_concurrent=2):
        self.max_concurrent = max_concurrent
        self.active_requests = 0
        self.lock = threading.Lock()
    
    async def __call__(self, request: Request, call_next):
        # Only limit POST requests to generate-clips
        if request.method == "POST" and "/generate-clips" in str(request.url):
            with self.lock:
                if self.active_requests >= self.max_concurrent:
                    return JSONResponse(
                        status_code=503,
                        content={"error": "Server busy", "message": "Too many concurrent requests"},
                        headers={"Retry-After": "30"}
                    )
                self.active_requests += 1
            
            try:
                response = await call_next(request)
                return response
            finally:
                with self.lock:
                    self.active_requests -= 1
        else:
            return await call_next(request)

# Global limiter instance
request_limiter = ConcurrentRequestLimiter(max_concurrent=2)