"""
Tool for closing applications by partial name match
"""

import psutil
from typing import List, Optional

def close_app(app_name: str) -> str:
    """
    Close applications by partial name match
    
    Args:
        app_name (str): Partial or full name of the application to close
        
    Returns:
        str: Results of the close operation, including terminated processes
    """
    app_name = app_name.lower().strip()
    found = False
    terminated_processes = []
    failed_processes = []
    
    # Iterate through all running processes
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            process_name = proc.info['name'].lower()
            pid = proc.info['pid']
            
            # Check if the name contains the search string
            if app_name in process_name:
                try:
                    proc.terminate()  # Send termination signal
                    terminated_processes.append(f"{process_name} (PID: {pid})")
                    found = True
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    failed_processes.append(f"{process_name} (PID: {pid}) - Error: {str(e)}")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Prepare the result message
    if found:
        result = f"Successfully terminated {len(terminated_processes)} process(es) matching '{app_name}':\n"
        result += "\n".join([f"- {proc}" for proc in terminated_processes])
        
        if failed_processes:
            result += f"\n\nFailed to terminate {len(failed_processes)} process(es):\n"
            result += "\n".join([f"- {proc}" for proc in failed_processes])
    else:
        result = f"No processes found matching '{app_name}'"
    
    return result

# Advanced version that can close multiple apps and returns more detailed information
def close_apps(app_names: List[str], force: bool = False) -> str:
    """
    Close multiple applications by partial name match with option for force kill
    
    Args:
        app_names (List[str]): List of app names to close
        force (bool, optional): If True, use kill() instead of terminate() for stubborn processes
        
    Returns:
        str: Results of the close operations
    """
    results = []
    
    for app_name in app_names:
        app_name = app_name.lower().strip()
        found = False
        terminated_processes = []
        failed_processes = []
        
        # Iterate through all running processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                process_name = proc.info['name'].lower()
                pid = proc.info['pid']
                
                # Check if the name contains the search string
                if app_name in process_name:
                    try:
                        if force:
                            proc.kill()  # Force kill
                        else:
                            proc.terminate()  # Graceful termination
                            
                        terminated_processes.append(f"{process_name} (PID: {pid})")
                        found = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        failed_processes.append(f"{process_name} (PID: {pid}) - Error: {str(e)}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Prepare the result for this app
        if found:
            app_result = f"App '{app_name}': Terminated {len(terminated_processes)} process(es)"
            if failed_processes:
                app_result += f", Failed to terminate {len(failed_processes)} process(es)"
        else:
            app_result = f"App '{app_name}': No processes found"
            
        results.append(app_result)
    
    return "\n".join(results)

# For testing
if __name__ == "__main__":
    # Test the basic close_app function
    print("Testing close_app with 'notepad':")
    print(close_app("notepad"))
    
    # Test the advanced close_apps function
    print("\nTesting close_apps with multiple apps:")
    print(close_apps(["chrome", "spotify"]))
