'use client';

import { useState } from 'react';
import { VideoAnalysisRequest, VideoAnalysisResponse } from '@/types';

interface VideoAnalyzerProps {
  onAnalysisComplete: (analysis: VideoAnalysisResponse) => void;
  onLoadingChange: (loading: boolean) => void;
  onError: (error: string | null) => void;
}

export default function VideoAnalyzer({
  onAnalysisComplete,
  onLoadingChange,
  onError,
}: VideoAnalyzerProps) {
  const [videoUrl, setVideoUrl] = useState('');
  const [options, setOptions] = useState({
    analyze_emotions: true,
    generate_titles: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onError(null);
    onLoadingChange(true);

    try {
      // Validate video URL
      if (!videoUrl.startsWith('https://')) {
        throw new Error('Please enter a valid HTTPS URL');
      }

      const request: VideoAnalysisRequest = {
        video_url: videoUrl,
        analyze_emotions: options.analyze_emotions,
        generate_titles: options.generate_titles
      };

      // Add retry logic
      let retries = 3;
      let lastError = null;

      while (retries > 0) {
        try {
          console.log('Attempting to connect to:', `${process.env.NEXT_PUBLIC_API_URL}/api/analyze`);
          
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analyze`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: JSON.stringify(request),
            mode: 'cors',
            credentials: 'omit',
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Failed to analyze video' }));
            console.error('Server response:', response.status, errorData);
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          console.log('API Response:', JSON.stringify(data, null, 2));
          onAnalysisComplete(data);
          return; // Success, exit the function
        } catch (error) {
          console.error('Attempt failed:', error);
          lastError = error;
          retries--;
          if (retries > 0) {
            console.log(`Retrying... ${retries} attempts left`);
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before retrying
          }
        }
      }

      // If we get here, all retries failed
      throw lastError || new Error('Failed to analyze video after multiple attempts');

    } catch (err) {
      console.error('API Error:', err);
      onError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      onLoadingChange(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="videoUrl" className="block text-sm font-medium mb-2">
          Jelly Video URL
        </label>
        <input
          type="url"
          id="videoUrl"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          placeholder="https://jelly-shareables.s3.amazonaws.com/..."
          className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          required
        />
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Analysis Options</h3>
        <div className="space-y-2">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={options.analyze_emotions}
              onChange={(e) =>
                setOptions({ ...options, analyze_emotions: e.target.checked })
              }
              className="rounded border-gray-700 bg-gray-800"
            />
            <span>Analyze Emotions</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={options.generate_titles}
              onChange={(e) =>
                setOptions({ ...options, generate_titles: e.target.checked })
              }
              className="rounded border-gray-700 bg-gray-800"
            />
            <span>Generate Titles</span>
          </label>
        </div>
      </div>

      <button
        type="submit"
        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
      >
        Analyze Video
      </button>
    </form>
  );
}