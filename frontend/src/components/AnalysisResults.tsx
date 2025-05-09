import { VideoAnalysisResponse } from '@/types';

interface AnalysisResultsProps {
  analysis: VideoAnalysisResponse;
}

export default function AnalysisResults({ analysis }: AnalysisResultsProps) {
  console.log('AnalysisResults received:', JSON.stringify(analysis, null, 2));

  const handleDownload = () => {
    const dataStr = JSON.stringify(analysis, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = 'video-analysis.json';
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="mt-8 space-y-8">
      {/* Download Button */}
      <div className="flex justify-end">
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors flex items-center space-x-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
          <span>Download Analysis</span>
        </button>
      </div>

      {/* Summary Section */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Summary</h2>
        <p className="text-gray-200 leading-relaxed">
          {analysis.frame_analysis?.summary || analysis.transcription_analysis?.analysis || "No summary available"}
        </p>
      </section>

      {/* Fun TikTok Caption Section */}
      {typeof analysis.fun_caption === 'string' && analysis.fun_caption.trim() !== '' && (
        <section className="bg-gray-800/50 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">TikTok-Inspired Caption</h2>
          <p className="text-pink-400 text-lg">{analysis.fun_caption}</p>
        </section>
      )}

      {/* Key Points Section */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Key Points</h2>
        <ul className="list-disc pl-6 text-gray-200">
          {(analysis.transcription_analysis?.key_points || []).map((point: string, idx: number) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </section>

      {/* Frame Descriptions Section */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Frame Descriptions</h2>
        <ul className="list-decimal pl-6 text-gray-200">
          {(analysis.frame_analysis?.frame_descriptions || []).map((desc: string, idx: number) => (
            <li key={idx}>{desc}</li>
          ))}
        </ul>
      </section>

      {/* Emotions Section */}
      {analysis.emotions && (
        <section className="bg-gray-800/50 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Emotional Analysis</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-gray-300">Overall Mood</h3>
              <p className="text-gray-200">{analysis.emotions.mood_summary || "No mood information available"}</p>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-300">Emotional Analysis</h3>
              <p className="text-gray-200">{analysis.emotions.emotional_analysis || "No emotional analysis available"}</p>
            </div>
          </div>
        </section>
      )}

      {/* Titles Section */}
      {Array.isArray(analysis.titles?.suggested_titles) && analysis.titles.suggested_titles.length > 0 && (
        <section className="bg-gray-800/50 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Suggested Titles</h2>
          <ul className="space-y-2">
            {analysis.titles.suggested_titles.map((title: string, index: number) => (
              <li key={index} className="text-gray-200">{title}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Content Safety Score */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Content Safety Score</h2>
        <div className="flex items-center space-x-2">
          <div className="w-full bg-gray-700 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ width: `${((analysis.content_safety ?? 0) * 100).toFixed(0)}%` }}
            ></div>
          </div>
          <span className="text-gray-200">{((analysis.content_safety ?? 0) * 100).toFixed(0)}%</span>
        </div>
      </section>
    </div>
  );
}
