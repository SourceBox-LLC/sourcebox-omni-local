import psutil
import os
import signal
import ctypes
import time
from typing import List, Dict, Optional, Tuple

def is_admin() -> bool:
    """Check if the script is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_processes_by_name(process_name: str) -> List[Dict]:
    """
    Find all running processes that match the given process name (case-insensitive partial match)
    
    Args:
        process_name: Partial or full process name to search for
        
    Returns:
        List of dicts containing process info (pid, name, exe, status, username)
    """
    matching_processes = []
    
    # Handle list command
    if process_name.lower() == 'list':
        try:
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
                    matching_processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return matching_processes
        except Exception as e:
            print(f"Error listing processes: {e}")
            return []
    
    # Normal process search
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


def close_application(app_name: str, force: bool = False) -> List[Dict]:
    """
    Close all processes matching the given application name
    
    Args:
        app_name: Partial or full process name to search for
        force: If True, force kill processes that don't close gracefully
        
    Returns:
        List of dicts with results for each closed process
    """
    # Handle list command
    if app_name.lower() == 'list':
        processes = find_processes_by_name('list')
        if processes:
            print("\nCurrently running processes:")
            print("-" * 80)
            print(f"{'PID':<8} {'Name':<30} {'Status':<10} {'Username'}")
            print("-" * 80)
            for proc in sorted(processes, key=lambda x: x['name'].lower()):
                print(f"{proc['pid']:<8} {proc['name']:<30} {proc['status']:<10} {proc['username']}")
            print("\nTotal processes:", len(processes))
        return []
    
    # Normal process search and close
    processes = find_processes_by_name(app_name)
    results = []
    
    if not processes:
        print(f"No running processes found matching: {app_name}")
        print("Use 'list' to see all running processes.")
        return results
    
    print(f"\nFound {len(processes)} process(es) matching '{app_name}':")
    for idx, proc in enumerate(processes, 1):
        print(f"  {idx}. {proc['name']} (PID: {proc['pid']})")
        print(f"     Path: {proc.get('exe', 'N/A')}")
        print(f"     User: {proc.get('username', 'N/A')}")
    
    # Ask for confirmation
    if len(processes) > 0:
        response = input(f"\nClose {len(processes)} process(es)? [y/N] ").strip().lower()
        if response != 'y':
            print("Operation cancelled.")
            return results
    
    # Close each process
    for proc in processes:
        success, message = close_process(proc, force)
        result = {
            'name': proc['name'],
            'pid': proc['pid'],
            'success': success,
            'message': message
        }
        results.append(result)
        print(f"\n{message}")
        
        # Add a small delay between closing processes
        time.sleep(0.5)
    
    # Print summary
    if results:
        success_count = sum(1 for r in results if r['success'])
        print(f"\nSummary: {success_count} of {len(results)} process(es) closed successfully.")
    
    return results

def main():
    print("Process Manager - Close Running Applications")
    print("=" * 45)
    
    while True:
        print("\nOptions:")
        print("1. List all running processes")
        print("2. Close processes by name")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            # List all processes
            close_application('list')
            
        elif choice == '2':
            # Close processes by name
            app_name = input("Enter process name to close: ").strip()
            if not app_name:
                print("Please enter a valid process name.")
                continue
                
            force = input("Force kill if needed? (y/N): ").strip().lower() == 'y'
            
            if force and not is_admin():
                print("Warning: Force closing processes may require admin privileges.")
                print("Consider running this script as administrator for best results.")
            
            results = close_application(app_name, force)
            
        elif choice == '3':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")