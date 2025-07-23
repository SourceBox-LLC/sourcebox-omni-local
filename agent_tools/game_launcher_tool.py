"""
Game Launcher Tool - Find and launch games by title
This tool can automatically detect and launch games from multiple sources:
- Steam
- Epic Games
- GOG
- Origin/EA
- Battle.net
- Other common game installation locations
"""

import os
import subprocess
import glob
import winreg
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path


def launch_game(game_title: str) -> str:
    """
    Find and launch a game by title.
    
    Args:
        game_title (str): The title of the game to find and launch
        
    Returns:
        str: Result of the operation
    """
    game_title = game_title.lower().strip()
    
    # Search for the game
    game_info = _find_game(game_title)
    
    if not game_info:
        return f"No game found matching '{game_title}'. Try a different title or check if it's installed."
    
    # Launch the game
    launch_path, game_name = game_info
    try:
        # Check if it's a Steam URL or regular executable
        if launch_path.startswith("steam://"):
            # For Steam games, use the Steam protocol
            import webbrowser
            webbrowser.open(launch_path)
        else:
            # For non-Steam games, launch the executable directly
            subprocess.Popen(launch_path)
        return f"Successfully launched {game_name}"
    except Exception:
        import traceback
        error_message = traceback.format_exc()
        print(f"Game launcher error: {error_message}")
        return f"Error launching {game_name}: {str(error_message.splitlines()[-1])} - please check logs"


def _find_game(game_title: str) -> Optional[Tuple[str, str]]:
    """
    Find a game by title across multiple game stores and common locations.
    
    Args:
        game_title (str): The title of the game to find
        
    Returns:
        Optional[Tuple[str, str]]: Tuple of (executable_path, game_name) if found, None otherwise
    """
    # Try different game sources
    # 1. Steam games
    steam_result = _find_steam_game(game_title)
    if steam_result:
        return steam_result
    
    # 2. Epic Games
    epic_result = _find_epic_game(game_title)
    if epic_result:
        return epic_result
    
    # 3. GOG Games
    gog_result = _find_gog_game(game_title)
    if gog_result:
        return gog_result
    
    # 4. Origin/EA Games
    ea_result = _find_ea_game(game_title)
    if ea_result:
        return ea_result
    
    # 5. Battle.net Games
    battlenet_result = _find_battlenet_game(game_title)
    if battlenet_result:
        return battlenet_result
    
    # 6. Common game folders
    common_result = _find_game_in_common_locations(game_title)
    if common_result:
        return common_result
    
    # Not found
    return None


def _find_steam_game(game_title: str) -> Optional[Tuple[str, str]]:
    """
    Find a Steam game by title.
    """
    steam_path = _get_steam_path()
    if not steam_path:
        return None
    
    # Find Steam game libraries
    library_folders = _get_steam_libraries(steam_path)
    
    # Search in all library folders
    for library in library_folders:
        steamapps_path = os.path.join(library, "steamapps")
        
        # First try finding by app manifest (more reliable)
        for manifest_file in glob.glob(os.path.join(steamapps_path, "appmanifest_*.acf")):
            try:
                # Read manifest to find game name
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest_content = f.read()
                    
                # Extract app ID from filename
                app_id = os.path.basename(manifest_file).split('_')[1].split('.')[0]
                
                # Extract name from manifest using regex
                import re
                name_match = re.search(r'"name"\s+"([^"]+)"', manifest_content)
                
                if name_match:
                    game_name = name_match.group(1)
                    if game_title in game_name.lower():
                        # Return steam:// URL protocol
                        steam_url = f"steam://run/{app_id}"
                        return steam_url, game_name
            except Exception:
                continue
        
        # Fallback to common folder if manifest approach fails
        common_path = os.path.join(steamapps_path, "common")
        if os.path.exists(common_path):
            for game_dir in os.listdir(common_path):
                if game_title in game_dir.lower():
                    # Found a potential match by folder name
                    # Look for a corresponding manifest file
                    for manifest_file in glob.glob(os.path.join(steamapps_path, "appmanifest_*.acf")):
                        try:
                            with open(manifest_file, 'r', encoding='utf-8') as f:
                                manifest_content = f.read()
                                
                            if game_dir.lower() in manifest_content.lower():
                                app_id = os.path.basename(manifest_file).split('_')[1].split('.')[0]
                                steam_url = f"steam://run/{app_id}"
                                return steam_url, game_dir
                        except Exception:
                            continue
                    
                    # If we couldn't find a manifest, fall back to executable
                    game_path = os.path.join(common_path, game_dir)
                    exe_file = _find_executable_in_directory(game_path)
                    if exe_file:
                        return exe_file, game_dir
    
    return None


