#!/usr/bin/env python3
"""
Close Application by Name Tool
Finds and closes running applications by partial process name match.
"""

import psutil
import time
from typing import List, Dict, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_processes_by_name(process_name: str) -> List[Dict]:
    """
    Find all running processes that match the given process name (case-insensitive partial match)
    
    Args:
        process_name: Partial or full process name to search for
        
    Returns:
        List of dicts containing process info (pid, name, exe, status, username)
    """
    matching_processes = []
    
    for proc in psutil.process_iter():
        try:
            # Get process info directly
            pinfo = {
                'pid': proc.pid,
                'name': proc.name(),
                'exe': 'N/A',
                'status': proc.status(),
                'username': 'N/A'
            }
            
            try:
                pinfo['exe'] = proc.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            try:
                pinfo['username'] = proc.username()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # Check if process name contains our search string (case-insensitive)
            if pinfo['name'] and process_name.lower() in pinfo['name'].lower():
                matching_processes.append(pinfo)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            continue
            
    return matching_processes

def close_process(process_info: Dict, force: bool = False) -> Tuple[bool, str]:
    """
    Attempt to close a process gracefully, with option to force kill
    
    Args:
        process_info: Dictionary containing process info (must contain 'pid')
        force: If True, force kill the process if graceful shutdown fails
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    pid = process_info['pid']
    name = process_info.get('name', 'unknown')
    
    try:
        # Get the process
        process = psutil.Process(pid)
        
        # Try to close gracefully first
        try:
            # Try to close the main window first (if it has one)
            if process.is_running() and process.status() != 'zombie':
                for proc in (process, *process.children(recursive=True)):
                    try:
                        proc.terminate()  # Graceful termination
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Wait for process to terminate
                gone, alive = psutil.wait_procs([process], timeout=3)
                if not alive:  # Process terminated
                    return True, f"Successfully closed {name} (PID: {pid})"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
        # If we get here, graceful termination failed or timed out
        if force:
            try:
                # Try to kill the process tree
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.kill()
                    except:
                        pass
                parent.kill()
                return True, f"Forcefully killed {name} (PID: {pid})"
            except Exception as e:
                return False, f"Failed to force kill {name} (PID: {pid}): {str(e)}"
        else:
            return False, f"Failed to close {name} (PID: {pid}) gracefully. Use force=True to force kill."
            
    except psutil.NoSuchProcess:
        return False, f"Process {name} (PID: {pid}) not found or already closed"
    except Exception as e:
        return False, f"Error closing {name} (PID: {pid}): {str(e)}"

def close_application_by_name(app_name: str, force: bool = False, auto_confirm: bool = True) -> str:
    """
    Close all processes matching the given application name
    
    Args:
        app_name: Partial or full process name to search for
        force: If True, force kill processes that don't close gracefully
        auto_confirm: If True, automatically confirm closing (for agent use)
        
    Returns:
        String with results summary for agent consumption
    """
    processes = find_processes_by_name(app_name)
    
    if not processes:
        return f"No running processes found matching: {app_name}"
    
    # Build result message
    result_msg = f"Found {len(processes)} process(es) matching '{app_name}':\n"
    for idx, proc in enumerate(processes, 1):
        result_msg += f"  {idx}. {proc['name']} (PID: {proc['pid']})\n"
        result_msg += f"     Path: {proc.get('exe', 'N/A')}\n"
        result_msg += f"     User: {proc.get('username', 'N/A')}\n"
    
    # For agent use, auto-confirm closing
    if not auto_confirm:
        # This would be used for interactive mode (not agent)
        return result_msg + "\nUse auto_confirm=True to proceed with closing."
    
    # Close each process
    results = []
    for proc in processes:
        success, message = close_process(proc, force)
        results.append({
            'name': proc['name'],
            'pid': proc['pid'],
            'success': success,
            'message': message
        })
        
        # Add a small delay between closing processes
        time.sleep(0.5)
    
    # Build summary
    success_count = sum(1 for r in results if r['success'])
    result_msg += f"\nClosure Results:\n"
    
    for result in results:
        status = "✓" if result['success'] else "✗"
        result_msg += f"  {status} {result['message']}\n"
    
    result_msg += f"\nSummary: {success_count} of {len(results)} process(es) closed successfully."
    
    # Log the operation
    logger.info(f"Closed {success_count}/{len(results)} processes matching '{app_name}'")
    
    return result_msg

def list_all_processes() -> str:
    """
    List all running processes
    
    Returns:
        String with formatted process list for agent consumption
    """
    try:
        processes = []
        for proc in psutil.process_iter():
            try:
                pinfo = {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'exe': 'N/A',
                    'status': proc.status(),
                    'username': 'N/A'
                }
                try:
                    pinfo['exe'] = proc.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                try:
                    pinfo['username'] = proc.username()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if not processes:
            return "No processes found."
        
        # Format the output
        result = "Currently running processes:\n"
        result += "-" * 80 + "\n"
        result += f"{'PID':<8} {'Name':<30} {'Status':<10} {'Username'}\n"
        result += "-" * 80 + "\n"
        
        for proc in sorted(processes, key=lambda x: x['name'].lower()):
            result += f"{proc['pid']:<8} {proc['name']:<30} {proc['status']:<10} {proc['username']}\n"
        
        result += f"\nTotal processes: {len(processes)}"
        
        return result
        
    except Exception as e:
        return f"Error listing processes: {str(e)}"

# Main functions for agent use
def close_app_by_name(app_name: str, force_kill: bool = False) -> str:
    """
    Main function for agent to close applications by name
    
    Args:
        app_name: Partial or full process name to search for
        force_kill: If True, force kill processes that don't close gracefully
        
    Returns:
        String with operation results
    """
    return close_application_by_name(app_name, force=force_kill, auto_confirm=True)

def list_processes() -> str:
    """
    Main function for agent to list all running processes
    
    Returns:
        String with formatted process list
    """
    return list_all_processes()

# Test function
if __name__ == "__main__":
    print("Close Application by Name Tool - Test Mode")
    print("=" * 50)
    
    # Test listing processes
    print("\nTesting process listing...")
    process_list = list_processes()
    print(f"Found {len(process_list.split('\\n'))} lines in process list")
    
    # Test finding a common process
    print("\nTesting process search...")
    test_processes = find_processes_by_name("python")
    print(f"Found {len(test_processes)} Python processes")
    
    for proc in test_processes:
        print(f"  - {proc['name']} (PID: {proc['pid']})")
    
    print("\nTool is ready for agent integration!")
