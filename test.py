#!/usr/bin/env python3
"""
Screen Recording Tool for Local Agent
Provides functionality to record the screen or a specific window
"""
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing optional dependencies
DEPENDENCIES_MET = True
MISSING_DEPENDENCIES = []

try:
    import numpy as np
except ImportError:
    DEPENDENCIES_MET = False
    MISSING_DEPENDENCIES.append("numpy")

try:
    import cv2
except ImportError:
    DEPENDENCIES_MET = False
    MISSING_DEPENDENCIES.append("opencv-python")

try:
    import pyautogui
except ImportError:
    DEPENDENCIES_MET = False
    MISSING_DEPENDENCIES.append("pyautogui")

# Default settings
DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Recordings")
DEFAULT_FPS = 20
DEFAULT_CODEC = "mp4v"  # MP4 codec
DEFAULT_EXTENSION = "mp4"
DEFAULT_QUALITY = 95  # 0-100


class ScreenRecorder:
    """Screen recording tool that can record the desktop or a specific window."""
    
    def __init__(self):
        """Initialize the screen recorder with default settings."""
        self.is_recording = False
        self.output_dir = DEFAULT_OUTPUT_DIR
        self.fps = DEFAULT_FPS
        self.codec = DEFAULT_CODEC
        self.extension = DEFAULT_EXTENSION
        self.quality = DEFAULT_QUALITY
        self.recording_thread = None
        self.video_writer = None
        self.start_time = None
        self.recording_file = None
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def check_dependencies(self) -> Dict[str, Any]:
        """Check if all required dependencies are installed."""
        if not DEPENDENCIES_MET:
            return {
                "success": False,
                "error": f"Missing required dependencies: {', '.join(MISSING_DEPENDENCIES)}",
                "missing": MISSING_DEPENDENCIES
            }
        return {"success": True}
    
    def _generate_filename(self) -> str:
        """Generate a unique filename for the recording."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(self.output_dir, f"Screen_Recording_{timestamp}.{self.extension}")
    
    def start_recording(self, window_title: Optional[str] = None, duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Start recording the screen or a specific window.
        
        Args:
            window_title: Title of the window to record (None for full desktop)
            duration: Maximum recording duration in seconds (None for manual stop)
            
        Returns:
            Dict with operation status
        """
        # Check dependencies first
        deps_check = self.check_dependencies()
        if not deps_check["success"]:
            return deps_check
            
        # Check if already recording
        if self.is_recording:
            return {
                "success": False,
                "error": "Already recording. Stop current recording first."
            }
            
        try:
            # Create output filename
            self.recording_file = self._generate_filename()
            
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            
            # TODO: If window_title is specified, find and focus the window
            # This would require additional window management functionality
            if window_title:
                # For now, we'll just log that we're ignoring the window title
                logger.warning(f"Window title '{window_title}' specified, but window targeting is not yet implemented")
                logger.info(f"Recording full desktop instead")
            
            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            self.video_writer = cv2.VideoWriter(
                self.recording_file, 
                fourcc, 
                self.fps, 
                (screen_width, screen_height)
            )
            
            if not self.video_writer.isOpened():
                return {
                    "success": False,
                    "error": "Failed to open video writer. Check codec and output directory permissions."
                }
            
            # Start recording
            self.is_recording = True
            self.start_time = time.time()
            end_time = None if duration is None else self.start_time + duration
            
            logger.info(f"Started recording to {self.recording_file}")
            logger.info(f"Press Ctrl+C to stop or wait for {duration}s duration" if duration else "Press Ctrl+C to stop")
            
            try:
                # Main recording loop
                while self.is_recording:
                    # Capture the screen
                    screenshot = pyautogui.screenshot()
                    
                    # Convert the screenshot to an OpenCV compatible format
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Write the frame to the video file
                    self.video_writer.write(frame)
                    
                    # Sleep to maintain the desired frame rate
                    time.sleep(1 / self.fps)
                    
                    # Check if duration has elapsed
                    if end_time and time.time() >= end_time:
                        logger.info(f"Recording duration of {duration}s reached")
                        self.is_recording = False
            
            except KeyboardInterrupt:
                logger.info("Recording stopped by user")
            
            finally:
                # Cleanup
                if self.video_writer:
                    self.video_writer.release()
                
                duration = round(time.time() - self.start_time, 2)
                self.is_recording = False
                
                return {
                    "success": True,
                    "file": self.recording_file,
                    "duration": duration,
                    "message": f"Recording saved to: {self.recording_file} ({duration} seconds)"
                }
                
        except Exception as e:
            logger.exception("Error during recording")
            return {
                "success": False,
                "error": f"Recording failed: {str(e)}"
            }
    
    def stop_recording(self) -> Dict[str, Any]:
        """
        Stop the current recording.
        
        Returns:
            Dict with operation status
        """
        if not self.is_recording:
            return {
                "success": False,
                "error": "No active recording to stop"
            }
            
        self.is_recording = False
        
        # Wait a moment to let the recording thread finish
        time.sleep(0.5)
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        duration = round(time.time() - self.start_time, 2)
        
        return {
            "success": True,
            "file": self.recording_file,
            "duration": duration,
            "message": f"Recording stopped and saved to: {self.recording_file} ({duration} seconds)"
        }
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get current recorder settings.
        
        Returns:
            Dict with current settings
        """
        return {
            "output_dir": self.output_dir,
            "fps": self.fps,
            "codec": self.codec,
            "extension": self.extension,
            "quality": self.quality,
            "is_recording": self.is_recording
        }
    
    def update_settings(self, 
                      output_dir: Optional[str] = None, 
                      fps: Optional[int] = None,
                      codec: Optional[str] = None,
                      extension: Optional[str] = None,
                      quality: Optional[int] = None) -> Dict[str, Any]:
        """
        Update recorder settings.
        
        Args:
            output_dir: Directory to save recordings
            fps: Frames per second
            codec: Video codec (e.g., 'mp4v', 'XVID')
            extension: File extension (e.g., 'mp4', 'avi')
            quality: Video quality (0-100)
            
        Returns:
            Dict with operation status and updated settings
        """
        if self.is_recording:
            return {
                "success": False,
                "error": "Cannot change settings while recording is in progress"
            }
            
        try:
            if output_dir:
                output_dir = os.path.abspath(output_dir)
                os.makedirs(output_dir, exist_ok=True)
                self.output_dir = output_dir
                
            if fps is not None and fps > 0:
                self.fps = fps
                
            if codec:
                self.codec = codec
                
            if extension:
                self.extension = extension
                
            if quality is not None:
                self.quality = max(0, min(100, quality))
                
            return {
                "success": True,
                "settings": self.get_settings(),
                "message": "Settings updated successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update settings: {str(e)}"
            }


def record_screen(duration: Optional[int] = None, window_title: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple function to record the screen for a specified duration.
    
    Args:
        duration: Recording duration in seconds (None for manual stop)
        window_title: Title of the window to record (None for full desktop)
        
    Returns:
        Dict with operation result
    """
    recorder = ScreenRecorder()
    deps_check = recorder.check_dependencies()
    
    if not deps_check["success"]:
        return deps_check
    
    print(f"Recording {'full screen' if window_title is None else f'window: {window_title}'}")
    print(f"Duration: {duration if duration else 'manual stop (Ctrl+C)'} seconds")
    print(f"Output will be saved to: {recorder.output_dir}")
    
    try:
        return recorder.start_recording(window_title=window_title, duration=duration)
    except KeyboardInterrupt:
        return recorder.stop_recording()


