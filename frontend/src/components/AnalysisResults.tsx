import { VideoAnalysisResponse } from '@/types';

interface AnalysisResultsProps {
  analysis: VideoAnalysisResponse;
}

export default function AnalysisResults({ analysis }: AnalysisResultsProps) {
  console.log('AnalysisResults received:', JSON.stringify(analysis, null, 2));
  console.log('Summary value:', analysis.summary);
  console.log('Setting value:', analysis.setting);
  console.log('Conversation Topic value:', analysis.conversation_topic);
  
  return (
    <div className="mt-8 space-y-8">
      {/* Summary Section */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Summary</h2>
        <p className="text-gray-200 leading-relaxed">{analysis.summary || "No summary available"}</p>
      </section>

      {/* Context Section */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Context</h2>
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-300 mb-2">Setting and Context</h3>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <p className="text-gray-200 whitespace-pre-wrap">
                {analysis.setting && analysis.setting.trim() !== '' 
                  ? analysis.setting 
                  : "No setting information available"}
              </p>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-300 mb-2">Topic and Key Points</h3>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <p className="text-gray-200 whitespace-pre-wrap">
                {analysis.conversation_topic && analysis.conversation_topic.trim() !== '' 
                  ? analysis.conversation_topic.replace(/^\d+\.\s*/, '') // Remove leading numbers and dots
                  : "No topic information available"}
              </p>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-300 mb-2">Mood and Tone</h3>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <p className="text-gray-200 capitalize whitespace-pre-wrap">
                {analysis.mood || "No mood information available"}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Key Moments Section */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Key Moments</h2>
        <div className="space-y-3">
          {analysis.key_moments.map((moment, index) => (
            <div key={index} className="flex items-start space-x-4">
              <span className="text-blue-400 font-mono">
                {formatTimestamp(moment.timestamp)}
              </span>
              <p className="text-gray-200">{moment.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Emotions Section */}
      {analysis.emotions && (
        <section className="bg-gray-800/50 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Emotional Analysis</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-gray-300">Overall Tone</h3>
              <p className="text-gray-200">{analysis.emotions.overall_tone}</p>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-300">Emotional Progression</h3>
              <p className="text-gray-200">{analysis.emotions.emotional_progression}</p>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-300">Dominant Emotions</h3>
              <p className="text-gray-200">{analysis.emotions.dominant_emotions}</p>
            </div>
          </div>
        </section>
      )}

      {/* Titles Section */}
      {analysis.titles && analysis.titles.length > 0 && (
        <section className="bg-gray-800/50 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Suggested Titles</h2>
          <ul className="space-y-2">
            {analysis.titles.map((title, index) => (
              <li key={index} className="text-gray-200">{title}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Suggested Caption */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Suggested Caption</h2>
        <p className="text-gray-200">{analysis.suggested_caption || "No caption available"}</p>
      </section>

      {/* Additional Information */}
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Additional Information</h2>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-medium text-gray-300">Content Safety Score</h3>
            <div className="flex items-center space-x-2">
              <div className="w-full bg-gray-700 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full"
                  style={{ width: `${analysis.safety_score * 100}%` }}
                ></div>
              </div>
              <span className="text-gray-200">{(analysis.safety_score * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function formatTimestamp(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}
