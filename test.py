import replicate
import os
from pathlib import Path

def describe_image(image_path, prompt="Describe this image in as much detail as possible"):
    """
    Describe an image using Replicate's Moondream2 model
    
    Args:
        image_path: Path to the local image file
        prompt: Custom prompt for image description
    
    Returns:
        str: Detailed description of the image
    """
    # Validate file exists
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}"
    
    # Validate file is an image
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    file_ext = Path(image_path).suffix.lower()
    if file_ext not in valid_extensions:
        return f"Error: Unsupported file type {file_ext}. Supported: {', '.join(valid_extensions)}"
    
    try:
        print(f"🖼️ Analyzing image: {os.path.basename(image_path)}")
        print(f"📝 Prompt: {prompt}")
        print("🔄 Processing with Moondream2...\n")
        
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
            print(item, end="", flush=True)
        
        print("\n\n✅ Analysis complete!")
        return description
        
    except Exception as e:
        error_msg = f"Error analyzing image: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

def main():
    """Interactive CLI for image description"""
    print("🎨 Image Description Tool with Moondream2")
    print("=" * 40)
    
    while True:
        # Get image path from user
        image_path = input("\n📁 Enter image file path (or 'quit' to exit): ").strip()
        
        if image_path.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        # Remove quotes if user wrapped path in quotes
        image_path = image_path.strip('"\'')
        
        # Get custom prompt (optional)
        custom_prompt = input("📝 Custom prompt (or press Enter for default): ").strip()
        if not custom_prompt:
            custom_prompt = "Describe this image in as much detail as possible"
        
        # Analyze the image
        result = describe_image(image_path, custom_prompt)
        
        # Ask if user wants to continue
        continue_choice = input("\n🔄 Analyze another image? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            print("👋 Goodbye!")
            break

if __name__ == "__main__":
    main()