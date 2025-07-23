import os
import subprocess
from pathlib import Path
import json



def app_finder(query: str = None, refresh: bool = False) -> str:
    """
    Index and find installed Windows applications.
    
    Args:
        query (str, optional): Application name to search for
        refresh (bool, optional): Force refresh the application index
        
    Returns:
        str: Information about matching applications or all indexed apps
    """
    # Path to store the cached application index
    cache_file = Path.home() / ".app_index_cache.json"
    
    # Check if we need to build/refresh the cache
    if refresh or not cache_file.exists():
        apps = {}
        
        # Method 1: Check Start Menu entries (most user-friendly apps)
        start_menu_dirs = [
            Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs",
            Path(os.environ["PROGRAMDATA"]) / "Microsoft/Windows/Start Menu/Programs"
        ]
        
        for dir_path in start_menu_dirs:
            if dir_path.exists():
                # Find all .lnk files (shortcuts)
                for shortcut in dir_path.glob("**/*.lnk"):
                    try:
                        # Use shell to resolve shortcut target
                        cmd = f'powershell -command "(New-Object -ComObject WScript.Shell).CreateShortcut(\"{str(shortcut)}\").TargetPath"'
                        target = subprocess.check_output(cmd, shell=True, text=True, timeout=2).strip()
                        
                        # Only add valid executables
                        if target and target.lower().endswith(('.exe', '.bat', '.cmd')) and Path(target).exists():
                            app_name = shortcut.stem.lower()
                            apps[app_name] = target
                    except Exception:
                        # Silent fail - some shortcuts might be invalid
                        pass
        
        # Method 2: Check common installation directories
        install_dirs = [
            Path(os.environ["PROGRAMFILES"]),
            Path(os.environ["PROGRAMFILES(X86)"]),
            Path(os.environ["LOCALAPPDATA"])
        ]
        
        for dir_path in install_dirs:
            if dir_path.exists():
                # Find executable files up to 2 levels deep (avoid traversing entire drives)
                for exe_file in dir_path.glob("*/*.exe"):
                    app_name = exe_file.stem.lower()
                    apps[app_name] = str(exe_file)
                for exe_file in dir_path.glob("*/*/*.exe"):
                    app_name = exe_file.stem.lower()
                    apps[app_name] = str(exe_file)
        
        # Save the cache
        with open(cache_file, "w") as f:
            json.dump(apps, f)
        
        result = f"Application index created with {len(apps)} applications"
    else:
        # Load the existing cache
        with open(cache_file, "r") as f:
            apps = json.load(f)
        result = f"Using existing application index with {len(apps)} applications"
    
    # If a query is provided, search for matching applications
    if query:
        query = query.lower()
        matches = {}
        
        # Exact match
        if query in apps:
            matches["exact"] = {query: apps[query]}
        
        # Partial matches
        partial = {name: path for name, path in apps.items() if query in name}
        if partial:
            matches["partial"] = partial
        
        if matches:
            # Format the results
            result = f"Found applications matching '{query}':\n"
            
            if "exact" in matches:
                for name, path in matches["exact"].items():
                    result += f"✓ {name}: {path}\n"
            
            if "partial" in matches:
                result += "\nPartial matches:\n"
                for name, path in list(matches["partial"].items())[:5]:  # Limit to 5 matches
                    result += f"- {name}: {path}\n"
                
                if len(matches["partial"]) > 5:
                    result += f"...and {len(matches['partial']) - 5} more matches"
            
            return result
        else:
            return f"No applications found matching '{query}'"
    
    # If no query, just return summary statistics
    return result



def launch_app(app_name: str) -> str:
    """
    Find and launch an application by name, with robust handling for all app types.
    
    Args:
        app_name (str): Name of the application to find and launch
        
    Returns:
        str: Result of the launch attempt
    """
    print(f"Looking for application: {app_name}")
    
    # First, try to find the app using app_finder
    find_result = app_finder(query=app_name)
    
    if "No applications found" in find_result:
        return f"Could not find any application matching '{app_name}'"
    
    # Extract the app path from the result
    app_path = None
    lines = find_result.split("\n")
    
    # First try to get exact match
    for line in lines:
        if line.startswith("✓") and ":" in line:
            app_path = line.split(": ", 1)[1].strip()
            break
    
    # If no exact match, try partial match
    if not app_path:
        for line in lines:
            if line.startswith("-") and ":" in line:
                app_path = line.split(": ", 1)[1].strip()
                break
    
    # Check if we found an app path
    if not app_path:
        return f"Could not determine path for '{app_name}'"
    
    # Launch the application
    try:
        # Use subprocess with special flags to detach completely from parent process
        # This prevents hanging in the terminal
        if os.name == 'nt':  # Windows
            # DETACHED_PROCESS flag ensures the process doesn't keep the console window
            # CREATE_NEW_PROCESS_GROUP prevents the child from receiving ctrl+c events from parent
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(
                [app_path],  # Don't use shell=True to prevent hanging
                startupinfo=startupinfo,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                shell=False
            )
        else:  # Linux/Mac
            subprocess.Popen(
                [app_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
        
        return f"Successfully launched {app_name} from {app_path}"
    except Exception:
        import traceback
        error_message = traceback.format_exc()
        print(f"Launch app error: {error_message}")
        return f"Error launching {app_name}: {str(error_message.splitlines()[-1])}"


if __name__ == "__main__":
    app_name = "steam"
    result = launch_app(app_name)
    print(result)