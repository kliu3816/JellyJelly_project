import os
import tempfile
import requests
from moviepy.editor import VideoFileClip
import openai
import google.generativeai as genai
from PIL import Image
import numpy as np
from typing import List, Dict, Any
import io
import base64
from dotenv import load_dotenv
import whisper
import asyncio
import time
import logging
import subprocess
import re

load_dotenv(dotenv_path=".env", override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoAnalyzer:
    def __init__(self):
        # Initialize OpenAI client without any proxy settings
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info("Loading Whisper model...")
        try:
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
        
        # Configure Gemini with safety settings
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        generation_config = {
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 2048,
        }
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        self.gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
    def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video file to a temporary WAV file."""
        temp_audio_path = video_path.replace('.mp4', '_audio.wav')
        try:
            # Use ffmpeg to extract audio
            command = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                temp_audio_path
            ]
            
            logger.info(f"Extracting audio with command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return ""
                
            logger.info("Audio extraction successful")
            return temp_audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return ""
        
    async def _transcribe_audio(self, video_path: str) -> str:
        """Transcribe the audio from the video using Whisper."""
        temp_audio_path = None
        try:
            logger.info(f"Starting transcription of video: {video_path}")
            
            # Verify the file exists and is readable
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return ""
                
            # Get file size
            file_size = os.path.getsize(video_path)
            logger.info(f"Video file size: {file_size} bytes")
            
            # Extract audio to WAV format
            temp_audio_path = self._extract_audio(video_path)
            if not temp_audio_path or not os.path.exists(temp_audio_path):
                logger.error("Failed to extract audio")
                return ""
            
            # Run the CPU-intensive transcription in a thread pool
            loop = asyncio.get_event_loop()
            logger.info("Starting Whisper transcription...")
            result = await loop.run_in_executor(None, self.whisper_model.transcribe, temp_audio_path)
            
            if not result or "text" not in result:
                logger.error("Transcription failed - no text in result")
                return ""
                
            transcription = result["text"].strip()
            logger.info(f"Transcription completed. Length: {len(transcription)} characters")
            logger.info(f"Transcription content: {transcription}")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return ""
        finally:
            # Clean up temporary audio file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                    logger.info(f"Cleaned up temporary audio file: {temp_audio_path}")
                except Exception as e:
                    logger.error(f"Error deleting temporary audio file: {str(e)}")

    def _extract_key_frames(self, video_path: str, num_frames: int = 5) -> List[Image.Image]:
        """Extract key frames from video for analysis."""
        video = None
        try:
            video = VideoFileClip(video_path)
            duration = video.duration
            
            frames = []
            for i in range(num_frames):
                timestamp = (i + 0.5) * duration / num_frames
                frame = video.get_frame(timestamp)
                # Convert numpy array to PIL Image and ensure proper format
                frame_image = Image.fromarray(frame.astype('uint8'))
                # Resize if needed (Gemini has size limits)
                if frame_image.width > 1024 or frame_image.height > 1024:
                    frame_image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                frames.append(frame_image)
            
            return frames
        finally:
            if video is not None:
                video.close()

    async def _analyze_content_safety(self, summary: str) -> float:
        """Analyze content safety using GPT-4."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a content safety analyzer. Your task is to analyze the content and provide a safety score between 0 and 1.
                        Consider:
                        1. Explicit or inappropriate content
                        2. Hate speech or discriminatory language
                        3. Violence or harmful content
                        4. Adult or NSFW content
                        5. Misinformation or harmful claims
                        
                        Return ONLY a number between 0 and 1, where:
                        1.0 = Completely safe, family-friendly content
                        0.0 = Extremely unsafe, harmful content"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this content for safety: {summary}"
                    }
                ]
            )
            
            # Extract the score from GPT's response
            score_text = response.choices[0].message.content.strip()
            try:
                score = float(score_text)
                # Ensure score is between 0 and 1
                return max(0.0, min(1.0, score))
            except ValueError:
                logger.error(f"Invalid safety score format: {score_text}")
                return 0.95  # Default safe score if parsing fails
                
        except Exception as e:
            logger.error(f"Error analyzing content safety: {str(e)}")
            return 0.95  # Default safe score if analysis fails

    async def analyze_video(self, video_url: str) -> Dict[str, Any]:
        """Analyze a video using multiple AI models."""
        temp_file_path = None
        try:
            logger.info(f"Starting video analysis for URL: {video_url}")
            
            # Download video to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                logger.info("Downloading video...")
                response = requests.get(video_url, stream=True)
                response.raise_for_status()  # Raise an exception for bad status codes
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_file_path = temp_file.name
                logger.info(f"Video downloaded to: {temp_file_path}")

            # Extract frames for analysis
            logger.info("Extracting frames...")
            frames = self._extract_key_frames(temp_file_path)
            
            # Get video duration
            video = VideoFileClip(temp_file_path)
            duration = video.duration
            video.close()
            logger.info(f"Video duration: {duration} seconds")

            # Transcribe audio
            logger.info("Starting audio transcription...")
            transcription = await self._transcribe_audio(temp_file_path)
            if not transcription:
                logger.warning("No transcription available - proceeding with visual analysis only")
                transcription = "No audio transcription available."

            # Analyze frames with Gemini
            logger.info("Analyzing frames with Gemini...")
            frame_descriptions = []
            for i, frame in enumerate(frames):
                try:
                    # Convert frame to bytes
                    img_byte_arr = io.BytesIO()
                    frame.save(img_byte_arr, format='JPEG', quality=95)
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Convert to base64
                    base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
                    
                    # Create image part for Gemini
                    image_parts = [
                        {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    ]
                    
                    logger.info(f"Analyzing frame {i+1} with Gemini...")
                    response = self.gemini_model.generate_content([
                        "Describe this frame in detail, including:\n1. What's happening\n2. The setting\n3. People and their actions\n4. Notable expressions or emotions",
                        image_parts[0]
                    ])
                    
                    if response and hasattr(response, 'text'):
                        frame_descriptions.append(response.text)
                        logger.info(f"Successfully analyzed frame {i+1}")
                    else:
                        logger.warning(f"Empty response from Gemini for frame {i+1}")
                        frame_descriptions.append("Unable to analyze this frame")
                        
                except Exception as e:
                    logger.error(f"Error analyzing frame {i+1} with Gemini: {str(e)}")
                    frame_descriptions.append("Unable to analyze this frame")

            # Combine frame descriptions and transcription for final analysis
            logger.info("Generating final analysis with GPT-4...")
            combined_analysis = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a video analysis expert. Your task is to analyze both the visual content and spoken words to create a comprehensive analysis. Remember that Jelly Jelly is the social media app that you are working for and the content is for
                        and  a jelly is a video that is uploaded to the app.
                        Focus on:
                        1. What is actually being said in the video
                        2. The visual context and actions
                        3. How the spoken content relates to what's being shown
                        4. The overall message and purpose of the video"""
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this video based on:

Visual Content (Frame Descriptions):
{frame_descriptions}

Spoken Content (Transcription):
{transcription}

Please provide:
1. A detailed summary that combines both what is being said and what is being shown. Focus on the actual content and message.
2. The setting and context of the video
3. The main topic and key points being discussed
4. A viral caption that captures the essence of both the visual and spoken content"""
                    }
                ]
            )

            analysis_text = combined_analysis.choices[0].message.content
            logger.info("Analysis completed successfully")
            analysis = self._parse_analysis(analysis_text)
            
            # Add key moments
            analysis["key_moments"] = self._extract_key_moments(frames, duration)
            
            # Analyze content safety
            logger.info("Analyzing content safety...")
            analysis["safety_score"] = await self._analyze_content_safety(analysis["summary"])

            return analysis

        except Exception as e:
            logger.error(f"Error during video analysis: {str(e)}")
            raise
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    # Give a small delay to ensure all file handles are released
                    await asyncio.sleep(1)
                    os.unlink(temp_file_path)
                    logger.info(f"Temporary file cleaned up: {temp_file_path}")
                except Exception as e:
                    logger.error(f"Error deleting temporary file: {str(e)}")

    def _extract_key_moments(self, frames: List[Image.Image], duration: float) -> List[Dict[str, Any]]:
        """Extract key moments from the video."""
        moments = []
        for i, frame in enumerate(frames):
            timestamp = (i + 0.5) * duration / len(frames)
            moments.append({
                "timestamp": timestamp,
                "description": f"Key moment at {timestamp:.1f} seconds"
            })
        return moments

    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse the analysis text into structured data."""
        try:
            # Split the text into sections
            sections = analysis_text.split('\n\n')
            
            # Initialize the result dictionary
            result = {
                "summary": "",
                "setting": "",
                "conversation_topic": "",
                "suggested_caption": "",
                "mood": "neutral"
            }
            
            # Process each section
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                # Look for summary section
                if "1. A detailed summary" in section or "Summary:" in section:
                    # Extract the summary text, removing the header
                    summary_lines = section.split('\n')[1:] if '\n' in section else [section]
                    result["summary"] = ' '.join(summary_lines).strip()
                
                # Look for setting section
                elif "2. The setting" in section or "Setting:" in section:
                    # Extract the setting text, removing the header
                    setting_lines = section.split('\n')[1:] if '\n' in section else [section]
                    result["setting"] = ' '.join(setting_lines).strip()
                
                # Look for conversation topic section
                elif "3. The main topic" in section or "Topic:" in section:
                    # Extract the topic text, removing the header
                    topic_lines = section.split('\n')[1:] if '\n' in section else [section]
                    result["conversation_topic"] = ' '.join(topic_lines).strip()
                
                # Look for caption section
                elif "4. A viral caption" in section or "Caption:" in section:
                    # Extract the caption text, removing the header
                    caption_lines = section.split('\n')[1:] if '\n' in section else [section]
                    result["suggested_caption"] = ' '.join(caption_lines).strip()
            
            # If any field is empty, try to extract it from the text
            if not result["summary"]:
                # Try to find the first substantial paragraph as summary
                paragraphs = [p.strip() for p in analysis_text.split('\n\n') if p.strip()]
                if paragraphs:
                    result["summary"] = paragraphs[0]
            
            if not result["setting"]:
                # Try to find setting information
                for section in sections:
                    if "setting" in section.lower() or "context" in section.lower():
                        result["setting"] = section.strip()
                        break
            
            if not result["conversation_topic"]:
                # Try to find topic information
                for section in sections:
                    if "topic" in section.lower() or "key points" in section.lower():
                        result["conversation_topic"] = section.strip()
                        break
            
            if not result["suggested_caption"]:
                # Try to find caption information
                for section in sections:
                    if "caption" in section.lower():
                        result["suggested_caption"] = section.strip()
                        break
            
            # Clean up any remaining headers or numbers in the fields
            for key in ["setting", "conversation_topic", "suggested_caption"]:
                if result[key]:
                    # Remove common headers and numbers
                    result[key] = result[key].replace("Setting:", "").replace("Topic:", "").replace("Caption:", "")
                    result[key] = re.sub(r'^\d+\.\s*', '', result[key])
                    result[key] = result[key].strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing analysis text: {str(e)}")
            # Return a default structure if parsing fails
            return {
                "summary": analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text,
                "setting": "Unable to extract setting",
                "conversation_topic": "Unable to extract topic",
                "suggested_caption": "Unable to extract caption",
                "mood": "neutral"
            } 