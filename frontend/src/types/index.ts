export interface VideoAnalysisRequest {
    video_url: string;
    language?: string;
    analyze_emotions?: boolean;
    generate_titles?: boolean;
}

export interface VideoAnalysisResponse {
    frame_analysis?: {
        frame_descriptions?: string[];
        summary?: string;
    };
    transcription_analysis?: {
        analysis?: string;
        key_points?: string[];
    };
    content_safety?: number;
    emotions?: {
        emotional_analysis?: string;
        mood_summary?: string;
    };
    titles?: {
        suggested_titles: string[];
        best_title: string;
    };
    fun_caption?: string;
}