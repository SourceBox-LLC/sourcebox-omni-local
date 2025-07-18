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
    except Exception as e:
        # Fallback to current directory if there's an error
        logger.error(f"Error creating Screenshots folder: {str(e)}")
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
            except Exception as window_error:
                logger.warning(f"Error focusing window: {str(window_error)}")

        # Take and save screenshot
        img = pyautogui.screenshot()
        img.save(path)
        logger.info(f"Screenshot saved to {path}")
        return f"Screenshot saved to {path}"
    except Exception as e:
        error_msg = f"Error taking screenshot: {str(e)}"
        logger.exception(error_msg)
        return error_msg


if __name__ == "__main__":
    # Set up logging for direct script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Take screenshot with default settings
    result = take_screenshot()
    print(result)