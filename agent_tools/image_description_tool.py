#!/usr/bin/env python3
"""
Image Description Tool using Replicate's Moondream2 model
Analyzes images and provides detailed text descriptions
"""

import replicate
import os
from pathlib import Path

def describe_image(image_path, prompt="Describe this image in as much detail as possible"):
    """
    Describe an image using Replicate's Moondream2 model
    
    Args:
        image_path (str): Path to the local image file
        prompt (str): Custom prompt for image description
    
    Returns:
        str: Detailed description of the image or error message
    """
    try:
        # Validate file exists
        if not os.path.exists(image_path):
            return f"Error: Image file not found at {image_path}"
        
        # Validate file is an image
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_ext = Path(image_path).suffix.lower()
        if file_ext not in valid_extensions:
            return f"Error: Unsupported file type {file_ext}. Supported: {', '.join(valid_extensions)}"
        
        # Get file size for user info
        file_size = os.path.getsize(image_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"🖼️ Analyzing image: {os.path.basename(image_path)} ({file_size_mb:.1f} MB)")
        
        # Open and upload the local image file to Replicate
        with open(image_path, "rb") as image_file:
            output = replicate.run(
                "lucataco/moondream2:72ccb656353c348c1385df54b237eeb7bfa874bf11486cf0b9473e691b662d31",
                input={
                    "image": image_file,
                    "prompt": prompt
                }
            )
        
        # Collect the streaming output
        description = ""
        for item in output:
            description += str(item)
        
        # Format the result nicely
        result = f"📸 **Image Analysis Results**\n\n"
        result += f"**File:** {os.path.basename(image_path)}\n"
        result += f"**Size:** {file_size_mb:.1f} MB\n"
        result += f"**Prompt:** {prompt}\n\n"
        result += f"**Description:**\n{description.strip()}"
        
        return result
        
    except Exception as e:
        error_msg = f"Error analyzing image: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

def test_image_description():
    """Test function for the image description tool"""
    print("🎨 Testing Image Description Tool")
    print("=" * 40)
    
    # Test with a non-existent file
    test_result = describe_image("nonexistent.jpg")
    print("Test 1 - Non-existent file:")
    print(test_result)
    print()
    
    # Test with invalid file type
    test_result = describe_image("test.txt")
    print("Test 2 - Invalid file type:")
    print(test_result)
    print()
    
    print("✅ Basic validation tests completed")
    print("To test with real images, provide actual image file paths")

if __name__ == "__main__":
    test_image_description()
