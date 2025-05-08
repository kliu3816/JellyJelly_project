# JellyJelly Video Analyzer

A multimodal AI-powered web application that analyzes Jelly videos using various AI models to provide rich insights and descriptions.

## Features

- Video content analysis using OpenAI GPT-4 Vision and Google Gemini Pro
- Automatic video summarization and scene description
- Emotion detection and sentiment analysis
- Auto-title generation
- Speaker detection
- Multilingual support
- Content safety scoring

## Setup

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```
4. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Install frontend dependencies and start the development server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: React + Tailwind CSS
- AI Models: OpenAI GPT-4 Vision, Google Gemini Pro
- Video Processing: MoviePy
- Deployment: Vercel (Frontend) + Render (Backend)

## API Endpoints

- `POST /api/analyze`: Submit a video URL for analysis
- `GET /api/health`: Health check endpoint

## License

MIT 