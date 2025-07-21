#!/usr/bin/env python3
"""
Settings Manager for Local Ollama Agent
Handles loading, saving, and applying user settings
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class SettingsManager:
    def __init__(self):
        self.settings_file = Path.home() / ".local_ollama_agent" / "settings.json"
        self.settings_file.parent.mkdir(exist_ok=True)
        
        # Default settings
        self.default_settings = {
            "appearance": {
                "theme": "Dark",
                "accent_color": "Blue"
            },
            "ai_model": {
                "model": "qwen3"
            },
            "tools": {
                "screenshot_tool": True,
                "web_search": True,
                "file_operations": True,
                "game_launcher": True,
                "image_generation": True
            }
        }
        
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = self.default_settings.copy()
                self._deep_update(settings, loaded_settings)
                return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, category: str, key: str = None):
        """Get a setting value"""
        if key is None:
            return self.settings.get(category, {})
        return self.settings.get(category, {}).get(key)
    
    def set(self, category: str, key: str, value: Any) -> bool:
        """Set a setting value and save"""
        if category not in self.settings:
            self.settings[category] = {}
        
        self.settings[category][key] = value
        return self.save_settings()
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get color scheme based on current theme and accent color"""
        theme = self.get("appearance", "theme")
        accent = self.get("appearance", "accent_color")
        
        # Base colors for dark theme
        if theme == "Dark":
            base_colors = {
                "bg_primary": "#111111",
                "bg_secondary": "#1a1a1a", 
                "bg_tertiary": "#2a2a2a",
                "text_primary": "#ffffff",
                "text_secondary": "#888888",
                "border": "#333333"
            }
        elif theme == "Light":
            base_colors = {
                "bg_primary": "#ffffff",
                "bg_secondary": "#f8f9fa",
                "bg_tertiary": "#e9ecef", 
                "text_primary": "#212529",
                "text_secondary": "#6c757d",
                "border": "#dee2e6"
            }
        else:  # Auto - default to dark for now
            base_colors = {
                "bg_primary": "#111111",
                "bg_secondary": "#1a1a1a",
                "bg_tertiary": "#2a2a2a",
                "text_primary": "#ffffff", 
                "text_secondary": "#888888",
                "border": "#333333"
            }
        
        # Accent colors - adjusted for better contrast in both themes
        if theme == "Light":
            accent_colors = {
                "Blue": "#0066cc",
                "Green": "#28a745", 
                "Purple": "#6f42c1",
                "Orange": "#fd7e14"
            }
        else:
            accent_colors = {
                "Blue": "#00d4ff",
                "Green": "#00ff88", 
                "Purple": "#bb88ff",
                "Orange": "#ff8844"
            }
        
        # Set accent color with proper fallback for theme
        if theme == "Light":
            base_colors["accent"] = accent_colors.get(accent, "#0066cc")
        else:
            base_colors["accent"] = accent_colors.get(accent, "#00d4ff")
        return base_colors
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Recursively update nested dictionaries"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
