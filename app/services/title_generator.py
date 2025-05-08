import openai
from typing import List

class TitleGenerator:
    def __init__(self):
        self.openai_client = openai.OpenAI()

    async def generate_titles(self, video_summary: str, transcription: str = "") -> List[str]:
        """Generate engaging titles for the video using OpenAI's GPT-4."""
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are a viral content expert. Generate 5 engaging titles for the video based on the summary and transcription.
                    The titles should be:
                    1. Attention-grabbing
                    2. Under 60 characters
                    3. Include relevant keywords from both visual and spoken content
                    4. Use power words
                    5. Follow YouTube/TikTok title best practices
                    6. Not mention how it is split screen since every video is split screen
                    7. Incorporate key phrases from the actual conversation
                    
                    Format each title on a new line."""
                },
                {
                    "role": "user",
                    "content": f"""Generate 5 viral-worthy titles for this video:

Summary: {video_summary}

Transcription: {transcription}

Focus on creating titles that capture both the visual content and the actual conversation."""
                }
            ],
            max_tokens=300
        )

        # Parse the response into a list of titles
        titles_text = response.choices[0].message.content
        titles = [title.strip() for title in titles_text.split('\n') if title.strip()]
        
        # Ensure we have exactly 5 titles
        while len(titles) < 5:
            titles.append("Title placeholder")
        return titles[:5]  # Return only the first 5 titles 