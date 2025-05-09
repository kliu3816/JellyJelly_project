from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.services.video_analyzer import VideoAnalyzer
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Global analyzer instance
analyzer: VideoAnalyzer

@app.on_event("startup")
async def startup_event():
    global analyzer
    logger.info("Loading VideoAnalyzer model...")
    analyzer = VideoAnalyzer(model_size=os.getenv("WHISPER_MODEL", "tiny"))
    logger.info("VideoAnalyzer model loaded")

# Timeout middleware
class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=600.0)
        except asyncio.TimeoutError:
            return JSONResponse(status_code=504, content={"detail": "Request timeout"})

app.add_middleware(TimeoutMiddleware)

# CORS for production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jelly-jelly-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoAnalysisRequest(BaseModel):
    video_url: str
    analyze_emotions: bool = True
    generate_titles: bool = True

@app.get("/")
async def root():
    return {"message": "JellyJelly API is running"}

@app.post("/api/analyze")
async def analyze_video(request: Request):
    start_time = time.time()
    try:
        payload = await request.json()
        video_url = payload.get("video_url")
        if not video_url:
            raise HTTPException(status_code=400, detail="video_url is required")

        if not os.getenv("OPENAI_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
            raise HTTPException(status_code=500, detail="API keys not configured")

        result = await analyzer.analyze_video(
            video_url,
            analyze_emotions=payload.get("analyze_emotions", True),
            generate_titles=payload.get("generate_titles", True)
        )

        logger.info(f"Analysis completed in {time.time() - start_time:.2f}s")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
