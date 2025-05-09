export interface VideoAnalysisRequest {
    video_url: string;
    language?: string;
    analyze_emotions?: boolean;
    generate_titles?: boolean;
  }
  
  export interface VideoAnalysisResponse {
    summary: string;
    setting: string;
    mood: string;
    conversation_topic: string;
    suggested_caption: string;
    key_moments: Array<{
      timestamp: number;
      description: string;
    }>;
    emotions?: {
      overall_tone: string;
      emotional_progression: string;
      key_moments: Array<{
        timestamp: number;
        emotion: string;
      }>;
      dominant_emotions: string;
    };
    titles?: string[];
    safety_score: number;
  }