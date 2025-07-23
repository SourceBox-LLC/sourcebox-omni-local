import replicate
import os
from dotenv import load_dotenv
load_dotenv()



def generate_image(prompt: str, save_path: str = "output.png") -> str:
    """
    Generate an image using the Replicate API.
    
    Args:
        prompt (str): The prompt to generate the image from
        save_path (str, optional): The path to save the generated image
    
    Returns:
        str: The path to the saved image or error message
    """
    # Or create a client with the token
    client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

    try:
        output = client.run(
            "google/imagen-4",
            input={
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "output_format": "jpg",
                "safety_filter_level": "block_medium_and_above"
            }
        )
        
        # To access the file URL:
        print(output.url)
        
        if save_path:
            # To write the file to disk:
            with open(save_path, "wb") as file:
                file.write(output.read())
            
            print(f"Image saved as {save_path}")
            return f"Image saved as {save_path}"

        else:
            # To write the file to disk:
            with open("output.png", "wb") as file:
                file.write(output.read())
            
            print(f"Image saved as output.png")
            return f"Image saved as output.png"
        
    except Exception:
        # Store exception in a variable with a different name to avoid PyInstaller scope issues
        import traceback
        error_message = traceback.format_exc()
        print(f"Error generating image: {error_message}")
        print(f"Image generation error: {error_message}")
        return f"Error generating image: {str(error_message.splitlines()[-1])} - please check logs"


if __name__ == "__main__":
    user_input = input("Enter a prompt: ")
    save_path = "output.png"
    generate_image(user_input, save_path)