# For testing when run directly
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Screen Recording Tool")
    parser.add_argument("--duration", "-d", type=int, default=10,
                        help="Recording duration in seconds (default: 10)")
    parser.add_argument("--window", "-w", type=str, default=None,
                        help="Window title to record (default: full desktop)")
    parser.add_argument("--output", "-o", type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--fps", "-f", type=int, default=DEFAULT_FPS,
                        help=f"Frames per second (default: {DEFAULT_FPS})")
    
    args = parser.parse_args()
    
    # Check dependencies first
    recorder = ScreenRecorder()
    deps_check = recorder.check_dependencies()
    
    if not deps_check["success"]:
        print(f"Error: {deps_check['error']}")
        print("Please install missing dependencies:")
        for dep in deps_check["missing"]:
            print(f"  pip install {dep}")
        sys.exit(1)
    
    # Update settings if provided
    recorder.update_settings(
        output_dir=args.output,
        fps=args.fps
    )
    
    print(f"Starting screen recording...")
    print(f"Press Ctrl+C to stop before the duration")
    
    try:
        result = recorder.start_recording(
            window_title=args.window,
            duration=args.duration
        )
        
        if result["success"]:
            print(result["message"])
        else:
            print(f"Error: {result['error']}")
            
    except KeyboardInterrupt:
        print("\nRecording stopped by user")
        result = recorder.stop_recording()
        
        if result["success"]:
            print(result["message"])