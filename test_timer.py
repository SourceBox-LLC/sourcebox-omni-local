#!/usr/bin/env python3
"""
Test script to debug timer tool wrapper issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.timer_tool import set_timer

def test_timer_wrapper():
    """Test the timer tool directly"""
    print("Testing timer tool wrapper...")
    
    try:
        result = set_timer("10 seconds")
        print(f"Result: {result}")
        
        if isinstance(result, dict):
            if result.get('success', False):
                print(f"Success: {result.get('message', 'Timer set successfully')}")
                print(f"Process ID: {result.get('process_id')}")
                print(f"Duration: {result.get('duration_seconds')} seconds")
            else:
                print(f"Failed: {result.get('message', 'Failed to set timer')}")
        else:
            print(f"Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timer_wrapper()
