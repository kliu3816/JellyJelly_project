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

class VideoAnalyzer:
    def __init__(self):
        self.openai_client = openai.OpenAI()
        
        # Configure Gemini with safety settings
        load_dotenv(dotenv_path=".env", override=True) 

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
        
    async def analyze_video(self, video_url: str) -> Dict[str, Any]:
        """Analyze a video using multiple AI models."""
        # Download video to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            response = requests.get(video_url)
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        try:
            # Extract frames for analysis
            frames = self._extract_key_frames(temp_file_path)
            
            # Get video duration
            video = VideoFileClip(temp_file_path)
            duration = video.duration
            video.close()

            # Analyze frames with Gemini
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
                    
                    print(f"Analyzing frame {i+1} with Gemini...")
                    response = self.gemini_model.generate_content([
                        "Describe this frame in detail, including:\n1. What's happening\n2. The setting\n3. People and their actions\n4. Notable expressions or emotions",
                        image_parts[0]
                    ])
                    
                    if response and hasattr(response, 'text'):
                        frame_descriptions.append(response.text)
                        print(f"Successfully analyzed frame {i+1}")
                    else:
                        print(f"Empty response from Gemini for frame {i+1}")
                        frame_descriptions.append("Unable to analyze this frame")
                        
                except Exception as e:
                    print(f"Error analyzing frame {i+1} with Gemini: {str(e)}")
                    frame_descriptions.append("Unable to analyze this frame")

            # Combine frame descriptions for final analysis
            combined_analysis = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a video analysis expert. Analyze the following frame-by-frame descriptions and provide a comprehensive analysis."
                    },
                    {
                        "role": "user",
                        "content": f"Based on these frame descriptions: {frame_descriptions}\n\nProvide:\n1. A concise summary\n2. The setting\n3. The likely conversation topic\n4. A suggested viral caption"
                    }
                ]
            )

            analysis_text = combined_analysis.choices[0].message.content
            analysis = self._parse_analysis(analysis_text)
            
            # Add key moments
            analysis["key_moments"] = self._extract_key_moments(frames, duration)
            analysis["safety_score"] = 0.95  # Placeholder implementation

            return analysis

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    def _extract_key_frames(self, video_path: str, num_frames: int = 5) -> List[Image.Image]:
        """Extract key frames from video for analysis."""
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
        
        video.close()
        return frames

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
        lines = analysis_text.split('\n')
        return {
            "summary": lines[0] if lines else "",
            "setting": lines[1] if len(lines) > 1 else "",
            "conversation_topic": lines[2] if len(lines) > 2 else "",
            "suggested_caption": lines[3] if len(lines) > 3 else "",
            "mood": "neutral"  # Placeholder implementation
        }

    async def detect_speakers(self, video_url: str) -> int:
        """Detect the number of speakers in the video."""
        # Placeholder implementation
        return 1 