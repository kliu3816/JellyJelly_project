import os
import tempfile
import requests
from moviepy.editor import VideoFileClip
import openai
import google.generativeai as genai
from PIL import Image
import numpy as np
from typing import List, Dict, Any, Optional
import io
import base64
from dotenv import load_dotenv
import whisper
import asyncio
import time
import logging
import subprocess
import re
import json

# Load environment variables
load_dotenv(dotenv_path=".env", override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VideoAnalyzer:
    def __init__(self, model_size: str = "tiny"):
        """Initialize the VideoAnalyzer with specified Whisper model size."""
        logger.info(f"Loading VideoAnalyzer with Whisper model size: {model_size}")
        self.model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully")
        
        # Initialize Google AI model
        self.gemini_pro = genai.GenerativeModel('gemini-pro')
        self.gemini_pro_vision = genai.GenerativeModel('gemini-pro-vision')
        logger.info("Google AI models initialized successfully")

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
            result = await loop.run_in_executor(None, self.model.transcribe, temp_audio_path)
            
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
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
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

    async def analyze_video(self, video_url: str, analyze_emotions: bool = True, generate_titles: bool = True) -> Dict[str, Any]:
        """Analyze a video and return insights."""
        try:
            logger.info(f"Starting video analysis for: {video_url}")
            start_time = time.time()

            # Download video
            logger.info("Downloading video...")
            response = requests.get(video_url)
            if response.status_code != 200:
                raise ValueError(f"Failed to download video: {response.status_code}")
            
            # Save video temporarily
            temp_video_path = "temp_video.mp4"
            with open(temp_video_path, "wb") as f:
                f.write(response.content)
            logger.info("Video downloaded successfully")

            # Extract frames and transcribe audio
            logger.info("Extracting frames and transcribing audio...")
            frames = self._extract_key_frames(temp_video_path)
            transcription = await self._transcribe_audio(temp_video_path)
            logger.info("Frames extracted and audio transcribed")

            # Clean up temporary file
            os.remove(temp_video_path)
            logger.info("Temporary video file removed")

            # Analyze frames
            logger.info("Analyzing frames...")
            frame_analysis = await self.analyze_frames(frames)
            logger.info("Frame analysis complete")

            # Analyze transcription
            logger.info("Analyzing transcription...")
            transcription_analysis = await self.analyze_transcription(transcription)
            logger.info("Transcription analysis complete")

            # Combine results
            result = {
                "frame_analysis": frame_analysis,
                "transcription_analysis": transcription_analysis,
                "content_safety": await self._analyze_content_safety(transcription)
            }

            # Add emotions analysis if requested
            if analyze_emotions:
                logger.info("Analyzing emotions...")
                result["emotions"] = await self.analyze_emotions(frame_analysis, transcription_analysis)
                logger.info("Emotions analysis complete")

            # Generate titles if requested
            if generate_titles:
                logger.info("Generating titles...")
                result["titles"] = await self.generate_titles(frame_analysis, transcription_analysis)
                logger.info("Titles generated")

            processing_time = time.time() - start_time
            logger.info(f"Video analysis completed in {processing_time:.2f} seconds")
            
            return result

        except Exception as e:
            logger.error(f"Error in video analysis: {str(e)}")
            raise

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

    async def analyze_frames(self, frames: list) -> Dict[str, Any]:
        """Analyze frames using Google's Gemini Pro Vision."""
        try:
            frame_analyses = []
            for frame in frames:
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                frame.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Analyze frame
                response = await asyncio.to_thread(
                    self.gemini_pro_vision.generate_content,
                    [img_byte_arr, "Describe this frame in detail, focusing on visual elements, actions, and any notable features."]
                )
                frame_analyses.append(response.text)
            
            return {
                "frame_descriptions": frame_analyses,
                "summary": await self.summarize_frame_analyses(frame_analyses)
            }
        except Exception as e:
            logger.error(f"Error analyzing frames: {str(e)}")
            raise

    async def analyze_transcription(self, transcription: str) -> Dict[str, Any]:
        """Analyze transcription using Google's Gemini Pro."""
        try:
            # Analyze transcription
            response = await asyncio.to_thread(
                self.gemini_pro.generate_content,
                f"Analyze this transcription and provide insights about the content, tone, and key points:\n\n{transcription}"
            )
            
            return {
                "analysis": response.text,
                "key_points": await self.extract_key_points(transcription)
            }
        except Exception as e:
            logger.error(f"Error analyzing transcription: {str(e)}")
            raise

    async def analyze_emotions(self, frame_analysis: Dict[str, Any], transcription_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze emotions in the video."""
        try:
            # Combine frame and transcription analyses
            combined_analysis = f"Frame Analysis: {frame_analysis['summary']}\nTranscription Analysis: {transcription_analysis['analysis']}"
            
            # Analyze emotions
            response = await asyncio.to_thread(
                self.gemini_pro.generate_content,
                f"Analyze the emotions and mood in this content. Provide a detailed breakdown of emotional elements:\n\n{combined_analysis}"
            )
            
            return {
                "emotional_analysis": response.text,
                "mood_summary": await self.summarize_mood(combined_analysis)
            }
        except Exception as e:
            logger.error(f"Error analyzing emotions: {str(e)}")
            raise

    async def generate_titles(self, frame_analysis: Dict[str, Any], transcription_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate titles for the video."""
        try:
            # Combine analyses for context
            combined_analysis = f"Frame Analysis: {frame_analysis['summary']}\nTranscription Analysis: {transcription_analysis['analysis']}"
            
            # Generate titles
            response = await asyncio.to_thread(
                self.gemini_pro.generate_content,
                f"Generate 5 engaging titles for this content. Make them catchy and relevant:\n\n{combined_analysis}"
            )
            
            return {
                "suggested_titles": response.text.split('\n'),
                "best_title": await self.select_best_title(combined_analysis)
            }
        except Exception as e:
            logger.error(f"Error generating titles: {str(e)}")
            raise

    async def summarize_frame_analyses(self, frame_analyses: list) -> str:
        """Summarize frame analyses."""
        try:
            response = await asyncio.to_thread(
                self.gemini_pro.generate_content,
                f"Summarize these frame analyses into a cohesive description:\n\n{json.dumps(frame_analyses, indent=2)}"
            )
            return response.text
        except Exception as e:
            logger.error(f"Error summarizing frame analyses: {str(e)}")
            raise

    async def extract_key_points(self, transcription: str) -> list:
        """Extract key points from transcription."""
        try:
            response = await asyncio.to_thread(
                self.gemini_pro.generate_content,
                f"Extract the key points from this transcription:\n\n{transcription}"
            )
            return response.text.split('\n')
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            raise

    async def summarize_mood(self, analysis: str) -> str:
        """Summarize the overall mood."""
        try:
            response = await asyncio.to_thread(
                self.gemini_pro.generate_content,
                f"Summarize the overall mood and emotional tone of this content:\n\n{analysis}"
            )
            return response.text
        except Exception as e:
            logger.error(f"Error summarizing mood: {str(e)}")
            raise

    async def select_best_title(self, analysis: str) -> str:
        """Select the best title from generated options."""
        try:
            response = await asyncio.to_thread(
                self.gemini_pro.generate_content,
                f"Select and refine the best title for this content:\n\n{analysis}"
            )
            return response.text
        except Exception as e:
            logger.error(f"Error selecting best title: {str(e)}")
            raise 