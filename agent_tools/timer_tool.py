#!/usr/bin/env python3
"""
Simple Timer Tool
Directly opens the timer GUI using subprocess
"""

import subprocess
import os
import re


def parse_time_duration(duration_str):
    """Parse natural language duration into seconds.
    
    Args:
        duration_str (str): Duration like "5 minutes", "30 seconds", "1 hour"
        
    Returns:
        int: Duration in seconds
        
    Raises:
        ValueError: If duration format is invalid
    """
    if not duration_str or not isinstance(duration_str, str):
        raise ValueError("Duration must be a non-empty string")
    
    duration_str = duration_str.lower().strip()
    
    # If it's just a number, assume minutes
    if duration_str.isdigit():
        return int(duration_str) * 60
    
    # Parse hours, minutes, and seconds
    total_seconds = 0
    
    # Hours pattern
    hours_match = re.search(r'(\d+)\s*(?:hours?|hrs?|h)', duration_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Minutes pattern
    minutes_match = re.search(r'(\d+)\s*(?:minutes?|mins?|m)(?!s)', duration_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    # Seconds pattern
    seconds_match = re.search(r'(\d+)\s*(?:seconds?|secs?|s)', duration_str)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    
    if total_seconds == 0:
        raise ValueError(f"Could not parse duration: '{duration_str}'. Use format like '5 minutes', '30 seconds', '1 hour'")
    
    return total_seconds


def format_duration(seconds):
    """Format seconds into a human-readable duration string."""
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return f"{minutes} minute{'s' if minutes != 1 else ''} and {remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"


def set_timer(duration_input):
    """Set a timer by directly opening the timer GUI with specified duration.
    
    Args:
        duration_input (str): Duration like "5 minutes", "30 seconds", "1 hour"
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Parse the duration input
        seconds = parse_time_duration(duration_input)
        
        if seconds <= 0:
            return {
                "success": False,
                "message": "Duration must be greater than 0 seconds"
            }
        
        # Direct path to the timer GUI
        timer_path = r"C:\Users\S'Bussiso\Desktop\Local Agent\agent_tools\flet_timer_tool\main.py"
        
        # Use the current Python executable to ensure same environment
        import sys
        python_exe = sys.executable
        cmd = [python_exe, timer_path, "--set", str(seconds)]
        
        # Start the timer application
        process = subprocess.Popen(cmd)
        
        # Format duration for user-friendly message
        duration_str = format_duration(seconds)
        
        return {
            "success": True,
            "message": f"Timer set for {duration_str}. Timer window opened.",
            "duration_seconds": seconds,
            "process_id": process.pid
        }
        
    except ValueError as e:
        return {
            "success": False,
            "message": f"Invalid duration format: {str(e)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to start timer: {str(e)}"
        }


if __name__ == "__main__":
    # Test the timer tool
    result = set_timer("test")
    print(f"Result: {result}")
