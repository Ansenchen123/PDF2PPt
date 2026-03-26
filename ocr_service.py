import os
import json
import time
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv

# Initial load (optional, useful for CLI)
load_dotenv()
DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY")

if DEFAULT_API_KEY:
    genai.configure(api_key=DEFAULT_API_KEY)

def configure_gemini(api_key: str):
    """Re-configures the Gemini API with a new key."""
    genai.configure(api_key=api_key)

def extract_text_and_coords(image_path: str) -> List[Dict[str, Any]]:
    """
    Uploads an image to Gemini and extracts text with bounding box coordinates.
    """
    # Use the 'gemini-3-flash-preview' as requested
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
    prompt = """
    Please extract all the text from this image.
    For each block of text, provide the exact text content and the bounding box coordinates.
    Return the result as a JSON array of objects.
    Each object should have:
    - "text": The text content string.
    - "box_2d": [ymin, xmin, ymax, xmax] where coordinates are normalized 0-1000.
    
    Output strictly valid JSON only. Do not wrap in markdown code blocks.
    """
    
    try:
        sample_file = genai.upload_file(path=image_path, display_name="PDF Page")
        print(f"Uploaded file: {sample_file.name}")
        
        # Verify file state
        while sample_file.state.name == "PROCESSING":
            print("  - Waiting for file processing...")
            time.sleep(1) # Reduced to 1s for responsiveness
            sample_file = genai.get_file(sample_file.name)
            
        if sample_file.state.name != "ACTIVE":
            print(f"  - Error: File state is {sample_file.state.name}. Cannot proceed.")
            return []

        generation_config = {"response_mime_type": "application/json"}
        response = model.generate_content([sample_file, prompt], generation_config=generation_config)
        
        # Clean potential markdown formatting (though JSON mode usually avoids this, it's safe to keep)
        text_response = response.text.strip()
        if text_response.startswith("```json"):
            text_response = text_response[7:-3].strip()
        elif text_response.startswith("```"):
            text_response = text_response[3:-3].strip()
            
        try:
            data = json.loads(text_response)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Raw Response: {text_response}")
            return []
        
        # Cleanup
        try:
            genai.delete_file(sample_file.name)
            print(f"  - Deleted file: {sample_file.name}")
        except Exception as cleanup_error:
            print(f"  - Warning: Could not delete file {sample_file.name}: {cleanup_error}")
        
        # Ensure it's a list
        if isinstance(data, dict) and "text_blocks" in data:
            return data["text_blocks"]
        elif isinstance(data, list):
            return data
        else:
            print("Unexpected JSON format from Gemini.")
            return []
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # If API key is invalid, this will likely raise an error
        raise e 
