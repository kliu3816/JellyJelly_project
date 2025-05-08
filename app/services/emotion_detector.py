import os
import tempfile
import requests
from moviepy.editor import VideoFileClip
import openai
import google.generativeai as genai
from PIL import Image
from typing import Dict, Any, List
import io
import base64
from dotenv import load_dotenv

class EmotionDetector:
    def __init__(self):
        self.openai_client = openai.OpenAI()
        # Load environment variables
        load_dotenv(dotenv_path=".env", override=True)
        
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

    async def detect_emotions(self, video_url: str) -> Dict[str, Any]:
        """Detect emotions in a video using Gemini Pro Vision."""
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
            frame_emotions = []
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
                    
                    print(f"Analyzing emotions in frame {i+1} with Gemini...")
                    response = self.gemini_model.generate_content([
                        "Analyze the emotions in this frame. Consider:\n1. Facial expressions\n2. Body language\n3. Overall mood\n4. Intensity of emotions",
                        image_parts[0]
                    ])
                    
                    if response and hasattr(response, 'text'):
                        frame_emotions.append(response.text)
                        print(f"Successfully analyzed emotions in frame {i+1}")
                    else:
                        print(f"Empty response from Gemini for frame {i+1}")
                        frame_emotions.append("Unable to analyze emotions in this frame")
                        
                except Exception as e:
                    print(f"Error analyzing emotions in frame {i+1} with Gemini: {str(e)}")
                    frame_emotions.append("Unable to analyze emotions in this frame")

            # Combine frame analyses using GPT-4
            combined_analysis = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an emotion analysis expert. Analyze the following frame-by-frame emotional descriptions and provide a comprehensive emotional analysis."
                    },
                    {
                        "role": "user",
                        "content": f"Based on these emotional descriptions: {frame_emotions}\n\nProvide:\n1. Overall emotional tone\n2. Emotional progression\n3. Key emotional moments\n4. Dominant emotions"
                    }
                ]
            )

            analysis_text = combined_analysis.choices[0].message.content
            return self._parse_emotion_analysis(analysis_text, duration)

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    def _extract_key_frames(self, video_path: str, num_frames: int = 5) -> List[Image.Image]:
        """Extract key frames from video for emotion analysis."""
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

    def _parse_emotion_analysis(self, analysis_text: str, duration: float) -> Dict[str, Any]:
        """Parse the emotion analysis text into structured data."""
        lines = analysis_text.split('\n')
        return {
            "overall_tone": lines[0] if lines else "",
            "emotional_progression": lines[1] if len(lines) > 1 else "",
            "key_moments": [
                {
                    "timestamp": (i + 0.5) * duration / len(lines[2:]) if len(lines) > 2 else 0,
                    "emotion": line.strip()
                }
                for i, line in enumerate(lines[2:])
            ],
            "dominant_emotions": lines[-1] if lines else ""
        } 