def _get_steam_path() -> Optional[str]:
    """
    Get the Steam installation path from registry.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
            return winreg.QueryValueEx(key, "InstallPath")[0]
    except Exception:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam") as key:
                return winreg.QueryValueEx(key, "InstallPath")[0]
        except Exception:
            # Default path if registry lookup fails
            default_path = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Steam")
            if os.path.exists(default_path):
                return default_path
    return None


def _get_steam_libraries(steam_path: str) -> List[str]:
    """
    Get all Steam library folders.
    """
    libraries = [steam_path]
    
    # Parse libraryfolders.vdf to find additional library locations
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf_path):
        try:
            with open(vdf_path, 'r') as f:
                content = f.read()
            
            # Simple parsing of library folders
            # This is a basic implementation; a proper VDF parser would be more robust
            import re
            paths = re.findall(r'"path"\s+"([^"]+)"', content)
            for path in paths:
                # Replace escaped backslashes
                path = path.replace("\\\\", "\\")
                libraries.append(path)
        except Exception:
            pass
    
    return libraries


def _find_epic_game(game_title: str) -> Optional[Tuple[str, str]]:
    """
    Find an Epic Games game by title.
    """
    # Default Epic Games Launcher manifests location
    manifest_dirs = [
        os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), r"Epic\EpicGamesLauncher\Data\Manifests"),
        os.path.expanduser(r"~\AppData\Local\EpicGamesLauncher\Saved\Config\Windows")
    ]
    
    for manifest_dir in manifest_dirs:
        if os.path.exists(manifest_dir):
            for file in os.listdir(manifest_dir):
                if file.endswith(".item") or file.endswith(".json"):
                    try:
                        with open(os.path.join(manifest_dir, file), 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        
                        # Extract game info from manifest
                        display_name = manifest.get("DisplayName", "")
                        if game_title in display_name.lower():
                            install_location = manifest.get("InstallLocation", "")
                            if install_location and os.path.exists(install_location):
                                exe_file = _find_executable_in_directory(install_location)
                                if exe_file:
                                    return exe_file, display_name
                    except Exception:
                        continue
    
    return None


def _find_gog_game(game_title: str) -> Optional[Tuple[str, str]]:
    """
    Find a GOG game by title.
    """
    # Common GOG installation directories
    gog_dirs = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), r"GOG Galaxy\Games"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), r"GOG Galaxy\Games"),
    ]
    
    for gog_dir in gog_dirs:
        if os.path.exists(gog_dir):
            for game_dir in os.listdir(gog_dir):
                if game_title in game_dir.lower():
                    game_path = os.path.join(gog_dir, game_dir)
                    exe_file = _find_executable_in_directory(game_path)
                    if exe_file:
                        return exe_file, game_dir
    
    return None


def _find_ea_game(game_title: str) -> Optional[Tuple[str, str]]:
    """
    Find an EA/Origin game by title.
    """
    # Common EA/Origin installation directories
    ea_dirs = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "EA Games"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "EA Games"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Origin Games"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Origin Games"),
    ]
    
    for ea_dir in ea_dirs:
        if os.path.exists(ea_dir):
            for game_dir in os.listdir(ea_dir):
                if game_title in game_dir.lower():
                    game_path = os.path.join(ea_dir, game_dir)
                    exe_file = _find_executable_in_directory(game_path)
                    if exe_file:
                        return exe_file, game_dir
    
    return None


def _find_battlenet_game(game_title: str) -> Optional[Tuple[str, str]]:
    """
    Find a Battle.net game by title.
    """
    # Common Battle.net installation directories
    battlenet_dirs = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), r"Battle.net\Games"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), r"Battle.net\Games"),
    ]
    
    # Map of common Battle.net games to their typical directories
    battlenet_games = {
        "wow": "World of Warcraft",
        "warcraft": "World of Warcraft",
        "world of warcraft": "World of Warcraft",
        "overwatch": "Overwatch",
        "diablo": "Diablo III",
        "diablo3": "Diablo III",
        "diablo 3": "Diablo III",
        "hearthstone": "Hearthstone",
        "starcraft": "StarCraft",
        "starcraft2": "StarCraft II",
        "starcraft 2": "StarCraft II",
        "heroes of the storm": "Heroes of the Storm",
        "heroes": "Heroes of the Storm",
        "call of duty": "Call of Duty",
        "cod": "Call of Duty",
    }
    
    # Check if the game title matches any known Battle.net games
    matched_dir = None
    for known_title, dir_name in battlenet_games.items():
        if game_title in known_title or known_title in game_title:
            matched_dir = dir_name
            break
    
    if matched_dir:
        for battlenet_dir in battlenet_dirs:
            potential_path = os.path.join(battlenet_dir, matched_dir)
            if os.path.exists(potential_path):
                exe_file = _find_executable_in_directory(potential_path)
                if exe_file:
                    return exe_file, matched_dir
    
    return None


def _find_game_in_common_locations(game_title: str) -> Optional[Tuple[str, str]]:
    """
    Find a game in common installation locations.
    """
    # Common game installation directories
    game_dirs = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Games"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Games"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files")),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    
    # Check drives for game folders
    for drive in ['C', 'D', 'E', 'F']:
        game_dirs.append(fr"{drive}:\Games")
        game_dirs.append(fr"{drive}:\SteamLibrary")
        game_dirs.append(fr"{drive}:\EpicGames")
        game_dirs.append(fr"{drive}:\GOGGames")
    
    for game_dir in game_dirs:
        if os.path.exists(game_dir):
            # Recursive search with max depth of 2 to avoid too deep scanning
            for root, dirs, files in os.walk(game_dir, topdown=True, followlinks=False):
                # Limit depth of recursion
                depth = root.count(os.path.sep) - game_dir.count(os.path.sep)
                if depth > 2:
                    continue
                
                if game_title in root.lower():
                    exe_file = _find_executable_in_directory(root)
                    if exe_file:
                        game_name = os.path.basename(root)
                        return exe_file, game_name
                
                # Check if any directory matches
                for dir_name in dirs:
                    if game_title in dir_name.lower():
                        dir_path = os.path.join(root, dir_name)
                        exe_file = _find_executable_in_directory(dir_path)
                        if exe_file:
                            return exe_file, dir_name
    
    return None


def _find_executable_in_directory(directory: str) -> Optional[Tuple[str, str]]:
    """
    Find a suitable executable file in the directory.
    
    Args:
        directory (str): Directory to search for executables
        
    Returns:
        Optional[Tuple[str, str]]: Tuple of (exe_path, game_name) if found, None otherwise
    """
    if not os.path.exists(directory):
        return None
    
    exes = []
    
    # Find all executable files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.exe'):
                exes.append(os.path.join(root, file))
    
    if not exes:
        return None
    
    # Try to find the main executable - typically named after the game or in certain locations
    game_name = os.path.basename(directory)
    
    # Priority 1: Exact match with directory name
    for exe in exes:
        exe_name = os.path.splitext(os.path.basename(exe))[0].lower()
        if exe_name == game_name.lower():
            return exe, game_name
    
    # Priority 2: Contains the directory name
    for exe in exes:
        exe_name = os.path.splitext(os.path.basename(exe))[0].lower()
        if game_name.lower() in exe_name:
            return exe, game_name
    
    # Priority 3: Executables in Bin, Binaries, or similar folders
    bin_exes = [exe for exe in exes if any(folder in os.path.dirname(exe).lower() 
                                          for folder in ['\\bin', '\\binaries', '\\game', '\\launch'])]
    if bin_exes:
        return bin_exes[0], game_name
    
    # Priority 4: .exe with largest file size (often the main game)
    if exes:
        largest_exe = max(exes, key=os.path.getsize)
        return largest_exe, game_name
    
    return None


# For testing
if __name__ == "__main__":
    while True:
        game_input = input("Enter a game title to launch (or 'exit' to quit): ")
        if game_input.lower() == 'exit':
            break
        result = launch_game(game_input)
        print(result)
