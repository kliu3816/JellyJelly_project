import requests
import json
from pprint import pprint

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/api/health")
    print("\nTesting health endpoint:")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_video_analysis():
    """Test the video analysis endpoint"""
    # Example Jelly video URL
    video_url = "https://jelly-shareables.s3.amazonaws.com/B3C5069A-C7E9-4598-9298-E70275B8CFF7/B3C5069A-C7E9-4598-9298-E70275B8CFF7_original.mp4"
    
    payload = {
        "video_url": video_url,
        "language": "en",
        "analyze_emotions": True,
        "generate_titles": True,
        "detect_speakers": True
    }
    
    print("\nTesting video analysis endpoint:")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/analyze", json=payload)
        print(f"Status code: {response.status_code}")
        print("Response:")
        pprint(response.json())
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Test health endpoint
    test_health()
    
    # Test video analysis endpoint
    test_video_analysis() 