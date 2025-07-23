#!/usr/bin/env python3
"""
Windows Wallpaper Setter Tool
Sets the desktop wallpaper from an image file path using Windows API
"""
import os
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Dict, Any
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Windows API constants
SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

def set_wallpaper(image_path: str) -> str:
    """
    Set the Windows desktop wallpaper to the specified image.
    
    Args:
        image_path (str): Full path to the image file
        
    Returns:
        str: Success message or error description
    """
    try:
        # Convert to Path object and resolve
        image_file = Path(image_path).resolve()
        
        # Check if file exists
        if not image_file.exists():
            return f"❌ Error: Image file does not exist: {image_file}"
        
        # Check if it's a file (not a directory)
        if not image_file.is_file():
            return f"❌ Error: Path is not a file: {image_file}"
        
        # Check if it's a supported image format
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        if image_file.suffix.lower() not in supported_formats:
            return f"❌ Error: Unsupported image format: {image_file.suffix}. Supported formats: {', '.join(supported_formats)}"
        
        # Convert path to string for Windows API
        wallpaper_path = str(image_file)
        
        # Call Windows API to set wallpaper
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            wallpaper_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        
        if result:
            logger.info(f"Successfully set wallpaper to: {wallpaper_path}")
            return f"✅ Successfully set wallpaper to: {wallpaper_path}"
        else:
            # Get the last Windows error
            error_code = ctypes.windll.kernel32.GetLastError()
            logger.error(f"Failed to set wallpaper. Windows error code: {error_code}")
            return f"❌ Failed to set wallpaper. Windows error code: {error_code}"
            
    except Exception:
        import traceback
        error_message = traceback.format_exc()
        logger.exception("Error setting wallpaper")
        print(f"Wallpaper setting error: {error_message}")
        return f"❌ Error setting wallpaper: {str(error_message.splitlines()[-1])} - please check logs"

def get_current_wallpaper() -> Dict[str, Any]:
    """
    Get the current desktop wallpaper path.
    Note: This may not work reliably on Windows 10/11 due to how the OS handles wallpapers.
    
    Returns:
        Dict[str, Any]: Result dictionary with current wallpaper path
    """
    try:
        # Method 1: Try the traditional Windows API
        buffer = ctypes.create_unicode_buffer(260)  # MAX_PATH
        result = ctypes.windll.user32.SystemParametersInfoW(
            73,  # SPI_GETDESKWALLPAPER
            260,  # Buffer size
            buffer,
            0
        )
        
        if result and buffer.value and buffer.value.strip():
            current_path = buffer.value
            return {
                "success": True,
                "path": current_path,
                "message": f"Current wallpaper: {current_path}"
            }
        
        # Method 2: Try reading from Windows Registry (fallback)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Control Panel\Desktop")
            wallpaper_path, _ = winreg.QueryValueEx(key, "Wallpaper")
            winreg.CloseKey(key)
            
            if wallpaper_path and wallpaper_path.strip():
                return {
                    "success": True,
                    "path": wallpaper_path,
                    "message": f"Current wallpaper (from registry): {wallpaper_path}"
                }
        except Exception:
            pass
        
        # If both methods fail
        return {
            "success": False,
            "error": "Unable to retrieve current wallpaper path. This is common on Windows 10/11 with dynamic wallpapers or slideshow mode.",
            "note": "The wallpaper setter will still work for setting new wallpapers."
        }
            
    except Exception:
        import traceback
        error_message = traceback.format_exc()
        logger.exception("Error getting current wallpaper")
        return {
            "success": False,
            "error": f"Error getting current wallpaper: {str(error_message.splitlines()[-1])} - please check logs"
        }

# For testing when run directly
if __name__ == "__main__":
    print("Windows Wallpaper Setter Tool")
    print("=" * 30)
    
    # Get current wallpaper first
    print("\n1. Getting current wallpaper...")
    current = get_current_wallpaper()
    if current["success"]:
        print(f"✅ {current['message']}")
    else:
        print(f"❌ {current['error']}")
        if "note" in current:
            print(f"ℹ️  {current['note']}")
    
    # Ask user for new wallpaper path
    print("\n2. Set new wallpaper:")
    image_path = input("Enter the full path to your image file: ").strip().strip('"')
    
    if not image_path:
        print("❌ No path provided. Exiting.")
        exit()
    
    print(f"\nAttempting to set wallpaper to: {image_path}")
    result = set_wallpaper(image_path)
    print(result)
    
    if "Successfully set wallpaper" in result:
        print("\n🎉 Wallpaper should now be updated on your desktop!")
    else:
        print("\n💡 Troubleshooting tips:")
        print("- Make sure the file path is correct and the file exists")
        print("- Ensure the image is in a supported format (JPG, PNG, BMP, etc.)")
        print("- Try using a different image file")
        print("- Make sure you have permission to change system settings")
