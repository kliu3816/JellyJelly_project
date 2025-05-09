import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api():
    # Get the API URL from environment variable or default to localhost
    api_url = os.getenv('API_URL', 'http://localhost:10000')
    
    # Test the root endpoint
    print("\nTesting root endpoint...")
    try:
        response = requests.get(f"{api_url}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing root endpoint: {str(e)}")

    # Test the debug endpoint
    print("\nTesting debug endpoint...")
    try:
        response = requests.get(f"{api_url}/debug/env")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error testing debug endpoint: {str(e)}")

    # Test the analyze endpoint with a sample video URL
    print("\nTesting analyze endpoint...")
    test_video_url = "https://jelly-shareables.s3.amazonaws.com/2771CE78-B149-4807-8CE1-AE615BA31E8D/2771CE78-B149-4807-8CE1-AE615BA31E8D_original.mp4"  # Replace with your test video URL
    try:
        response = requests.post(
            f"{api_url}/api/analyze",
            json={
                "video_url": test_video_url,
                "analyze_emotions": True,
                "generate_titles": True
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Analysis request successful!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error testing analyze endpoint: {str(e)}")

if __name__ == "__main__":
    print("Starting API tests...")
    test_api()
    print("\nAPI tests completed!") 