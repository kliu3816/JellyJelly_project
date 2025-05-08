'use client';

import { useState } from 'react';
import VideoAnalyzer from '@/components/VideoAnalyzer';
import AnalysisResults from '@/components/AnalysisResults';
import { VideoAnalysisResponse } from '@/types';

export default function Home() {
  const [analysis, setAnalysis] = useState<VideoAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <main className="min-h-screen">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8">
          JellyJelly Video Analyzer
        </h1>
        
        <div className="max-w-4xl mx-auto">
          <VideoAnalyzer
            onAnalysisComplete={setAnalysis}
            onLoadingChange={setLoading}
            onError={setError}
          />
          
          {loading && (
            <div className="mt-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
              <p className="mt-4">Analyzing your video...</p>
            </div>
          )}
          
          {error && (
            <div className="mt-8 p-4 bg-red-500/20 border border-red-500 rounded-lg">
              <p className="text-red-200">{error}</p>
            </div>
          )}
          
          {analysis && <AnalysisResults analysis={analysis} />}
        </div>
      </div>
    </main>
  );
}
