import { VideoAnalysisResponse } from '@/types';

interface AnalysisResultsProps {
  analysis: VideoAnalysisResponse;
}

export default function AnalysisResults({ analysis }: AnalysisResultsProps) {
  return (
    <div className="mt-8 space-y-8">
      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Summary</h2>
        <p className="text-gray-300">{analysis.summary}</p>
      </section>

      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-lg font-medium mb-2">Setting</h3>
            <p className="text-gray-300">{analysis.setting}</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Mood</h3>
            <p className="text-gray-300">{analysis.mood}</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Conversation Topic</h3>
            <p className="text-gray-300">{analysis.conversation_topic}</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Suggested Caption</h3>
            <p className="text-gray-300">{analysis.suggested_caption}</p>
          </div>
        </div>
      </section>

      {analysis.emotions && (
        <section className="bg-gray-800/50 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Emotional Analysis</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium mb-2">Overall Tone</h3>
              <p className="text-gray-300">{analysis.emotions.overall_tone}</p>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-2">Emotional Progression</h3>
              <p className="text-gray-300">{analysis.emotions.emotional_progression}</p>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-2">Dominant Emotions</h3>
              <p className="text-gray-300">{analysis.emotions.dominant_emotions}</p>
            </div>
          </div>
        </section>
      )}

      {analysis.titles && (
        <section className="bg-gray-800/50 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Generated Titles</h2>
          <ul className="space-y-2">
            {analysis.titles.map((title, index) => (
              <li key={index} className="text-gray-300">
                {title}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Key Moments</h2>
        <div className="space-y-4">
          {analysis.key_moments.map((moment, index) => (
            <div key={index} className="flex items-start space-x-4">
              <span className="text-blue-400 font-mono">
                {moment.timestamp.toFixed(1)}s
              </span>
              <p className="text-gray-300">{moment.description}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="bg-gray-800/50 rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4">Safety Score</h2>
        <div className="flex items-center space-x-4">
          <div className="w-full bg-gray-700 rounded-full h-4">
            <div
              className="bg-green-500 h-4 rounded-full"
              style={{ width: `${analysis.safety_score * 100}%` }}
            ></div>
          </div>
          <span className="text-lg font-medium">
            {(analysis.safety_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
}
