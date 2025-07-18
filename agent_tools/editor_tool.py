#!/usr/bin/env python3
"""
Editor Tool for Local Agent
Provides functionality to detect available code editors and open folders in them
"""
import os
import shutil
import subprocess
import sys
import logging
from typing import Union, Dict, Optional
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

# Map human-friendly names to possible executables on PATH
KNOWN_EDITORS = {
    "Visual Studio Code": ["code", "code-insiders"],
    "PyCharm": ["pycharm", "pycharm64", "charm"],
    "Sublime Text": ["subl", "sublime_text"],
    "Notepad++": ["notepad++"],
    "Atom": ["atom"],
    "Vim": ["vim"],
    "Emacs": ["emacs"],
    "Visual Studio (devenv)": ["devenv"],
    "IntelliJ IDEA": ["idea", "idea64"],
}

def find_available_editors() -> Dict[str, str]:
    """
    Scan PATH for known editor executables.
    
    Returns:
        A dict mapping friendly names to executable paths
    """
    found = {}
    try:
        for name, cmds in KNOWN_EDITORS.items():
            for cmd in cmds:
                path = shutil.which(cmd)
                if path:
                    found[name] = path
                    break
        return found
    except Exception as e:
        logger.exception("Error finding available editors")
        return {}

def open_folder_in_editor(
    folder: Union[str, os.PathLike],
    editor_name: Optional[str] = None
) -> Dict[str, any]:
    """
    Open the given folder in the specified editor, first available editor,
    or fallback to file explorer.
    
    Args:
        folder: Path to the folder to open
        editor_name: (Optional) Preferred editor name to use
        
    Returns:
        Dict with operation result including:
        - success: Whether opening was successful
        - method: How the folder was opened (editor name or "file_explorer")
        - path: Path to the folder that was opened
        - error: Error message if something went wrong
    """
    try:
        folder_path = os.path.abspath(folder)
        if not os.path.isdir(folder_path):
            return {
                "success": False, 
                "error": f"Folder not found: {folder_path}",
                "path": folder_path
            }

        editors = find_available_editors()
        cmd_to_run = None
        chosen_editor = None
        
        # Try to find the requested editor
        if editor_name:
            for name, path in editors.items():
                if editor_name.lower() in name.lower():
                    cmd_to_run = path
                    chosen_editor = name
                    break
                    
        # If specific editor not found/specified, use first available
        if not cmd_to_run and editors:
            chosen_editor, cmd_to_run = next(iter(editors.items()))
            
        # Try opening with editor if available
        if cmd_to_run:
            try:
                subprocess.Popen([cmd_to_run, folder_path])
                logger.info(f"Opened '{folder_path}' in editor ({chosen_editor})")
                return {
                    "success": True,
                    "method": chosen_editor,
                    "path": folder_path
                }
            except Exception as e:
                logger.warning(f"Failed to launch editor '{chosen_editor}': {e}")
                # Fall through to file explorer as backup

        # Fallback to file explorer
        try:
            if sys.platform.startswith('win'):
                subprocess.Popen(["explorer", folder_path])
                method = "Windows Explorer"
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(["open", folder_path])
                method = "macOS Finder"
            else:
                subprocess.Popen(["xdg-open", folder_path])
                method = "File Manager"
                
            logger.info(f"Opened '{folder_path}' in file explorer")
            return {
                "success": True,
                "method": f"file_explorer ({method})",
                "path": folder_path
            }
        except Exception as e:
            error_msg = f"Failed to open folder in file explorer: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "path": folder_path
            }
            
    except Exception as e:
        error_msg = f"Error opening folder: {str(e)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

def get_available_editors() -> Dict[str, str]:
    """
    Get a list of available code editors on the system.
    
    Returns:
        Dict mapping editor names to their executable paths
    """
    editors = find_available_editors()
    return editors


# For testing directly
if __name__ == "__main__":
    import json
    import argparse
    
    # Configure basic logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(
        description="Detect and open a folder in a code editor or file explorer"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Path to the folder to open (defaults to current directory)"
    )
    parser.add_argument(
        "--editor", "-e", dest="editor", help="Preferred editor friendly name"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available editors and exit"
    )
    args = parser.parse_args()

    if args.list:
        editors = find_available_editors()
        print("Available editors:")
        for name, path in editors.items():
            print(f"  {name}: {path}")
        sys.exit(0)

    result = open_folder_in_editor(args.folder, args.editor)
    if result["success"]:
        print(f"✅ Opened '{result['path']}' using {result['method']}")
    else:
        print(f"❌ Error: {result['error']}")
