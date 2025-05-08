from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import openai
import google.generativeai as genai
from .services.video_analyzer import VideoAnalyzer
from .services.emotion_detector import EmotionDetector
from .services.title_generator import TitleGenerator
import logging
import tempfile
import requests
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI(title="JellyJelly Video Analyzer")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoAnalysisRequest(BaseModel):
    video_url: str
    language: Optional[str] = "en"
    analyze_emotions: Optional[bool] = True
    generate_titles: Optional[bool] = True
    detect_speakers: Optional[bool] = True

class VideoAnalysisResponse(BaseModel):
    summary: str
    setting: str
    mood: str
    conversation_topic: str
    suggested_caption: str
    key_moments: List[dict]
    emotions: Optional[dict]
    titles: Optional[List[str]]
    speaker_count: Optional[int]
    safety_score: float

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(request: VideoAnalysisRequest):
    temp_file_path = None
    try:
        logger.info(f"Starting video analysis for URL: {request.video_url}")
        
        analyzer = VideoAnalyzer()
        emotion_detector = EmotionDetector()
        title_generator = TitleGenerator()

        # Basic video analysis
        logger.info("Performing basic video analysis...")
        analysis = await analyzer.analyze_video(request.video_url)
        
        # Additional analysis based on request parameters
        if request.analyze_emotions:
            logger.info("Analyzing emotions...")
            analysis["emotions"] = await emotion_detector.detect_emotions(request.video_url)
        
        if request.generate_titles:
            logger.info("Generating titles...")
            # Get transcription from the analyzer
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                response = requests.get(request.video_url)
                temp_file.write(response.content)
                temp_file_path = temp_file.name
                try:
                    transcription = await analyzer._transcribe_audio(temp_file_path)
                    analysis["titles"] = await title_generator.generate_titles(analysis["summary"], transcription)
                finally:
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            # Give a small delay to ensure all file handles are released
                            await asyncio.sleep(1)
                            os.unlink(temp_file_path)
                        except Exception as e:
                            logger.error(f"Error deleting temporary file: {str(e)}")
        
        if request.detect_speakers:
            logger.info("Detecting speakers...")
            analysis["speaker_count"] = await analyzer.detect_speakers(request.video_url)

        logger.info("Analysis completed successfully")
        return VideoAnalysisResponse(**analysis)
    
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Ensure temporary file is cleaned up
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                await asyncio.sleep(1)
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Error deleting temporary file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 