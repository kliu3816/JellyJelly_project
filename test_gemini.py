import os
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
import base64
from dotenv import load_dotenv
def test_gemini_api():
    # Get API key
    load_dotenv(dotenv_path=".env", override=True) 

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set")
        return
    
    print(f"API Key found: {api_key[:5]}...{api_key[-5:]}")  # Show first and last 5 chars
    
    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        print("Successfully configured Gemini API")
    except Exception as e:
        print(f"Error configuring Gemini API: {str(e)}")
        return

    # Create model
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("Successfully created Gemini model")
    except Exception as e:
        print(f"Error creating Gemini model: {str(e)}")
        return

    # Test with a sample image
    try:
        # Download a sample image
        image_url = "https://picsum.photos/800/600"  # Random sample image
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        
        # Convert to base64
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr = img_byte_arr.getvalue()
        base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
        
        # Create image part
        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64_image
            }
        ]
        
        print("Testing image analysis...")
        response = model.generate_content([
            "Describe this image in detail",
            image_parts[0]
        ])
        
        if response and hasattr(response, 'text'):
            print("\nSuccess! Gemini API Response:")
            print(response.text)
        else:
            print("Error: Empty response from Gemini API")
            
    except Exception as e:
        print(f"Error during image analysis: {str(e)}")

if __name__ == "__main__":
    test_gemini_api() 