from datetime import datetime
import pyautogui
import os
import sys
from pathlib import Path
import logging

# Configure logger
logger = logging.getLogger(__name__)

def get_screenshots_folder():
    """Get a reliable folder path to store screenshots"""
    try:
        # Simple approach: use desktop folder which is reliable across Windows versions
        if os.name == 'nt':  # Windows
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            screenshots_folder = os.path.join(desktop_path, 'Screenshots')
        else:  # macOS/Linux
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            screenshots_folder = os.path.join(desktop_path, 'Screenshots')
        
        # Ensure the folder exists
        if not os.path.exists(screenshots_folder):
            logger.info(f"Creating Screenshots folder: {screenshots_folder}")
            os.makedirs(screenshots_folder)
            
        return screenshots_folder
    except Exception:
        import traceback
        error_message = traceback.format_exc()
        # Fallback to current directory if there's an error
        logger.error(f"Error creating Screenshots folder: {error_message}")
        cwd = os.getcwd()
        logger.info(f"Falling back to current working directory: {cwd}")
        return cwd

def take_screenshot(window_title: str = None) -> str:
    """
    Capture a screenshot and save it to the default Screenshots folder.
    Optionally activates a window by title before capturing.
    
    Args:
        window_title: Optional window title to focus before capturing
        
    Returns:
        Path to the saved screenshot file or error message
    """
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Always use Screenshots folder
        screenshots_folder = get_screenshots_folder()
        path = os.path.join(screenshots_folder, f"screenshot_{ts}.png")
            
        # Make sure parent directory exists
        parent_dir = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
            logger.info(f"Created directory: {parent_dir}")

        # Try to focus window if title provided
        if window_title:
            try:
                import pygetwindow as gw
                wins = gw.getWindowsWithTitle(window_title)
                if wins:
                    wins[0].activate()
                    logger.info(f"Activated window: {window_title}")
                else:
                    logger.warning(f"No window found with title: {window_title}")
            except Exception as e:
                import traceback
                error_message = traceback.format_exc()
                logger.warning(f"Error focusing window: {str(e)}")
                print(f"Window focus error: {str(e)}")

        # Take and save screenshot - try multiple methods for PyInstaller compatibility
        try:
            # Method 1: Standard PyAutoGUI
            img = pyautogui.screenshot()
            img.save(path)
            logger.info(f"Screenshot saved to {path} using standard PyAutoGUI")
            return f"Screenshot saved to {path}"
        except Exception:
            try:
                # Method 2: Alternative using MSS library (more compatible with PyInstaller)
                import mss
                with mss.mss() as sct:
                    # Get the first monitor
                    monitor = sct.monitors[1]
                    # Capture the screen
                    img = sct.grab(monitor)
                    # Save the screenshot
                    import mss.tools
                    mss.tools.to_png(img.rgb, img.size, output=path)
                    logger.info(f"Screenshot saved to {path} using MSS library")
                    return f"Screenshot saved to {path}"
            except Exception:
                try:
                    # Method 3: Using ImageGrab from PIL directly (last resort)
                    from PIL import ImageGrab
                    img = ImageGrab.grab()
                    img.save(path)
                    logger.info(f"Screenshot saved to {path} using PIL ImageGrab")
                    return f"Screenshot saved to {path}"
                except Exception:
                    # All methods failed, log detailed error
                    import traceback
                    error_message = traceback.format_exc()
                    logger.error(f"All screenshot methods failed: {error_message}")
                    return f"Screenshot error: All capture methods failed - please install 'mss' library with pip install mss"
    except Exception:
        import traceback
        error_message = traceback.format_exc()
        print(f"Screenshot error: {error_message}")
        print(f"Screenshot error: {error_message}")
        return f"Screenshot error: {str(error_message.splitlines()[-1])} - please check logs"

if __name__ == "__main__":
    # Set up logging for direct script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Take screenshot with default settings
    result = take_screenshot()
    print(result)