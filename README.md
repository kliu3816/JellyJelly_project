# JellyJelly Video Analyzer By Kevin Liu

A powerful video analysis tool that uses AI to analyze videos and provide detailed insights. The application is deployed at [https://jelly-jelly-app.vercel.app/](https://jelly-jelly-app.vercel.app/)

## Example links: 
- https://jelly-shareables.s3.amazonaws.com/B3C5069A-C7E9-4598-9298-E70275B8CFF7/B3C5069A-C7E9-4598-9298-E70275B8CFF7_original.mp4
- https://jelly-shareables.s3.amazonaws.com/B3C5069A-C7E9-4598-9298-E70275B8CFF7/B3C5069A-C7E9-4598-9298-E70275B8CFF7_original.mp4


## Features

- **Video Analysis**: Upload or provide a video URL for comprehensive analysis
- **Content Safety**: AI-powered content safety scoring that evaluates:
  - Explicit or inappropriate content
  - Hate speech or discriminatory language
  - Violence or harmful content
  - Adult or NSFW content
  - Misinformation or harmful claims
- **Emotional Analysis**: Analyze emotions and mood throughout the video
- **Key Moments**: Automatically identify and timestamp important moments
- **Context Analysis**: Detailed analysis of setting, topic, and key points
- **Title Generation**: AI-generated titles for your video content
- **Export Functionality**: Download complete analysis results as JSON

## Tech Stack

- **Frontend**: Next.js, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python
- **AI Models**: 
  - GPT-4 for content analysis and safety scoring
  - Gemini for visual analysis
  - Whisper for audio transcription

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- FFmpeg installed on your system

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jellyjelly-project.git
cd jellyjelly-project
```

2. Set up the backend:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Create a `.env` file in the backend directory with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
```

### Running the Application

1. Start the backend server:
```bash
uvicorn app.main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Deployment

### Frontend Deployment (Vercel)

1. Push your code to GitHub
2. Go to [Vercel](https://vercel.com)
3. Import your repository
4. Configure the project:
   - Framework Preset: Next.js
   - Root Directory: frontend
   - Build Command: `npm run build`
   - Output Directory: .next
5. Add environment variables:
   - `NEXT_PUBLIC_API_URL`: Your backend API URL

### Backend Deployment (Render)

1. Create a new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Configure the service:
   - Name: jellyjelly-backend
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
5. Deploy the service

### Environment Variables

Make sure to set these environment variables in your deployment platforms:

Frontend (Vercel):
- `NEXT_PUBLIC_API_URL`: Your Render backend URL

Backend (Render):
- `OPENAI_API_KEY`: Your OpenAI API key
- `GOOGLE_API_KEY`: Your Google API key

## Usage

1. Enter a video URL in the input field
2. Select analysis options:
   - Analyze Emotions
   - Generate Titles
3. Click "Analyze Video"
4. View the comprehensive analysis results
5. Download the analysis as JSON using the download button

<<<<<<< HEAD
## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
=======
## Deployment

The application is deployed on Vercel and can be accessed at [https://jelly-jelly-app.vercel.app/](https://jelly-jelly-app.vercel.app/)
>>>>>>> 8536ae14eb2bca24ef6934d221ebcf74e3e41112
