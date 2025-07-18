#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import json
from typing import Union

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

def find_available_editors() -> dict:
    """
    Scan PATH for known editor executables.
    Returns a dict: {friendly_name: executable_path}
    """
    found = {}
    for name, cmds in KNOWN_EDITORS.items():
        for cmd in cmds:
            path = shutil.which(cmd)
            if path:
                found[name] = path
                break
    return found


def open_folder_in_editor(
    folder: Union[str, os.PathLike],
    editor_name: str = None
) -> bool:
    """
    Open the given folder in the specified editor, first available editor,
    or fallback to file explorer. Returns True if launched successfully.
    """
    folder_path = os.path.abspath(folder)
    if not os.path.isdir(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return False

    editors = find_available_editors()
    cmd_to_run = None
    if editor_name and editor_name in editors:
        cmd_to_run = editors[editor_name]
    elif editors:
        chosen, path = next(iter(editors.items()))
        cmd_to_run = path
        print(f"⚙️  No preference given or not found. Using: {chosen}")

    # Try opening in editor if available
    if cmd_to_run:
        try:
            subprocess.Popen([cmd_to_run, folder_path])
            print(f"✅ Opened '{folder_path}' in editor ({cmd_to_run})")
            return True
        except Exception as e:
            print(f"⚠️ Failed to launch editor '{cmd_to_run}': {e}")

    # Fallback to file explorer
    try:
        if sys.platform.startswith('win'):
            subprocess.Popen(["explorer", folder_path])
        elif sys.platform.startswith('darwin'):
            subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])
        print(f"✅ Opened '{folder_path}' in file explorer")
        return True
    except Exception as e:
        print(f"❌ Failed to open file explorer: {e}")
        return False


def main():
    import argparse
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
        "--json", action="store_true", help="Output available editors as JSON"
    )
    args = parser.parse_args()

    if args.json:
        editors = find_available_editors()
        print(json.dumps(editors, indent=2))
        sys.exit(0)

    open_folder_in_editor(args.folder, args.editor)
    sys.exit(0)

if __name__ == "__main__":
    main()
