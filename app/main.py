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
from starlette.requests import Request
from starlette.responses import Response
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=300.0)  # 5 minutes timeout
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )

app = FastAPI()

# Add timeout middleware
app.add_middleware(TimeoutMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["jelly-jelly-app.vercel.app"],
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

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    env_vars = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
        "HTTP_PROXY": os.getenv("HTTP_PROXY"),
        "HTTPS_PROXY": os.getenv("HTTPS_PROXY"),
        "NO_PROXY": os.getenv("NO_PROXY"),
    }
    return env_vars

@app.post("/api/analyze")
async def analyze_video(request: Request):
    start_time = time.time()
    try:
        # Parse request body
        body = await request.json()
        video_url = body.get("video_url")
        analyze_emotions = body.get("analyze_emotions", True)
        generate_titles = body.get("generate_titles", True)

        if not video_url:
            raise HTTPException(status_code=400, detail="video_url is required")

        logger.info(f"Received analysis request for video: {video_url}")
        
        # Validate environment variables
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        if not os.getenv("GOOGLE_API_KEY"):
            raise HTTPException(status_code=500, detail="Google API key not configured")
            
        # Initialize analyzer and process video
        analyzer = VideoAnalyzer()
        logger.info("VideoAnalyzer initialized successfully")
        
        result = await analyzer.analyze_video(
            video_url,
            analyze_emotions=analyze_emotions,
            generate_titles=generate_titles
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Video analysis completed successfully in {processing_time:.2f} seconds")
        return JSONResponse(content=result)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during video analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000")),
        timeout_keep_alive=300,
        timeout_graceful_shutdown=300
    ) 