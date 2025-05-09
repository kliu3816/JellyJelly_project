from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.services.video_analyzer import VideoAnalyzer
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Vercel domain
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
async def analyze_video(request: VideoAnalysisRequest):
    try:
        logger.info(f"Received analysis request for video: {request.video_url}")
        
        # Validate environment variables
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        if not os.getenv("GOOGLE_API_KEY"):
            raise HTTPException(status_code=500, detail="Google API key not configured")
            
        # Initialize analyzer and process video
        analyzer = VideoAnalyzer()
        logger.info("VideoAnalyzer initialized successfully")
        
        result = await analyzer.analyze_video(
            request.video_url,
            analyze_emotions=request.analyze_emotions,
            generate_titles=request.generate_titles
        )
        
        logger.info("Video analysis completed successfully")
        return JSONResponse(content=result)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during video analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 