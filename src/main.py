#!/usr/bin/env python
"""
SourceBox OmniLocal - Local-First AI Desktop Assistant
Beautiful graphical interface with powerful on-device AI capabilities
Copyright (c) 2024 SourceBox LLC
"""

import sys
import os
import threading
import time
from typing import List, Dict, Any
import flet as ft
import json
import threading
import asyncio
import subprocess
import sys
import os
import shutil
import tempfile
import uuid
import webbrowser
import traceback
import socket
import psutil
import sys
from pathlib import Path
import GPUtil
from ollama import chat, ChatResponse
import datetime
import platform
from settings import SettingsManager
import urllib.request
import urllib.error
import shlex
import types as pytypes

# Optional MCP client
try:
    from mcp.client.stdio import stdio_client, StdioServerParameters
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    MCP_AVAILABLE = True
except Exception:
    MCP_AVAILABLE = False

# Add project root directory to path to import agent tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import tools from agent_tools package
# Handle missing dependencies gracefully
try:
    from agent_tools.launch_app_tool import launch_app
except ImportError as e:
    def launch_app(app_name):
        return f"Error: Launch app tool unavailable - {str(e)}"

try:
    from agent_tools.screenshot_tool import take_screenshot
except ImportError as e:
    def take_screenshot(window_title=None):
        return f"Error: Screenshot tool unavailable - {str(e)}. Please install pyautogui: pip install pyautogui"

try:
    from agent_tools.web_search_tool import web_search
except ImportError as e:
    def web_search(query, max_results=5):
        return f"Error: Web search tool unavailable - {str(e)}"

try:
    from agent_tools.system_info_tool import system_info
except ImportError as e:
    def system_info(info_type="all"):
        return f"Error: System info tool unavailable - {str(e)}"

try:
    from agent_tools.close_app_tool import close_app
except ImportError as e:
    def close_app(app_name):
        return f"Error: Close app tool unavailable - {str(e)}"

try:
    from agent_tools.game_launcher_tool import launch_game
except ImportError as e:
    def launch_game(game_title):
        return f"Error: Game launcher tool unavailable - {str(e)}"

try:
    from agent_tools.file_ops_tool import FileOperationsTool
except ImportError as e:
    class FileOperationsTool:
        def __init__(self):
            pass
        
        def list_directory(self, path=None, pattern=None, show_hidden=False, sort_by="name", reverse=False):
            return {"error": f"File operations tool unavailable - {str(e)}"}
        
        def copy_item(self, source, destination, overwrite=False):
            return {"error": f"File operations tool unavailable - {str(e)}"}
            
        def move_item(self, source, destination, overwrite=False):
            return {"error": f"File operations tool unavailable - {str(e)}"}
            
        def delete_item(self, path, recursive=False):
            return {"error": f"File operations tool unavailable - {str(e)}"}
            
        def rename_item(self, path, new_name):
            return {"error": f"File operations tool unavailable - {str(e)}"}
            
        def create_directory(self, path):
            return {"error": f"File operations tool unavailable - {str(e)}"}
            
        def create_file(self, path, content="", overwrite=False, encoding="utf-8"):
            return {"error": f"File operations tool unavailable - {str(e)}"}

try:
    from agent_tools.editor_tool import open_folder_in_editor, get_available_editors
except ImportError as e:
    def open_folder_in_editor(folder, editor_name=None):
        return {"success": False, "error": f"Editor tool unavailable - {str(e)}"}
    
    def get_available_editors():
        return {"error": f"Editor tool unavailable - {str(e)}"}

try:
    from agent_tools.image_gen_tool import generate_image
except ImportError as e:
    def generate_image(prompt, save_path="output.png"):
        return f"Error: Image generation tool unavailable - {str(e)}. Please install replicate: pip install replicate"

try:
    from agent_tools.wallpaper_tool import set_wallpaper
except ImportError as e:
    def set_wallpaper(image_path):
        return f"Error: Wallpaper tool unavailable - {str(e)}"

try:
    from agent_tools.webpage_extraction_tool import load_web_content
    WEBPAGE_EXTRACTION_AVAILABLE = True
except ImportError as e:
    def load_web_content(urls):
        return {"success": False, "error": f"Webpage extraction tool unavailable - {str(e)}", "content": ""}
    WEBPAGE_EXTRACTION_AVAILABLE = False

try:
    from agent_tools.close_app_by_name_tool import close_app_by_name, list_processes
    CLOSE_APP_BY_NAME_AVAILABLE = True
except ImportError as e:
    def close_app_by_name(app_name, force_kill=False):
        return f"Error: Close app by name tool unavailable - {str(e)}"
    def list_processes():
        return f"Error: Process listing tool unavailable - {str(e)}"
    CLOSE_APP_BY_NAME_AVAILABLE = False

try:
    from agent_tools.document_loader_tool import load_document_content, is_supported_document, get_document_type
    DOCUMENT_LOADER_AVAILABLE = True
except ImportError as e:
    def load_document_content(file_path):
        return {"success": False, "error": f"Document loader unavailable - {str(e)}", "content": None}
    def is_supported_document(file_path):
        return False
    def get_document_type(file_path):
        return "Unknown"
    DOCUMENT_LOADER_AVAILABLE = False

try:
    from agent_tools.timer_tool import set_timer
    TIMER_TOOL_AVAILABLE = True
except ImportError as e:
    def set_timer(duration_text):
        return {"success": False, "message": f"Timer tool unavailable - {str(e)}"}
    TIMER_TOOL_AVAILABLE = False

try:
    from agent_tools.image_description_tool import describe_image
    IMAGE_DESCRIPTION_AVAILABLE = True
except ImportError as e:
    def describe_image(image_path, prompt="Describe this image in as much detail as possible"):
        return f"Error: Image description tool unavailable - {str(e)}. Please install replicate: pip install replicate"
    IMAGE_DESCRIPTION_AVAILABLE = False

# Audio transcription with Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Optional Flet Audio Recorder plugin (moved out of core Flet)
try:
    from flet_audio_recorder import AudioRecorder as FletAudioRecorder  # type: ignore
    FLET_AUDIO_RECORDER_AVAILABLE = True
except Exception:
    FLET_AUDIO_RECORDER_AVAILABLE = False


class OllamaAgentGUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.messages = []
        # Initialize file operations tool
        self.file_ops = FileOperationsTool()
        # Page navigation state
        self.current_page = "chat"  # "chat" or "settings"
        self.main_content = None
        # Settings manager
        self.settings = SettingsManager()
        # Track pending settings changes
        self.settings_changed = False
        self.save_button = None
        # File upload functionality
        self.temp_dir = None
        self.uploaded_files = []
        # Load any previously uploaded files
        self.load_file_queue_state()
        
        # Audio recording functionality
        self.audio_recorder = None
        self.is_recording = False
        self.current_recording_path = None
        self.tools = [self.launch_apps, self.take_screenshot_wrapper, 
                     self.web_search_wrapper, self.get_system_info, self.close_apps, 
                     self.launch_game_wrapper, 
                     # File operations tools
                     self.list_directory, self.copy_file, self.move_file, 
                     self.delete_file, self.rename_file, self.create_directory, 
                     self.create_file,
                     # Editor tool
                     self.open_in_editor,
                     # Image generation tool
                     self.generate_image_wrapper,
                     # Wallpaper tool
                     self.set_wallpaper_wrapper,
                     # Webpage extraction tool
                     self.extract_webpage_content,
                     # Close app by name tools
                     self.close_app_by_name_wrapper,
                     self.list_processes_wrapper,
                     # Timer tool
                     self.set_timer_wrapper,
                     # Image description tool
                     self.describe_image_wrapper]
        # MCP runtime state
        self.mcp_wrapper_names = []  # legacy placeholder; keep for safety
        self.mcp_tool_names: list[str] = []  # discovered tool names from server
        self.mcp_server_conf: dict | None = None
        self.mcp_announce_done: bool = False

        self.setup_page()
        self.setup_system_message()
        self.create_ui()
        
    def setup_page(self):
        """Configure the main page settings"""
        self.page.title = "🔊 SourceBox OmniLocal"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 900
        self.page.window_min_height = 700
        self.page.window_title_bar_hidden = False
        self.page.window_title_bar_buttons_hidden = False
        
        # System metrics containers for charts
        self.cpu_chart_container = ft.Container(
            content=None,  # Will be set in create_chart method
            expand=True,
            height=40,
            border_radius=5,
            padding=0
        )
        
        self.ram_chart_container = ft.Container(
            content=None,  # Will be set in create_chart method
            expand=True,
            height=40,
            border_radius=5,
            padding=0
        )
        
        self.live_stats_text = ft.Text(
            "Initializing system metrics...", 
            size=14,
            color="#808080"
        )
        
        # CPU and RAM history data for charts (last 60 data points)
        self.cpu_history = [0] * 60
        self.ram_history = [0] * 60
        
    def setup_system_message(self):
        """Initialize the system message (same as console agent)"""
        system_msg = (
            "Your name is Omni, created by SourceBox LLC. You are the creation of the SourceBox OmniLocal Project. You are an AI agent on Windows. You achieve goals by invoking under the hood, built in tools. " +
            
            "This  .\n"
            
            "CURRENT USER: C:\\Users\\S'Bussiso\n" +
            "CURRENT DATE: " + datetime.datetime.now().strftime("%Y-%m-%d") + "\n" +
            "CURRENT TIME: " + datetime.datetime.now().strftime("%H:%M:%S") + "\n" +
            "CURRENT OS: " + platform.system() + "\n" +

            "AVAILABLE TOOLS:\n" +
            "1. launch_apps(app_name): Launch applications by name\n" +
            "2. close_apps(app_name): Close applications by partial name match\n" +
            "3. take_screenshot_wrapper(window_title=None): Capture screenshot and save to Desktop/Screenshots; optionally specify window to focus\n" +
            "4. web_search_wrapper(query, max_results=5): Search the web using DuckDuckGo\n" +
            "5. get_system_info(info_type='all'): Get system information - options: 'all', 'cpu', 'memory', 'disk', 'network', 'os', 'processes'\n" +
            "6. launch_game_wrapper(game_title): Find and launch a PC game by title\n\n" +
            "FILE OPERATIONS TOOLS:\n" +
            "7. list_directory(path=None, pattern=None, show_hidden=False, sort_by='name', reverse=False): List files and directories in the specified path\n" +
            "8. copy_file(source, destination, overwrite=False): Copy a file or directory to the destination path\n" +
            "9. move_file(source, destination, overwrite=False): Move a file or directory to the destination path\n" +
            "10. delete_file(path, recursive=False): Delete a file or directory (recursive for non-empty directories)\n" +
            "11. rename_file(path, new_name): Rename a file or directory to a new name\n" +
            "12. create_directory(path): Create a new directory at the specified path\n" +
            "13. create_file(path, content='', overwrite=False, encoding='utf-8'): Create a new file with optional content\n" +
            "14. open_in_editor(folder_path=None, editor_name=None): Open a folder in code editor or file explorer (if no path provided, lists available editors)\n" +
            "15. generate_image_wrapper(prompt, save_path='output.png'): Generate an AI image from text prompt and save to specified path\n" +
            "16. set_wallpaper_wrapper(image_path): Set Windows desktop wallpaper to the specified image file\n" +
            "17. extract_webpage_content(url): Extract and return the full content of a webpage for analysis\n" +
            "18. close_app_by_name_wrapper(app_name, force_kill=False): Close applications by partial process name match with detailed results\n" +
            "19. list_processes_wrapper(): List all running processes on the system\n" +
            "20. set_timer_wrapper(duration): Set a timer using natural language (e.g., '5 minutes', '30 seconds', '1 hour')\n" +
            "21. describe_image_wrapper(image_path, prompt='Describe this image in as much detail as possible'): Analyze and describe images using AI vision (supports JPG, PNG, GIF, BMP, WEBP)\n\n" +

            "IMPORTANT NOTE: the launch_apps tool and launch_game_wrapper tool are different.\n" +
            "the launch_app tool is for applications (steam, discord, spotify, etc) while the launch_game_wrapper tool is used ONLY for launching games.\n" +
            "SIMPLE WAY TO REMEMBER: VIDEO GAME = launch_game_wrapper tool, REGULAR APP = launch_app tool\n\n"

            "IMPORTANT NOTE: the web_search_tool and extract_webpage_content tool are different.\n" +
            "the web_search_tool is used to broadly search the web using DuckDuckGo while the extract_webpage_content tool is used to extract the full content of a webpage for analysis.\n" +
            "SIMPLE WAY TO REMEMBER: BROAD SEARCH = web_search_tool, DEEP SEARCH = extract_webpage_content tool\n\n"

            "IMPORTANT NOTE: close_apps and close_app_by_name_wrapper are different tools.\n" +
            "close_apps is the original simple tool, while close_app_by_name_wrapper provides detailed process information and better control.\n" +
            "SIMPLE WAY TO REMEMBER: DETAILED PROCESS CONTROL = close_app_by_name_wrapper, SIMPLE CLOSE = close_apps\n\n"
        )
        self.messages = [{"role": "system", "content": system_msg}]
       
    def create_ui(self):
        """Create the main UI components"""
        # File picker for file uploads
        self.file_picker = ft.FilePicker(
            on_result=self.handle_file_picker_result
        )
        self.page.overlay.append(self.file_picker)
        
        # Audio recorder temporarily disabled to avoid 'Unknown control: audiorecorder' on builds
        # If you want to enable voice later, install 'flet-audio-recorder' and set a flag to enable.
        self.audio_recorder = None
        self.voice_supported = False
        colors = self.settings.get_theme_colors()
        
        # Create header with dynamic styling
        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="Settings",
            on_click=self.open_settings,
            icon_color=colors["text_primary"],
            bgcolor=colors["bg_secondary"],
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                overlay_color=colors["border"]
            )
        )
        
        self.computer_button = ft.IconButton(
            icon=ft.Icons.COMPUTER,
            tooltip="System",
            on_click=self.open_system_page,
            icon_color=colors["text_primary"],
            bgcolor=colors["bg_secondary"],
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                overlay_color=colors["border"]
            )
        )
        
        self.refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Clear Chat",
            on_click=self.clear_chat,
            icon_color=colors["text_primary"],
            bgcolor=colors["bg_secondary"],
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                overlay_color=colors["border"]
            )
        )
        
        self.header = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY, color=colors["accent"], size=30),
                        ft.Text("🔊 SourceBox OmniLocal", size=20, weight=ft.FontWeight.BOLD, color=colors["text_primary"])
                    ], spacing=10),
                    padding=ft.padding.only(left=20)
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Row([
                        self.computer_button,
                        self.settings_button,
                        self.refresh_button
                    ], spacing=10),
                    padding=ft.padding.only(right=20)
                )
            ]),
            height=80,
            bgcolor=colors["bg_secondary"],
            border=ft.border.only(bottom=ft.BorderSide(2, colors["border"])),
            padding=ft.padding.symmetric(vertical=15)
        )
        
        # Modern Chat display area
        self.chat_container = ft.ListView(
            expand=True,
            spacing=15,
            padding=ft.padding.all(25),
            auto_scroll=True
        )
        
        chat_area = ft.Container(
            content=self.chat_container,
            bgcolor="#111111",
            expand=True,
            margin=ft.margin.symmetric(horizontal=20, vertical=10)
        )
        
        # Modern Input area with beautiful styling
        self.input_field = ft.TextField(
            hint_text="✨ Ask me to launch apps, take screenshots, search the web, or get system info... (Press Enter to send, Shift+Enter for new line)",
            expand=True,
            multiline=True,
            max_lines=4,
            min_lines=1,
            on_submit=self.send_message,
            border_color="#333333",
            focused_border_color="#00d4ff",
            bgcolor="#1a1a1a",
            color="#ffffff",
            hint_style=ft.TextStyle(color="#888888"),
            text_style=ft.TextStyle(size=14),
            border_radius=15,
            content_padding=ft.padding.all(15),
            shift_enter=True,  # Enable Shift+Enter for new lines
            on_change=self.handle_input_key
        )
        
        # File attachment button with real functionality
        self.attach_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.ATTACH_FILE_ROUNDED,
                on_click=self.open_file_picker,
                icon_color="#888888",
                bgcolor="#2a2a2a",
                style=ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    overlay_color="#444444"
                ),
                tooltip="Upload files to chat"
            ),
            width=45,
            height=45
        )
        
        # Microphone button for audio recording (disabled if not supported)
        self.mic_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.MIC_ROUNDED,
                on_click=self.toggle_recording if self.voice_supported else None,
                icon_color="#888888" if not self.voice_supported else "#dddddd",
                bgcolor="#2a2a2a",
                style=ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    overlay_color="#444444"
                ),
                tooltip=("Record voice message" if self.voice_supported else "Voice recording unavailable in this build")
            ),
            width=45,
            height=45
        )
        
        self.send_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.SEND_ROUNDED,
                on_click=self.send_message,
                icon_color="#ffffff",
                bgcolor="#00d4ff",
                style=ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    overlay_color="#0099cc"
                )
            ),
            width=50,
            height=50
        )
        
        # File queue display - persistent inline display when files are attached
        # Get colors for file queue styling
        queue_colors = self.settings.get_theme_colors()
        self.file_queue_row = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.ATTACH_FILE,
                    size=16,
                    color=queue_colors["accent"]
                ),
                ft.Text(
                    "Files ready to send:",
                    size=12,
                    color=queue_colors["text_secondary"]
                ),
                # File chips will be added here dynamically
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.symmetric(horizontal=20, vertical=8),
            bgcolor=queue_colors["bg_secondary"],
            border=ft.border.only(top=ft.BorderSide(1, queue_colors["border"])),
            visible=False  # Initially hidden
        )
        
        input_area = ft.Container(
            content=ft.Row([
                self.input_field,
                self.attach_button,
                self.mic_button,
                self.send_button
            ], spacing=10),
            padding=ft.padding.all(20),
            bgcolor="#1a1a1a",
            border=ft.border.only(top=ft.BorderSide(2, "#333333")),
            margin=ft.margin.only(top=10)
        )
        
        # Modern status indicator
        self.status_text = ft.Text(
            "🟢 Ready",
            size=13,
            color="#00ff88",
            weight=ft.FontWeight.W_500
        )
        
        status_area = ft.Container(
            content=ft.Row([
                self.status_text,
                ft.Container(expand=True),
                ft.Text(
                    "SourceBox OmniLocal - Local AI, Unlimited Potential",
                    size=11,
                    color="#666666",
                    italic=True
                )
            ]),
            padding=ft.padding.symmetric(horizontal=25, vertical=10),
            bgcolor="#1a1a1a"
        )
        
        # Add beautiful welcome message
        self.add_system_message(
            "🔊 Welcome to SourceBox OmniLocal!\n\n" +
            "I'm your local-first AI assistant with powerful on-device capabilities:\n\n" +
            "💻 System & File Operations\n" +
            "  • File management & editing\n\n" +
            "  • Close running applications\n\n" +
            "🎮 Media & Entertainment\n" +
            "  • Game launching (Steam/Epic/Origin)\n" +
            "  • Wallpaper management\n\n" +
            "🌐 Web & Research\n" +
            "  • Web search (DuckDuckGo)\n" +
            "  • Full webpage content extraction\n\n" +
            "🎨 Creative Tools\n" +
            "  • AI image generation\n" +
            "  • Screenshot capture\n\n" +
            "💡 Just type what you need help with!"
        )
        
        # Store UI components for navigation
        self.chat_area = chat_area
        self.input_area = input_area
        self.status_area = status_area
        
        # Create main content container for page switching
        self.main_content = ft.Column([
            chat_area,
            self.file_queue_row,  # Add file queue display
            input_area,
            status_area
        ], expand=True, spacing=0)
        
        # Main layout with modern structure
        self.page.add(
            ft.Column([
                self.header,
                self.main_content
            ], expand=True, spacing=0)
        )
        
        # Apply the saved theme on startup
        self.apply_theme()
        # If MCP is enabled, try discovery on startup so wrappers are available immediately
        try:
            if MCP_AVAILABLE and self.settings.get("mcp", "enabled"):
                threading.Thread(target=self.try_attach_mcp_tools, daemon=True).start()
        except Exception:
            pass
        
    def create_settings_page(self):
        """Create the settings page UI with dynamic theming"""
        # Get current theme colors
        colors = self.settings.get_theme_colors()
        
        # Settings header with back button
        settings_header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Back to Chat",
                    on_click=self.back_to_chat,
                    icon_color=colors["text_primary"],
                    bgcolor=colors["bg_secondary"],
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        overlay_color=colors["border"]
                    )
                ),
                ft.Text(
                    "Settings", 
                    size=24, 
                    weight=ft.FontWeight.W_600,
                    color=colors["text_primary"]
                ),
                ft.Container(expand=True)
            ]),
            padding=ft.padding.all(20),
            bgcolor=colors["bg_secondary"],
            border=ft.border.only(bottom=ft.BorderSide(2, colors["border"]))
        )
        
        # Settings content
        settings_content = ft.Container(
            content=ft.Column([
                # Theme Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("🎨 Appearance", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                        ft.Divider(color=colors["border"], height=1),
                        ft.Row([
                            ft.Text("Theme", color=colors["text_primary"], size=14),
                            ft.Container(expand=True),
                            ft.Dropdown(
                                width=150,
                                value=self.settings.get("appearance", "theme"),
                                options=[
                                    ft.dropdown.Option("Dark"),
                                    ft.dropdown.Option("Light"),
                                    ft.dropdown.Option("Auto")
                                ],
                                bgcolor=colors["bg_tertiary"],
                                color=colors["text_primary"],
                                border_color=colors["border"],
                                on_change=self.on_theme_change
                            )
                        ]),
                        ft.Row([
                            ft.Text("Accent Color", color=colors["text_primary"], size=14),
                            ft.Container(expand=True),
                            ft.Dropdown(
                                width=150,
                                value=self.settings.get("appearance", "accent_color"),
                                options=[
                                    ft.dropdown.Option("Blue"),
                                    ft.dropdown.Option("Green"),
                                    ft.dropdown.Option("Purple"),
                                    ft.dropdown.Option("Orange")
                                ],
                                bgcolor=colors["bg_tertiary"],
                                color=colors["text_primary"],
                                border_color=colors["border"],
                                on_change=self.on_accent_change
                            )
                        ])
                    ]),
                    padding=ft.padding.all(20),
                    margin=ft.margin.all(10),
                    bgcolor=colors["bg_secondary"],
                    border_radius=10,
                    border=ft.border.all(1, colors["border"])
                ),
                
                # Model Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("🤖 AI Model", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                        ft.Divider(color=colors["border"], height=1),
                        ft.Row([
                            ft.Text("Model", color=colors["text_primary"], size=14),
                            ft.Container(expand=True),
                            ft.Dropdown(
                                width=200,
                                value=self.settings.get("ai_model", "model"),
                                options=[
                                    ft.dropdown.Option("llama3.1"),
                                    ft.dropdown.Option("qwen3")
                                ],
                                bgcolor=colors["bg_tertiary"],
                                color=colors["text_primary"],
                                border_color=colors["border"],
                                on_change=self.on_model_change
                            )
                        ])
                    ]),
                    padding=ft.padding.all(20),
                    margin=ft.margin.all(10),
                    bgcolor=colors["bg_secondary"],
                    border_radius=10,
                    border=ft.border.all(1, colors["border"])
                ),
                
                # Tools Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("🛠️ Tools & Features", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                        ft.Divider(color=colors["border"], height=1),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "screenshot_tool"),
                                active_color="#00d4ff",
                                on_change=lambda event_param: self.on_tool_toggle("screenshot_tool", event_param.control.value)
                            ),
                            ft.Text("Screenshot Tool", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "web_search"),
                                active_color="#00d4ff",
                                on_change=lambda event_param: self.on_tool_toggle("web_search", event_param.control.value)
                            ),
                            ft.Text("Web Search", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "file_operations"),
                                active_color="#00d4ff",
                                on_change=lambda event_param: self.on_tool_toggle("file_operations", event_param.control.value)
                            ),
                            ft.Text("File Operations", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "game_launcher"),
                                active_color="#00d4ff",
                                on_change=lambda event_param: self.on_tool_toggle("game_launcher", event_param.control.value)
                            ),
                            ft.Text("Game Launcher", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "image_generation"),
                                active_color="#00d4ff",
                                on_change=lambda event_param: self.on_tool_toggle("image_generation", event_param.control.value)
                            ),
                            ft.Text("Image Generation", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "image_description"),
                                active_color="#00d4ff",
                                on_change=lambda event_param: self.on_tool_toggle("image_description", event_param.control.value)
                            ),
                            ft.Text("Image Description", color=colors["text_primary"], size=14)
                        ])
                    ]),
                    padding=ft.padding.all(20),
                    margin=ft.margin.all(10),
                    bgcolor=colors["bg_secondary"],
                    border_radius=10,
                    border=ft.border.all(1, colors["border"])
                ),
                
                # Ollama Connection & Model Check Section
                self.create_ollama_status_section(colors),
                
                # API Keys Configuration Section
                self.create_api_keys_section(colors),
                
                # MCP (Model Context Protocol) Section
                self.create_mcp_section(colors),
                
                # About Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("ℹ️ About", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                        ft.Divider(color=colors["border"], height=1),
                        ft.Text("SourceBox OmniLocal v1.0", color=colors["text_primary"], size=14, weight=ft.FontWeight.W_500),
                        ft.Text("Local-first AI desktop assistant", color=colors["text_secondary"], size=12),
                        ft.Text("© 2024 SourceBox LLC", color=colors["text_secondary"], size=12),
                        ft.Text("Built with Flet & Python", color=colors["text_secondary"], size=12)
                    ]),
                    padding=ft.padding.all(20),
                    margin=ft.margin.all(10),
                    bgcolor=colors["bg_secondary"],
                    border_radius=10,
                    border=ft.border.all(1, colors["border"])
                ),
                
                # Save & Restart Button
                self.create_save_button(colors)
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=ft.padding.all(10),
            bgcolor=colors["bg_primary"]
        )
        
        return ft.Column([
            settings_header,
            settings_content
        ], expand=True, spacing=0)
        
    def create_system_page(self):
        """Create the system page UI with dynamic theming"""
        # Get current theme colors
        colors = self.settings.get_theme_colors()
        
        # System page header with back button
        system_header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Back to Chat",
                    on_click=self.back_to_chat,
                    icon_color=colors["text_primary"],
                    bgcolor=colors["bg_secondary"],
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        overlay_color=colors["border"]
                    )
                ),
                ft.Text(
                    "System", 
                    size=24, 
                    weight=ft.FontWeight.W_600,
                    color=colors["text_primary"]
                ),
                ft.Container(expand=True)
            ]),
            padding=ft.padding.all(20),
            bgcolor=colors["bg_secondary"],
            border=ft.border.only(bottom=ft.BorderSide(2, colors["border"]))
        )
        
        # System content - placeholder for now
        system_content = ft.Container(
            content=ft.Column([
                # System Info Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("💻 System Information", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                        ft.Divider(color=colors["border"], height=1),
                        
                        # OS Information
                        ft.Text("🖥️ Operating System", size=16, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                        ft.Text(f"OS: {platform.system()} {platform.release()} ({platform.version()})", color=colors["text_primary"], size=14),
                        ft.Text(f"Architecture: {platform.machine()}", color=colors["text_primary"], size=14),
                        ft.Text(f"Node Name: {platform.node()}", color=colors["text_primary"], size=14),
                        ft.Text(f"Windows Edition: {platform.win32_edition() if hasattr(platform, 'win32_edition') else 'N/A'}", color=colors["text_primary"], size=14),
                        ft.Divider(color=colors["border"], height=1),
                        
                        # Hardware Information
                        ft.Text("🔌 Hardware", size=16, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                        ft.Text(f"Processor: {platform.processor()}", color=colors["text_primary"], size=14),
                        ft.Text(f"CPU Cores: {psutil.cpu_count(logical=False)} Physical, {psutil.cpu_count(logical=True)} Logical", color=colors["text_primary"], size=14),
                        ft.Text(f"Total RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB", color=colors["text_primary"], size=14),
                        ft.Text(f"Available RAM: {round(psutil.virtual_memory().available / (1024**3), 2)} GB", color=colors["text_primary"], size=14),
                        ft.Text(f"RAM Usage: {psutil.virtual_memory().percent}%", color=colors["text_primary"], size=14),
                        ft.Divider(color=colors["border"], height=1),
                        
                        # Disk Information
                        ft.Text("💾 Storage", size=16, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                        *self.get_disk_info(colors),
                        ft.Divider(color=colors["border"], height=1),
                        
                        # User Information
                        ft.Text("👤 User", size=16, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                        ft.Text(f"Current User: {os.getlogin()}", color=colors["text_primary"], size=14),
                        ft.Text(f"User Home: {os.path.expanduser('~')}", color=colors["text_primary"], size=14),
                    ]),
                    padding=ft.padding.all(20),
                    margin=ft.margin.all(10),
                    bgcolor=colors["bg_secondary"],
                    border_radius=10,
                    border=ft.border.all(1, colors["border"])
                ),
                
                # Live System Metrics Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("📈 Live System Metrics", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                        ft.Divider(color=colors["border"], height=1),
                        
                        # CPU Usage Graph
                        ft.Container(
                            content=ft.Column([
                                ft.Text("CPU Usage", size=16, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text("0%", color=colors["text_secondary"], size=12),
                                        alignment=ft.alignment.center_left,
                                        width=30
                                    ),
                                    self.cpu_chart_container,
                                    ft.Container(
                                        content=ft.Text("100%", color=colors["text_secondary"], size=12),
                                        alignment=ft.alignment.center_right,
                                        width=40
                                    ),
                                ]),
                                ft.Container(height=10),
                            ])
                        ),
                        
                        # RAM Usage Graph
                        ft.Container(
                            content=ft.Column([
                                ft.Text("RAM Usage", size=16, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text("0%", color=colors["text_secondary"], size=12),
                                        alignment=ft.alignment.center_left,
                                        width=30
                                    ),
                                    self.ram_chart_container,
                                    ft.Container(
                                        content=ft.Text("100%", color=colors["text_secondary"], size=12),
                                        alignment=ft.alignment.center_right,
                                        width=40
                                    ),
                                ]),
                                ft.Container(height=10),
                            ])
                        ),
                        
                        # GPU Usage Chart
                        ft.Container(
                            content=ft.Column([
                                ft.Text("GPU Usage", size=16, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text("0%", color=colors["text_secondary"], size=12),
                                        alignment=ft.alignment.center_left,
                                        width=30
                                    ),
                                    self.gpu_chart_container,
                                    ft.Container(
                                        content=ft.Text("100%", color=colors["text_secondary"], size=12),
                                        alignment=ft.alignment.center_right,
                                        width=40
                                    ),
                                ]),
                                ft.Container(height=10),
                            ])
                        ),
                        
                        # System Stats Text
                        self.live_stats_text,
                    ]),
                    padding=ft.padding.all(20),
                    margin=ft.margin.all(10),
                    bgcolor=colors["bg_secondary"],
                    border_radius=10,
                    border=ft.border.all(1, colors["border"])
                ),
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=ft.padding.all(10),
            bgcolor=colors["bg_primary"]
        )
        
        return ft.Column([
            system_header,
            system_content
        ], expand=True, spacing=0)
    
    def open_system_page(self, e=None):
        """Open the system page"""
        # Get current theme colors
        colors = self.settings.get_theme_colors()
        
        # Create initial data for charts
        if not hasattr(self, 'cpu_history'):
            self.cpu_history = [0] * 60
            self.ram_history = [0] * 60
        
        # Always make sure GPU histories are initialized (might be first time or after update)
        self.gpu_histories = []
        self.gpu_names = []
        self.gpu_count = 0
            
        # Try to get initial GPU data for all available GPUs
        try:
            gpus = GPUtil.getGPUs()
            self.gpu_count = len(gpus)
            
            # Initialize histories for each GPU
            if self.gpu_count > 0:
                for gpu in gpus:
                    self.gpu_histories.append([0] * 60)
                    self.gpu_names.append(gpu.name)
                    # Set initial value for each GPU
                    self.gpu_histories[-1][-1] = gpu.load * 100  # Convert to percentage
            
            # Ensure at least one GPU history exists even if no GPUs
            if self.gpu_count == 0:
                self.gpu_histories = [[0] * 60]  # Default empty history
                self.gpu_names = ["No GPU detected"]
        
        except Exception as e:
            print(f"GPU initialization error: {str(e)}")
            self.gpu_histories = [[0] * 60]  # Default empty history
            self.gpu_names = ["GPU Error"]
            self.gpu_count = 0
        
        # Initialize chart containers before creating system page
        self.cpu_chart_container = ft.Container(expand=True, height=150)
        self.ram_chart_container = ft.Container(expand=True, height=150)
        self.gpu_chart_container = ft.Container(expand=True, height=150)
        self.live_stats_text = ft.Text("Initializing system metrics...", color=colors["text_secondary"], size=14)
        
        # Get initial CPU and RAM usage values
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_percent = psutil.virtual_memory().percent
        
        # Initialize history data with real values
        self.cpu_history = [0] * 59 + [cpu_percent]
        self.ram_history = [0] * 59 + [ram_percent]
        
        # Initialize the charts with the CPU and RAM data
        cpu_chart = self.create_chart(self.cpu_history, colors["accent"])
        ram_chart = self.create_chart(self.ram_history, "#4CAF50")
        self.cpu_chart_container.content = cpu_chart
        self.ram_chart_container.content = ram_chart
        
        # Create multiple GPU charts if available
        if self.gpu_count > 0:
            # Create a column to hold all GPU charts
            gpu_charts_column = ft.Column(spacing=5)
            
            # Create a chart for each GPU
            gpu_colors = ["#FF9800", "#E91E63"]  # Orange and Pink for different GPUs
            for i in range(min(2, self.gpu_count)):  # Limit to 2 GPUs for now to avoid cluttering
                gpu_label = ft.Text(f"{self.gpu_names[i]}", size=14, weight=ft.FontWeight.W_500, color=colors["text_primary"])
                gpu_chart = self.create_chart(self.gpu_histories[i], gpu_colors[i % len(gpu_colors)])
                gpu_charts_column.controls.append(gpu_label)
                gpu_charts_column.controls.append(gpu_chart)
            
            self.gpu_chart_container.content = gpu_charts_column
        else:
            # No GPUs detected
            self.gpu_chart_container.content = ft.Text("No GPU detected", color=colors["text_secondary"])
        
        # Create the system page - this will now reference the initialized containers
        system_page = self.create_system_page()
        
        # Replace main content with system page
        self.main_content.controls = [system_page]
        self.page.update()
        
        # Now that controls are added to the page, start updating metrics
        self.timer_active = True
        print("Setting up system metrics update interval (direct approach)")
        
        # Do an initial update
        self.update_system_metrics()
        
        # Create a timer thread function that directly updates without invoke_async
        def timer_thread_function():
            print("Timer thread started")
            update_count = 0
            while self.timer_active:
                try:
                    # Sleep for 1 second
                    time.sleep(1)
                    # Call update if timer is still active
                    if self.timer_active:
                        update_count += 1
                        if update_count % 5 == 0:  # Log every 5 seconds
                            print(f"Timer thread still active, update #{update_count}")
                        # Direct call to update metrics - no fancy API methods needed
                        self.update_system_metrics()
                except Exception as e:
                    print(f"Error in timer thread: {str(e)}")
            print("Timer thread exiting")
        
        # Start the timer thread
        self.timer_thread = threading.Thread(target=timer_thread_function, daemon=True)
        self.timer_thread.start()
    
    def back_to_chat(self, e=None):
        """Navigate back to the chat interface"""
        # Stop the system metrics updates
        if hasattr(self, 'timer_active'):
            self.timer_active = False  # This will exit the timer thread loop
        
        # Restore the chat UI
        self.main_content.controls = [
            self.chat_area,
            self.file_queue_row,
            self.input_area,
            self.status_area
        ]
        self.page.update()
        
    def open_settings(self, e=None):
        """Open the settings page"""
        # Create the settings page
        settings_page = self.create_settings_page()
        
        # Replace main content with settings page
        self.main_content.controls = [settings_page]
        self.page.update()
        
    def get_disk_info(self, colors):
        """Get formatted disk information for all drives"""
        disk_info = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for partition in partitions:
                if os.name == 'nt' and ('cdrom' in partition.opts or partition.fstype == ''):
                    # Skip CD-ROM drives with no media
                    continue
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append(ft.Text(
                        f"Drive {partition.device} ({partition.mountpoint}): {partition.fstype}", 
                        color=colors["text_primary"], 
                        size=14, 
                        weight=ft.FontWeight.W_500
                    ))
                    disk_info.append(ft.Text(
                        f"  Total: {self.format_bytes(usage.total)}, Used: {self.format_bytes(usage.used)} ({usage.percent}%), Free: {self.format_bytes(usage.free)}", 
                        color=colors["text_primary"], 
                        size=14
                    ))
                except Exception:
                    # Some drives may not be accessible
                    disk_info.append(ft.Text(
                        f"Drive {partition.device}: [Could not access drive]", 
                        color=colors["text_secondary"], 
                        size=14
                    ))
        except Exception as e:
            disk_info.append(ft.Text(
                f"Could not retrieve disk information: {str(e)}", 
                color=colors["text_secondary"], 
                size=14
            ))
        
        # If no drives were found, add a message
        if not disk_info:
            disk_info.append(ft.Text(
                "No drives found", 
                color=colors["text_secondary"], 
                size=14
            ))
            
        return disk_info

    def get_network_info(self, colors):
        """Get formatted network information"""
        network_info = []
        
        try:
            # Get active network connections
            net_if_addrs = psutil.net_if_addrs()
            for interface_name, interface_addresses in net_if_addrs.items():
                network_info.append(ft.Text(
                    f"Interface: {interface_name}", 
                    color=colors["text_primary"], 
                    size=14,
                    weight=ft.FontWeight.W_500
                ))
                
                for address in interface_addresses:
                    if address.family == socket.AF_INET:  # IPv4
                        network_info.append(ft.Text(
                            f"  IPv4: {address.address}, Netmask: {address.netmask}", 
                            color=colors["text_primary"], 
                            size=14
                        ))
                    elif address.family == socket.AF_INET6:  # IPv6
                        network_info.append(ft.Text(
                            f"  IPv6: {address.address}", 
                            color=colors["text_primary"], 
                            size=14
                        ))
                    elif address.family == psutil.AF_LINK:  # MAC
                        network_info.append(ft.Text(
                            f"  MAC: {address.address}", 
                            color=colors["text_primary"], 
                            size=14
                        ))
                
                # Add a spacer between interfaces
                network_info.append(ft.Container(height=5))
        except Exception as e:
            network_info.append(ft.Text(
                f"Could not retrieve network information: {str(e)}", 
                color=colors["text_secondary"], 
                size=14
            ))
        
        return network_info
    
    def create_chart(self, data, color):
        """Create an animated line chart from data points"""
        colors = self.settings.get_theme_colors()
        
        # Create data points for LineChart
        data_points = []
        for i, value in enumerate(data):
            data_points.append(ft.LineChartDataPoint(x=i, y=value))
        
        # Create data series with the points
        data_series = ft.LineChartData(
            data_points=data_points,
            stroke_width=3,
            color=color,
            curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=ft.Colors.with_opacity(0.2, color),
        )
        
        # Create the line chart with animation
        chart = ft.LineChart(
            data_series=[data_series],
            border=ft.border.all(1, colors["border"]),
            horizontal_grid_lines=ft.ChartGridLines(interval=25, color=colors["border"], width=1),
            vertical_grid_lines=ft.ChartGridLines(interval=15, color=colors["border"], width=0.5),
            left_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=0, label=ft.Text("0%")), 
                                           ft.ChartAxisLabel(value=100, label=ft.Text("100%"))]),
            bottom_axis=None,  # Hide bottom axis
            interactive=True,
            min_y=0,
            max_y=100,
            min_x=0,
            max_x=59,
            tooltip_bgcolor=colors["bg_secondary"],
            animate=1000,  # 1000ms animation duration
            expand=True,
        )
        
        return chart
    
    def update_system_metrics(self, e=None):
        """Update the system metrics and charts"""
        # Debug print to track if this is being called
        current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{current_time}] update_system_metrics called")
        
        try:
            # Check if timer is active and if we're on the system page - if not, don't update
            if not hasattr(self, 'timer_active') or not self.timer_active:
                print(f"[{current_time}] Timer not active, skipping update")
                return
            
            # Check if the chart containers exist
            if not hasattr(self, 'cpu_chart_container') or not hasattr(self, 'ram_chart_container'):
                return
            
            # Get current CPU and RAM usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram_percent = psutil.virtual_memory().percent
            
            # Try to get GPU usage for all available GPUs
            gpu_data = []
            gpu_info_text = "No GPU"
            
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    # Collect data for each GPU
                    for i, gpu in enumerate(gpus):
                        gpu_percent = gpu.load * 100  # Convert to percentage
                        gpu_memory = f"{gpu.memoryUsed:.1f}/{gpu.memoryTotal:.1f} MB"
                        gpu_name = gpu.name
                        gpu_data.append({
                            'percent': gpu_percent,
                            'memory': gpu_memory,
                            'name': gpu_name
                        })
                    
                    # Create GPU info text for status line
                    if len(gpus) == 1:
                        # Single GPU format
                        gpu_info_text = f"GPU: {gpu_data[0]['percent']:.1f}% ({gpu_data[0]['name']})"
                    else:
                        # Multiple GPU format
                        gpu_info_text = f"GPUs: {', '.join([f'{gpu['name']}: {gpu['percent']:.1f}%' for gpu in gpu_data[:2]])}"
            except Exception as e:
                print(f"Error getting GPU data: {str(e)}")
            
            # Update history data
            if not hasattr(self, 'cpu_history'):
                self.cpu_history = [0] * 59 + [cpu_percent]
                self.ram_history = [0] * 59 + [ram_percent]
                # GPU histories are initialized in open_system_page
            else:
                # Update CPU and RAM histories
                self.cpu_history.pop(0)
                self.cpu_history.append(cpu_percent)
                self.ram_history.pop(0)
                self.ram_history.append(ram_percent)
                
                # Update GPU histories
                try:
                    if hasattr(self, 'gpu_histories') and self.gpu_histories:
                        # If we have GPU data from this update
                        if gpu_data:
                            # Update existing GPU histories
                            for i, gpu_info in enumerate(gpu_data):
                                if i < len(self.gpu_histories):
                                    self.gpu_histories[i].pop(0)
                                    self.gpu_histories[i].append(gpu_info['percent'])
                        else:
                            # No GPU data available, update with zeros
                            for history in self.gpu_histories:
                                history.pop(0)
                                history.append(0)
                except Exception as e:
                    print(f"Error updating GPU history: {str(e)}")
            
            # Get memory usage in GB
            ram_gb = psutil.virtual_memory().used / (1024**3)
            ram_total = psutil.virtual_memory().total / (1024**3)
            
            # Get disk IO stats
            try:
                disk_io = psutil.disk_io_counters()
                disk_read = disk_io.read_bytes / 1024 / 1024 if disk_io else 0  # MB
                disk_write = disk_io.write_bytes / 1024 / 1024 if disk_io else 0  # MB
            except:
                disk_read = 0
                disk_write = 0
            
            # Current timestamp
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Update text (if it exists)
            if hasattr(self, 'live_stats_text'):
                stats_text = f"CPU: {cpu_percent:.1f}% | RAM: {ram_gb:.1f}/{ram_total:.1f} GB ({ram_percent:.1f}%) | {gpu_info_text} | Disk Read: {disk_read:.1f} MB | Disk Write: {disk_write:.1f} MB | Updated: {timestamp}"
                if self.live_stats_text.value != stats_text:
                    self.live_stats_text.value = stats_text
                    try:
                        self.live_stats_text.update()
                    except:
                        print("Could not update live stats text")
            
            # Update charts with new data
            colors = self.settings.get_theme_colors()
            
            try:
                # Rebuild CPU chart with new data
                cpu_chart = self.create_chart(self.cpu_history, colors["accent"])
                self.cpu_chart_container.content = cpu_chart
                self.cpu_chart_container.update()
                
                # Rebuild RAM chart with new data
                ram_chart = self.create_chart(self.ram_history, "#4CAF50")
                self.ram_chart_container.content = ram_chart
                self.ram_chart_container.update()
                
                # Rebuild GPU charts with new data
                if hasattr(self, 'gpu_histories') and self.gpu_histories:
                    # Create a column to hold all GPU charts
                    gpu_charts_column = ft.Column(spacing=5)
                    
                    # Create a chart for each GPU
                    gpu_colors = ["#FF9800", "#E91E63"]  # Orange and Pink for different GPUs
                    for i in range(min(2, len(self.gpu_histories))):  # Limit to 2 GPUs for now
                        if i < len(self.gpu_names):
                            gpu_label = ft.Text(f"{self.gpu_names[i]}", 
                                               size=14, 
                                               weight=ft.FontWeight.W_500, 
                                               color=colors["text_primary"])
                            gpu_charts_column.controls.append(gpu_label)
                        
                        gpu_chart = self.create_chart(self.gpu_histories[i], gpu_colors[i % len(gpu_colors)])
                        gpu_charts_column.controls.append(gpu_chart)
                    
                    self.gpu_chart_container.content = gpu_charts_column
                    self.gpu_chart_container.update()
            except Exception as chart_error:
                print(f"Error updating charts: {str(chart_error)}")
                
            # Force refresh of the page
            self.page.update()
                
        except Exception as e:
            # If there's an error, just log it
            print(f"Error in update_system_metrics: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def update_live_stats_text(self):
        """Update the live stats text with current values"""
        try:
            # Get current stats
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            ram_used_gb = round(ram.used / (1024**3), 1)
            ram_total_gb = round(ram.total / (1024**3), 1)
            ram_percent = ram.percent
            
            # Get disk IO stats
            disk_io = psutil.disk_io_counters()
            read_mb = round(disk_io.read_bytes / (1024**2), 1) if disk_io else 0
            write_mb = round(disk_io.write_bytes / (1024**2), 1) if disk_io else 0
            
            # Format as text
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            stats_text = f"CPU: {cpu_percent}% | RAM: {ram_used_gb} GB / {ram_total_gb} GB ({ram_percent}%) | Disk Read: {read_mb} MB | Disk Write: {write_mb} MB | Updated: {current_time}"
            
            # Update the text control
            self.live_stats_text.value = stats_text
            self.live_stats_text.update()
        except Exception as e:
            self.live_stats_text.value = f"Error updating stats: {str(e)}"
            self.live_stats_text.update()
    
    def create_save_button(self, colors):
        """Create the save button and store reference for state control"""
        # Create button with initial state
        button_color = colors["accent"] if self.settings_changed else colors["bg_secondary"]
        text_color = "#ffffff" if self.settings_changed else colors["text_secondary"]
        
        self.save_button_widget = ft.ElevatedButton(
            "Save Changes",
            icon=ft.Icons.SAVE_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self.on_save_settings,
            bgcolor=button_color,
            color=text_color,
            width=200,
            height=50,
            disabled=not self.settings_changed,
        )
        
        help_text = "Make changes above to enable save" if not self.settings_changed else "✅ Settings are applied immediately and saved automatically"
        self.save_button_text = ft.Text(
            help_text,
            size=12,
            italic=True,
            color=colors["text_secondary"],
        )
        
        self.save_button = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.save_button_widget,
                    alignment=ft.alignment.center
                ),
                self.save_button_text
            ], spacing=10),
            padding=ft.padding.all(20),
            margin=ft.margin.all(10)
        )
        return self.save_button
    
    def create_ollama_status_section(self, colors):
        """Create the Ollama connection and model availability check section"""
        # Check Ollama status
        ollama_status = self._check_ollama_status()
        
        # Create status indicators
        server_status_color = "#00ff88" if ollama_status['server_running'] else "#ff4444"
        server_status_icon = "✅" if ollama_status['server_running'] else "❌"
        server_status_text = "Connected" if ollama_status['server_running'] else "Not Connected"
        
        # Model availability indicators
        qwen_status_color = "#00ff88" if ollama_status['has_qwen3'] else "#ff4444"
        qwen_status_icon = "✅" if ollama_status['has_qwen3'] else "❌"
        
        llama_status_color = "#00ff88" if ollama_status['has_llama31'] else "#ff4444"
        llama_status_icon = "✅" if ollama_status['has_llama31'] else "❌"
        
        # Create refresh button for re-checking status
        refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh Ollama Status",
            on_click=self.refresh_ollama_status,
            icon_color=colors["accent"],
            bgcolor=colors["bg_tertiary"],
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                overlay_color=colors["border"]
            )
        )
        
        # Build the content
        content_items = [
            ft.Row([
                ft.Text("🔌 Ollama Connection & Models", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                ft.Container(expand=True),
                refresh_button
            ]),
            ft.Divider(color=colors["border"], height=1),
            
            # Server status
            ft.Row([
                ft.Text(f"{server_status_icon} Ollama Server", color=colors["text_primary"], size=14),
                ft.Container(expand=True),
                ft.Text(server_status_text, color=server_status_color, size=14, weight=ft.FontWeight.W_500)
            ]),
            
            # Model availability
            ft.Row([
                ft.Text(f"{qwen_status_icon} Qwen3 Model", color=colors["text_primary"], size=14),
                ft.Container(expand=True),
                ft.Text("Available" if ollama_status['has_qwen3'] else "Not Found", 
                       color=qwen_status_color, size=14, weight=ft.FontWeight.W_500)
            ]),
            
            ft.Row([
                ft.Text(f"{llama_status_icon} Llama3.1 Model", color=colors["text_primary"], size=14),
                ft.Container(expand=True),
                ft.Text("Available" if ollama_status['has_llama31'] else "Not Found", 
                       color=llama_status_color, size=14, weight=ft.FontWeight.W_500)
            ])
        ]
        
        # Add error message if there's an issue
        if ollama_status['error']:
            content_items.append(
                ft.Container(
                    content=ft.Text(
                        f"⚠️ {ollama_status['error']}",
                        color="#ffaa00",
                        size=12,
                        italic=True
                    ),
                    padding=ft.padding.only(top=10),
                    bgcolor=colors["bg_tertiary"],
                    border_radius=5,
                    padding_all=10,
                    margin=ft.margin.only(top=10)
                )
            )
        
        # Add recommendations if models are missing
        if not ollama_status['has_qwen3'] and not ollama_status['has_llama31']:
            content_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "💡 No supported models found!",
                            color="#ffaa00",
                            size=13,
                            weight=ft.FontWeight.W_500
                        ),
                        ft.Text(
                            "Install a supported model:\n• ollama pull llama3.1\n• ollama pull qwen2.5",
                            color=colors["text_secondary"],
                            size=12
                        )
                    ], spacing=5),
                    padding=ft.padding.all(10),
                    bgcolor=colors["bg_tertiary"],
                    border_radius=5,
                    margin=ft.margin.only(top=10)
                )
            )
        
        # Show available models if server is running
        if ollama_status['server_running'] and ollama_status['available_models']:
            models_text = "\n".join([f"• {model}" for model in ollama_status['available_models'][:5]])  # Show first 5
            if len(ollama_status['available_models']) > 5:
                models_text += f"\n... and {len(ollama_status['available_models']) - 5} more"
            
            content_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"📋 Available Models ({len(ollama_status['available_models'])}):",
                            color=colors["text_primary"],
                            size=12,
                            weight=ft.FontWeight.W_500
                        ),
                        ft.Text(
                            models_text,
                            color=colors["text_secondary"],
                            size=11
                        )
                    ], spacing=5),
                    padding=ft.padding.all(10),
                    bgcolor=colors["bg_tertiary"],
                    border_radius=5,
                    margin=ft.margin.only(top=10)
                )
            )
        
        return ft.Container(
            content=ft.Column(content_items),
            padding=ft.padding.all(20),
            margin=ft.margin.all(10),
            bgcolor=colors["bg_secondary"],
            border_radius=10,
            border=ft.border.all(1, colors["border"])
        )
    
    def refresh_ollama_status(self, e):
        """Refresh the Ollama status and update the settings page"""
        # Navigate back to settings to refresh the status
        self.open_settings(e)
    
    def create_api_keys_section(self, colors):
        """Create the API Keys configuration section"""
        # Get current API key values
        replicate_key = self.settings.get("api_keys", "replicate_api_key")
        
        # Create masked display of API key (show only first 8 and last 4 characters)
        def mask_api_key(key):
            if not key or len(key) < 12:
                return key
            return f"{key[:8]}{'*' * (len(key) - 12)}{key[-4:]}"
        
        # Create text fields for API keys
        self.replicate_key_field = ft.TextField(
            label="Replicate API Key",
            value=replicate_key,
            hint_text="Enter your Replicate API key for image generation/description",
            password=True,
            can_reveal_password=True,
            width=400,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
            hint_style=ft.TextStyle(color=colors["text_secondary"]),
            on_change=self.on_api_key_change
        )
        
        # Test API key button
        test_button = ft.ElevatedButton(
            "Test Key",
            icon=ft.Icons.VERIFIED_USER,
            on_click=self.test_replicate_key,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )
        
        # Help text
        help_text = ft.Text(
            "💡 Get your free API key at: https://replicate.com/account/api-tokens",
            size=12,
            color=colors["text_secondary"],
            italic=True
        )
        
        content_items = [
            ft.Text("🔑 API Keys", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
            ft.Divider(color=colors["border"], height=1),
            
            # Replicate API Key section
            ft.Text("Replicate API Key", size=14, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
            ft.Text(
                "Required for image generation and image description tools",
                size=12,
                color=colors["text_secondary"]
            ),
            
            ft.Row([
                self.replicate_key_field,
                test_button
            ], spacing=10),
            
            help_text,
            
            # Status indicator
            ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.INFO_OUTLINE,
                        size=16,
                        color=colors["text_secondary"]
                    ),
                    ft.Text(
                        "API keys are stored securely and only used for tool functionality",
                        size=11,
                        color=colors["text_secondary"]
                    )
                ], spacing=8),
                padding=ft.padding.all(10),
                bgcolor=colors["bg_tertiary"],
                border_radius=5,
                margin=ft.margin.only(top=10)
            )
        ]
        
        return ft.Container(
            content=ft.Column(content_items, spacing=10),
            padding=ft.padding.all(20),
            margin=ft.margin.all(10),
            bgcolor=colors["bg_secondary"],
            border_radius=10,
            border=ft.border.all(1, colors["border"])
        )
    
    def create_mcp_section(self, colors):
        """Create the MCP (Model Context Protocol) configuration section"""
        # Read current MCP settings
        mcp_enabled = self.settings.get("mcp", "enabled") or False
        servers = self.settings.get("mcp", "servers") or []

        # Controls: enable switch and add-server fields
        self.mcp_enabled_switch = ft.Switch(
            value=mcp_enabled,
            label="Enable MCP integration",
            on_change=self.on_mcp_toggle,
            active_color=colors["accent"],
        )

        self.mcp_name_field = ft.TextField(
            label="Server Name",
            hint_text="e.g., Local MCP",
            width=180,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
            hint_style=ft.TextStyle(color=colors["text_secondary"]),
            on_submit=self.on_add_mcp_server,
        )

        # Server type selector (HTTP vs STDIO)
        self.mcp_type_field = ft.Dropdown(
            label="Server Type",
            value="HTTP",
            width=140,
            options=[ft.dropdown.Option("HTTP"), ft.dropdown.Option("STDIO")],
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
            on_change=self.on_mcp_type_change,
        )

        self.mcp_url_field = ft.TextField(
            label="Server URL",
            hint_text="http://localhost:4000",
            width=260,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
            hint_style=ft.TextStyle(color=colors["text_secondary"]),
            on_submit=self.on_add_mcp_server,
            visible=True,
        )

        # STDIO command and args
        self.mcp_cmd_field = ft.TextField(
            label="Command (STDIO)",
            hint_text="Path to python.exe or server binary",
            width=260,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
            hint_style=ft.TextStyle(color=colors["text_secondary"]),
            on_submit=self.on_add_mcp_server,
            visible=False,
        )

        self.mcp_args_field = ft.TextField(
            label="Args (STDIO)",
            hint_text="e.g., dummy_mcp_server\\server.py",
            width=260,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
            hint_style=ft.TextStyle(color=colors["text_secondary"]),
            on_submit=self.on_add_mcp_server,
            visible=False,
        )

        self.mcp_api_key_field = ft.TextField(
            label="API Key (optional)",
            hint_text="If your MCP server requires it",
            password=True,
            can_reveal_password=True,
            width=240,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
            hint_style=ft.TextStyle(color=colors["text_secondary"]),
            on_submit=self.on_add_mcp_server,
            visible=True,
        )

        add_button = ft.ElevatedButton(
            "Add Server",
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            on_click=self.on_add_mcp_server,
            bgcolor=colors["bg_tertiary"],
            color=colors["text_primary"],
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        # Server list UI
        server_rows = []
        if servers:
            for i, srv in enumerate(servers):
                name = srv.get("name", f"Server {i+1}")
                stype = (srv.get("type") or ("STDIO" if srv.get("command") else "HTTP")).upper()
                url = srv.get("url", "")
                cmd = srv.get("command", "")
                args = srv.get("args", [])
                detail = (
                    url if stype == "HTTP" else f"{cmd} {' '.join(args) if isinstance(args, list) else str(args)}"
                )
                server_rows.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(name, size=14, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
                                ft.Text(f"{stype} • {detail}", size=12, color=colors["text_secondary"]),
                            ], expand=True, spacing=2),
                            ft.TextButton(
                                "Test",
                                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                on_click=(lambda e, idx=i: self.test_mcp_server(idx)),
                                style=ft.ButtonStyle(color=colors["accent"]),
                            ),
                            ft.TextButton(
                                "Remove",
                                icon=ft.Icons.DELETE_OUTLINE,
                                on_click=(lambda e, idx=i: self.on_remove_mcp_server(idx)),
                                style=ft.ButtonStyle(color="#ff6666"),
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.symmetric(vertical=8, horizontal=10),
                        bgcolor=colors["bg_tertiary"],
                        border_radius=6,
                    )
                )
        else:
            server_rows.append(
                ft.Text("No MCP servers added yet.", size=12, color=colors["text_secondary"]) 
            )

        content_items = [
            ft.Text("🧩 MCP Integration (experimental)", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
            ft.Divider(color=colors["border"], height=1),
            ft.Text(
                "Model Context Protocol allows connecting external servers that provide additional tools and capabilities.",
                size=12,
                color=colors["text_secondary"],
            ),
            ft.Row([self.mcp_enabled_switch]),
            ft.Container(height=6),
            ft.Text("Add MCP Server", size=14, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
            ft.Row([
                self.mcp_name_field,
                self.mcp_type_field,
                self.mcp_url_field,
                self.mcp_cmd_field,
                self.mcp_args_field,
                self.mcp_api_key_field,
                add_button,
            ], wrap=True, spacing=10, run_spacing=10),
            ft.Container(height=6),
            ft.Text("Configured Servers", size=14, weight=ft.FontWeight.W_500, color=colors["text_primary"]),
            ft.Column(server_rows, spacing=8),
            # Inline status line for MCP actions
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=colors["text_secondary"]),
                    ft.Text("", size=12, color=colors["text_secondary"])
                ], spacing=8),
                padding=ft.padding.only(top=8)
            )
        ]
        # Keep reference to the status Text so we can update it later
        # The Text is the second control in the last Row above
        self.mcp_status_text = content_items[-1].content.controls[1]
        # Apply initial visibility based on selected type
        try:
            self._apply_mcp_type_visibility()
        except Exception:
            pass

        return ft.Container(
            content=ft.Column(content_items, spacing=10),
            padding=ft.padding.all(20),
            margin=ft.margin.all(10),
            bgcolor=colors["bg_secondary"],
            border_radius=10,
            border=ft.border.all(1, colors["border"]),
        )

    # ---------------- MCP helpers ----------------
    def _parse_stdio_args(self, args_str: str) -> list[str]:
        """Parse the Args textbox into a robust argv list.
        - Tries shlex.split(posix=False) first.
        - If a valid .py path with spaces/apostrophes is split, auto-join tokens until os.path.exists(candidate).
        """
        import os, shlex
        if not args_str:
            return []
        try:
            toks = shlex.split(args_str, posix=False)
        except ValueError:
            toks = [t for t in args_str.split() if t]
        # Strip wrapping quotes
        toks = [t.strip().strip('"').strip("'") for t in toks]
        # If any token already is an existing .py path, done
        for t in list(toks):
            if t.lower().endswith('.py') and os.path.exists(t):
                return toks
        # Try to join consecutive tokens into a .py path that exists
        n = len(toks)
        for i in range(n):
            for j in range(i, n):
                cand = " ".join(toks[i:j+1])
                if cand.lower().endswith('.py') and os.path.exists(cand):
                    return toks[:i] + [cand] + toks[j+1:]
        return toks

    def _repair_stdio_args(self, args_list: list[str]) -> list[str]:
        """Given a saved argv list, attempt to re-join tokens into a valid .py path if they were split.
        Leaves args untouched if already valid.
        """
        import os
        args = [a.strip().strip('"').strip("'") for a in (args_list or [])]
        # Already has valid .py path
        for a in args:
            if a.lower().endswith('.py') and os.path.exists(a):
                return args
        # Try to join sequences
        n = len(args)
        for i in range(n):
            for j in range(i, n):
                cand = " ".join(args[i:j+1])
                if cand.lower().endswith('.py') and os.path.exists(cand):
                    return args[:i] + [cand] + args[j+1:]
        return args

    def _apply_mcp_type_visibility(self):
        """Show only relevant inputs for the selected MCP server type."""
        stype = (self.mcp_type_field.value or "HTTP").upper()
        is_http = stype == "HTTP"
        # HTTP fields
        self.mcp_url_field.visible = is_http
        # STDIO fields
        self.mcp_cmd_field.visible = not is_http
        self.mcp_args_field.visible = not is_http
        # API key is generally relevant for HTTP only
        self.mcp_api_key_field.visible = is_http
        # Trigger redraw
        try:
            self.page.update()
        except Exception:
            pass

    def on_mcp_type_change(self, e):
        """Handle changes to server type dropdown and toggle field visibility."""
        self._apply_mcp_type_visibility()

    def on_mcp_toggle(self, e):
        """Enable/disable MCP and persist setting."""
        try:
            enabled = bool(e.control.value)
            self.settings.set("mcp", "enabled", enabled)
            self.settings_changed = True
            self.update_save_button_visibility()
            status = "enabled" if enabled else "disabled"
            self._set_mcp_status(f"MCP {status}", color="#00d4ff")
            # Kick off discovery when enabling
            if enabled:
                threading.Thread(target=self.try_attach_mcp_tools, daemon=True).start()
        except Exception as ex:
            print(f"Error updating MCP toggle: {ex}")

    def on_add_mcp_server(self, e):
        """Add a new MCP server from input fields (HTTP or STDIO)."""
        print("[MCP] Add Server clicked")
        self._set_mcp_status("Adding MCP server...", color="#00d4ff")
        name = (self.mcp_name_field.value or "").strip()
        stype = (self.mcp_type_field.value or "HTTP").strip().upper()
        url = (self.mcp_url_field.value or "").strip()
        cmd = (self.mcp_cmd_field.value or "").strip()
        args_str = (self.mcp_args_field.value or "").strip()
        api_key = (self.mcp_api_key_field.value or "").strip()

        if not name:
            self._set_mcp_status("Please provide a server name", color="#ffaa00")
            return

        server_entry = {"name": name, "type": stype}

        if stype == "HTTP":
            if not url:
                self._set_mcp_status("Please provide a server URL", color="#ffaa00")
                return
            if not (url.startswith("http://") or url.startswith("https://")):
                self._set_mcp_status("Server URL must start with http:// or https://", color="#ffaa00")
                return
            server_entry.update({"url": url, "api_key": api_key})
        else:  # STDIO
            if not cmd:
                self._set_mcp_status("Please provide a command for STDIO server", color="#ffaa00")
                return
            # Sanitize command (strip surrounding quotes)
            cmd_clean = cmd.strip().strip('"').strip("'")
            # Parse/repair args: auto-detect script paths with spaces/apostrophes and join into one token
            args_list = self._parse_stdio_args(args_str)
            server_entry.update({"command": cmd_clean, "args": args_list, "api_key": api_key})

        try:
            servers = self.settings.get("mcp", "servers") or []
            # Prevent duplicates: use (type,url) for HTTP or (type,command,args) for STDIO
            def is_duplicate(existing):
                if existing.get("type", "HTTP").upper() != stype:
                    return False
                if stype == "HTTP":
                    return existing.get("url") == server_entry.get("url")
                return existing.get("command") == server_entry.get("command") and (
                    (existing.get("args") or []) == (server_entry.get("args") or [])
                )

            if any(is_duplicate(s) for s in servers):
                self._set_mcp_status("That server is already in your list", color="#ffaa00")
                return

            servers.append(server_entry)
            # Persist
            self.settings.set("mcp", "servers", servers)
            self.settings_changed = True
            self.update_save_button_visibility()

            # Clear fields for convenience
            self.mcp_name_field.value = ""
            self.mcp_url_field.value = ""
            self.mcp_cmd_field.value = ""
            self.mcp_args_field.value = ""
            self.mcp_api_key_field.value = ""
            try:
                self.page.update()
            except Exception:
                pass

            # Re-open settings to refresh the list
            self.open_settings(None)
            self._set_mcp_status("MCP server added", color="#00ff88")
            # Attempt discovery immediately
            threading.Thread(target=self.try_attach_mcp_tools, daemon=True).start()
        except Exception as ex:
            print(f"Error adding MCP server: {ex}")
            self._set_mcp_status(f"Failed to add server: {str(ex)[:120]}...", color="#ff6666")

    def on_remove_mcp_server(self, server_index: int):
        """Remove an MCP server by index and refresh UI."""
        try:
            servers = self.settings.get("mcp", "servers") or []
            if 0 <= server_index < len(servers):
                removed = servers.pop(server_index)
                self.settings.set("mcp", "servers", servers)
                self.settings_changed = True
                self.update_save_button_visibility()
                self.open_settings(None)
                self._set_mcp_status(f"Removed server '{removed.get('name','Server')}'" , color="#ffaa00")
        except Exception as ex:
            print(f"Error removing MCP server: {ex}")
            self._set_mcp_status("Failed to remove server", color="#ff6666")

    def test_mcp_server(self, server_index: int):
        """Test MCP server connectivity.
        - HTTP: simple GET
        - STDIO: spawn process, initialize session, list tools
        """
        servers = self.settings.get("mcp", "servers") or []
        if not (0 <= server_index < len(servers)):
            self.update_status("Invalid server index", color="#ff6666")
            return
        srv = servers[server_index]
        name = srv.get("name", f"Server {server_index+1}")
        stype = (srv.get("type") or ("STDIO" if srv.get("command") else "HTTP")).upper()

        if stype == "HTTP":
            url = srv.get("url", "")
            if not url:
                self._set_mcp_status("Server URL missing", color="#ff6666")
                return
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    code = resp.getcode()
                    if 200 <= code < 400:
                        self._set_mcp_status(f"✅ MCP server '{name}' is reachable ({code})", color="#00ff88")
                        # If possible, perform a lightweight MCP handshake over HTTP and list tools.
                        if MCP_AVAILABLE:
                            def http_probe():
                                import asyncio
                                # Derive API endpoint: if URL ends with /healthz, replace with /mcp; otherwise append /mcp
                                base = url
                                norm = base.rstrip("/")
                                if norm.endswith("/healthz"):
                                    api = norm[: -len("/healthz")] + "/mcp"
                                else:
                                    api = norm + "/mcp"
                                try:
                                    async def do_http_test():
                                        async with streamablehttp_client(api, terminate_on_close=True) as (read, write, get_session_id):
                                            session = ClientSession(read, write)
                                            await session.initialize()
                                            tools = await session.list_tools()
                                            return tools
                                    tools_obj = asyncio.run(asyncio.wait_for(do_http_test(), timeout=10))
                                    try:
                                        # Attach wrappers immediately so chat can use them
                                        if tools_obj:
                                            self._attach_mcp_wrappers(srv, tools_obj)
                                        names = ", ".join([t.name for t in tools_obj.tools]) if getattr(tools_obj, 'tools', None) else "none"
                                        self._set_mcp_status(f"🔌 HTTP MCP handshake OK. Tools: {names}", color="#00ff88")
                                    except Exception as attach_ex:
                                        self._set_mcp_status(f"ℹ️ MCP OK but attach failed: {str(attach_ex)[:120]}...", color="#ffaa00")
                                except Exception as ex:
                                    self._set_mcp_status(f"ℹ️ HTTP reachable, MCP handshake skipped: {str(ex)[:120]}...", color="#ffaa00")
                            threading.Thread(target=http_probe, daemon=True).start()
                    else:
                        self._set_mcp_status(f"⚠️ MCP server responded with status {code}", color="#ffaa00")
            except urllib.error.URLError as ex:
                self._set_mcp_status(f"❌ Can't reach MCP server: {ex.reason}", color="#ff6666")
            except Exception as ex:
                self._set_mcp_status(f"❌ MCP test failed: {str(ex)[:60]}...", color="#ff6666")
            return

        # STDIO path
        if not MCP_AVAILABLE:
            self._set_mcp_status("Install 'mcp' package to enable STDIO MCP (pip install mcp)", color="#ffaa00")
            return
        # Sanitize potentially quoted values from stored settings
        cmd = (srv.get("command") or "").strip().strip('"').strip("'")
        args = [(str(a).strip().strip('"').strip("'")) for a in (srv.get("args") or [])]
        # Auto-repair in case the script path was saved split into multiple tokens
        try:
            args = self._repair_stdio_args(args)
        except Exception:
            pass
        # Show immediate feedback
        self._set_mcp_status("Testing STDIO server...", color="#00d4ff")
        
        def runner():
            import tempfile, os
            err_path = None
            try:
                # Pre-flight checks
                import shutil as _shutil
                if not cmd:
                    self._set_mcp_status("❌ Command is empty", color="#ff6666")
                    return
                cmd_exists = os.path.isabs(cmd) and os.path.exists(cmd)
                cmd_in_path = _shutil.which(cmd) is not None
                if not (cmd_exists or cmd_in_path):
                    self._set_mcp_status(f"❌ Command not found: {cmd}", color="#ff6666")
                    return
                async def _do_test():
                    # Capture server stderr for diagnostics
                    nonlocal err_path
                    err_f = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False)
                    err_path = err_f.name
                    try:
                        # Best-effort working directory: find first absolute existing path in args
                        cwd = None
                        script_path = None
                        for tok in args:
                            if os.path.isabs(tok) and os.path.exists(tok):
                                script_path = tok
                                cwd = os.path.dirname(tok)
                                break
                        # Unbuffered IO and verbose logging from the server
                        # Use base env + overrides to avoid losing required Windows env vars
                        env = os.environ.copy()
                        env.update({"PYTHONUNBUFFERED": "1", "DUMMY_MCP_LOG_LEVEL": "DEBUG", "PYTHONIOENCODING": "utf-8"})
                        # Harden launch: ensure '-u' and '--mode stdio' where appropriate
                        base = os.path.basename(cmd or "").lower()
                        final_args = list(args)
                        if base.startswith("python"):
                            if not final_args or final_args[0] != "-u":
                                final_args = ["-u"] + final_args
                        has_mode = any(a == "--mode" or a.startswith("--mode=") for a in final_args)
                        has_py = any(str(a).lower().endswith(".py") for a in final_args)
                        if has_py and not has_mode:
                            final_args += ["--mode", "stdio"]
                        params = StdioServerParameters(command=cmd, args=list(final_args), cwd=cwd, env=env)
                        async with stdio_client(params, errlog=err_f) as (read, write):
                            launch_arg = script_path or (args[0] if args else "")
                            self._set_mcp_status(f"Launching: {cmd} {launch_arg}", color="#00d4ff")
                            session = ClientSession(read, write)
                            await session.initialize()
                            tools = await session.list_tools()
                            tool_names = ", ".join([t.name for t in tools.tools]) if getattr(tools, 'tools', None) else "none"
                            self._set_mcp_status(f"✅ STDIO MCP '{name}' connected. Tools: {tool_names}", color="#00ff88")
                            try:
                                # Attach wrappers immediately so chat can use them
                                self._attach_mcp_wrappers(srv, tools)
                            except Exception as attach_ex:
                                self._set_mcp_status(f"ℹ️ MCP OK but attach failed: {str(attach_ex)[:120]}...", color="#ffaa00")
                    finally:
                        try:
                            err_f.flush()
                            err_f.close()
                        except Exception:
                            pass

                # Enforce timeout so UI doesn't hang forever
                asyncio.run(asyncio.wait_for(_do_test(), timeout=15))
            except BaseException as ex:
                # Try to surface server stderr if available
                tail = ""
                try:
                    if err_path and os.path.exists(err_path):
                        with open(err_path, "r", encoding="utf-8", errors="ignore") as f:
                            data = f.read()[-500:]
                            if data:
                                tail = f"\nServer stderr (last 500 chars):\n{data}"
                except Exception:
                    pass
                # Expand nested errors (e.g., ExceptionGroup) for clarity
                msg = str(ex)
                try:
                    import traceback as _tb
                    eg_details = ""
                    if hasattr(ex, 'exceptions') and isinstance(getattr(ex, 'exceptions'), (list, tuple)):
                        for i, sub in enumerate(ex.exceptions):
                            eg_details += f"\n  [{i+1}] {type(sub).__name__}: {sub}"
                    if eg_details:
                        msg = f"{msg}{eg_details}"
                except Exception:
                    pass
                if isinstance(ex, TimeoutError) or "Timeout" in msg:
                    self._set_mcp_status(f"❌ STDIO MCP test timed out after 15s. Verify Command & Args.{tail}", color="#ff6666")
                else:
                    self._set_mcp_status(f"❌ STDIO MCP test failed: {msg[:200]}...{tail}", color="#ff6666")
        
        t = threading.Thread(target=runner, daemon=True)
        t.start()

    def _set_mcp_status(self, message: str, color: str = None):
        """Update the inline MCP status text in settings, or fall back to global status."""
        try:
            if hasattr(self, "mcp_status_text") and self.mcp_status_text is not None:
                if color:
                    self.mcp_status_text.color = color
                self.mcp_status_text.value = message
                self.page.update()
            else:
                # Fall back to global status bar
                self.update_status(message, color or "#00d4ff")
        except Exception:
            # As a last resort, print
            print(message)
    
    def on_api_key_change(self, e):
        """Handle API key field changes"""
        # Save the API key to settings
        if e.control == self.replicate_key_field:
            self.settings.set("api_keys", "replicate_api_key", e.control.value)
            self.settings_changed = True
            self.update_save_button_visibility()
    
    def test_replicate_key(self, e):
        """Test the Replicate API key"""
        api_key = self.replicate_key_field.value
        if not api_key:
            self.show_api_key_test_result("❌ Please enter an API key first", "#ff4444")
            return
        
        try:
            # Set the API key temporarily for testing
            import os
            os.environ['REPLICATE_API_TOKEN'] = api_key
            
            # Try to make a simple API call to test the key
            import replicate
            # This is a lightweight test - just check if we can authenticate
            client = replicate.Client(api_token=api_key)
            # If we can create a client without error, the key format is valid
            self.show_api_key_test_result("✅ API key appears valid", "#00ff88")
            
        except ImportError:
            self.show_api_key_test_result("⚠️ Replicate package not installed", "#ffaa00")
        except Exception as ex:
            error_msg = str(ex)
            if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                self.show_api_key_test_result("❌ Invalid API key", "#ff4444")
            else:
                self.show_api_key_test_result(f"⚠️ Test failed: {error_msg[:50]}...", "#ffaa00")
    
    def show_api_key_test_result(self, message, color):
        """Show API key test result to user"""
        # For now, just print to console - could be enhanced with a dialog
        print(f"API Key Test: {message}")
        # TODO: Could add a temporary status message in the UI
        
    def add_user_message(self, message: str):
        """Add a user message to the chat"""
        colors = self.settings.get_theme_colors()
        user_msg = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, size=16, color=colors["accent"]),
                            ft.Text("You", size=13, weight=ft.FontWeight.W_600, color=colors["accent"])
                        ], spacing=8),
                        ft.Container(
                            content=ft.Text(
                                message, 
                                selectable=True,
                                size=14,
                                color=colors["text_primary"]
                            ),
                            margin=ft.margin.only(top=8)
                        )
                    ]),
                    bgcolor=colors["bg_secondary"],
                    padding=ft.padding.all(16),
                    border_radius=ft.border_radius.only(
                        top_left=20,
                        top_right=20,
                        bottom_left=20,
                        bottom_right=5
                    ),
                    width=500,
                    border=ft.border.all(1, colors["border"])
                )
            ]),
            margin=ft.margin.only(bottom=15)
        )
        self.chat_container.controls.append(user_msg)
        
    def add_agent_message(self, message: str):
        """Add an agent response to the chat with markdown rendering"""
        colors = self.settings.get_theme_colors()
        
        # Check if the message contains thinking sections
        if '<think>' in message and '</think>' in message:
            # Split message into parts and handle thinking sections
            message_parts = self._process_thinking_sections(message)
            content_column = [
                ft.Row([
                    ft.Icon(ft.Icons.SMART_TOY, size=16, color=colors["accent"]),
                    ft.Text("Agent", size=13, weight=ft.FontWeight.W_600, color=colors["accent"])
                ], spacing=8)
            ]
            
            # Add each part (thinking sections and regular content)
            for part in message_parts:
                if part['is_thinking']:
                    # Yellow thinking section
                    content_column.append(
                        ft.Container(
                            content=ft.Text(
                                part['content'],
                                size=13,
                                color="#ffcc00",  # Yellow color for thinking
                                italic=True,
                                selectable=True
                            ),
                            margin=ft.margin.only(top=8),
                            padding=ft.padding.all(8),
                            bgcolor=colors["bg_tertiary"],
                            border_radius=8,
                            border=ft.border.all(1, "#ffcc00")
                        )
                    )
                else:
                    # Regular markdown content
                    if part['content'].strip():  # Only add non-empty content
                        content_column.append(
                            ft.Container(
                                content=ft.Markdown(
                                    part['content'],
                                    selectable=True,
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    on_tap_link=self._on_link_tap
                                ),
                                margin=ft.margin.only(top=8)
                            )
                        )
        else:
            # No thinking sections, use regular markdown
            content_column = [
                ft.Row([
                    ft.Icon(ft.Icons.SMART_TOY, size=16, color=colors["accent"]),
                    ft.Text("Agent", size=13, weight=ft.FontWeight.W_600, color=colors["accent"])
                ], spacing=8),
                ft.Container(
                    content=ft.Markdown(
                        message,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        on_tap_link=self._on_link_tap
                    ),
                    margin=ft.margin.only(top=8)
                )
            ]
        
        agent_msg = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column(content_column),
                    bgcolor=colors["bg_secondary"],
                    padding=ft.padding.all(16),
                    border_radius=ft.border_radius.only(
                        top_left=20,
                        top_right=20,
                        bottom_left=5,
                        bottom_right=20
                    ),
                    width=500,
                    border=ft.border.all(1, colors["border"])
                ),
                ft.Container(expand=True)
            ]),
            margin=ft.margin.only(bottom=15)
        )
        self.chat_container.controls.append(agent_msg)
    
    def _process_thinking_sections(self, message: str):
        """Process message to separate thinking sections from regular content"""
        import re
        
        parts = []
        current_pos = 0
        
        # Find all <think>...</think> sections
        think_pattern = r'<think>(.*?)</think>'
        matches = list(re.finditer(think_pattern, message, re.DOTALL))
        
        for match in matches:
            # Add content before thinking section
            if match.start() > current_pos:
                before_content = message[current_pos:match.start()].strip()
                if before_content:
                    parts.append({
                        'content': before_content,
                        'is_thinking': False
                    })
            
            # Add thinking section
            thinking_content = match.group(1).strip()
            if thinking_content:
                parts.append({
                    'content': f"💭 {thinking_content}",  # Add thinking emoji
                    'is_thinking': True
                })
            
            current_pos = match.end()
        
        # Add remaining content after last thinking section
        if current_pos < len(message):
            remaining_content = message[current_pos:].strip()
            if remaining_content:
                parts.append({
                    'content': remaining_content,
                    'is_thinking': False
                })
        
        return parts
    
    def _on_link_tap(self, e):
        """Handle link clicks in markdown content"""
        import webbrowser
        try:
            webbrowser.open(e.data)
        except Exception:
            import traceback
            error_message = traceback.format_exc()
            print(f"Error opening link: PyInstaller packaging error")
    
    def _check_ollama_status(self):
        """Check Ollama server connection and available models"""
        import requests
        import json
        
        try:
            # Check if Ollama server is running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                # Check for required models (qwen3 and llama3.1)
                has_qwen3 = any('qwen' in model.lower() for model in available_models)
                has_llama31 = any('llama3.1' in model.lower() or 'llama3:latest' in model.lower() for model in available_models)
                
                return {
                    'server_running': True,
                    'available_models': available_models,
                    'has_qwen3': has_qwen3,
                    'has_llama31': has_llama31,
                    'error': None
                }
            else:
                return {
                    'server_running': False,
                    'available_models': [],
                    'has_qwen3': False,
                    'has_llama31': False,
                    'error': f"Server responded with status {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {
                'server_running': False,
                'available_models': [],
                'has_qwen3': False,
                'has_llama31': False,
                'error': "Cannot connect to Ollama server. Make sure Ollama is installed and running."
            }
        except Exception as e:
            return {
                'server_running': False,
                'available_models': [],
                'has_qwen3': False,
                'has_llama31': False,
                'error': f"Error checking Ollama: {str(e)}"
            }
        
    def add_tool_message(self, tool_name: str, result: str):
        """Add a tool execution result to the chat"""
        colors = self.settings.get_theme_colors()
        tool_msg = ft.Container(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.BUILD, size=16, color=colors["accent"]),
                        ft.Text(f"Tool: {tool_name}", size=13, weight=ft.FontWeight.W_600, color=colors["accent"])
                    ], spacing=8),
                    ft.Container(
                        content=ft.Text(
                            result, 
                            selectable=True, 
                            size=13,
                            color=colors["text_primary"],
                            font_family="Consolas"
                        ),
                        bgcolor=colors["bg_tertiary"],
                        padding=ft.padding.all(12),
                        border_radius=10,
                        margin=ft.margin.only(top=8),
                        border=ft.border.all(1, colors["border"])
                    )
                ]),
                bgcolor=colors["bg_secondary"],
                padding=ft.padding.all(16),
                border_radius=15,
                border=ft.border.all(1, colors["border"]),
                margin=ft.margin.symmetric(horizontal=50)
            ),
            margin=ft.margin.only(bottom=15)
        )
        self.chat_container.controls.append(tool_msg)
        
    def add_system_message(self, message: str):
        """Add a system message to the chat"""
        colors = self.settings.get_theme_colors()
        system_msg = ft.Container(
            content=ft.Container(
                content=ft.Text(
                    message, 
                    size=14, 
                    color=colors["text_secondary"], 
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_400
                ),
                padding=ft.padding.all(20),
                bgcolor=colors["bg_secondary"],
                border_radius=15,
                border=ft.border.all(1, colors["border"]),
                margin=ft.margin.symmetric(horizontal=40)
            ),
            margin=ft.margin.only(bottom=20)
        )
        self.chat_container.controls.append(system_msg)
        try:
            self.page.update()
        except Exception:
            pass
        
    def update_status(self, status: str, color: str = "#00d4ff"):
        """Update the status text"""
        self.status_text.value = status
        self.status_text.color = color
        self.page.update()
        
    def clear_chat(self, e):
        """Clear the chat history"""
        self.chat_container.controls.clear()
        self.setup_system_message()
        self.add_system_message("🤖 Chat cleared. Agent ready!")
        self.page.update()
        
    def open_settings(self, e):
        """Navigate to the settings page"""
        self.current_page = "settings"
        settings_page = self.create_settings_page()
        
        # Replace main content with settings page
        self.main_content.controls.clear()
        self.main_content.controls.append(settings_page)
        self.page.update()
        
    def back_to_chat(self, e):
        """Navigate back to the chat page"""
        self.current_page = "chat"
        
        # Restore chat interface
        self.main_content.controls.clear()
        self.main_content.controls.extend([
            self.chat_area,
            self.file_queue_row,  # Add file queue display back
            self.input_area,
            self.status_area
        ])
        
        # Restore file queue display if files are uploaded
        self.restore_file_queue_on_navigation()
        # Proactively attach MCP wrappers if enabled so the agent can use them immediately
        try:
            threading.Thread(target=self.try_attach_mcp_tools, daemon=True).start()
            # If MCP already discovered but not announced, announce now
            if getattr(self, "mcp_tool_names", []) and not getattr(self, "mcp_announce_done", False):
                self._announce_mcp_tools()
        except Exception:
            pass
        
        self.page.update()
        
    def on_theme_change(self, e):
        """Handle theme selection change"""
        new_theme = e.control.value
        self.settings.set("appearance", "theme", new_theme)
        self.settings_changed = True
        self.update_save_button_visibility()
        
    def on_accent_change(self, e):
        """Handle accent color change"""
        new_accent = e.control.value
        self.settings.set("appearance", "accent_color", new_accent)
        self.settings_changed = True
        self.update_save_button_visibility()
        
    def on_model_change(self, e):
        """Handle AI model selection change"""
        new_model = e.control.value
        self.settings.set("ai_model", "model", new_model)
        self.settings_changed = True
        self.update_save_button_visibility()
        
    def apply_theme(self):
        """Apply the current theme colors to the UI dynamically"""
        colors = self.settings.get_theme_colors()
        theme_name = self.settings.get("appearance", "theme")
        accent_name = self.settings.get("appearance", "accent_color")
        
        # Update page theme
        if theme_name == "Light":
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.bgcolor = colors["bg_primary"]
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.bgcolor = colors["bg_primary"]
        
        # Update custom theme with accent color
        self.page.theme = ft.Theme(
            color_scheme_seed=colors["accent"],
            use_material3=True
        )
        
        # Apply colors to existing UI components
        self.apply_colors_to_components(colors)
        
        # Update the page
        self.page.update()
        
        self.add_system_message(f"🎨 Theme applied: {theme_name} with {accent_name} accent")
        
    def apply_colors_to_components(self, colors):
        """Apply theme colors to existing UI components"""
        try:
            # Update header colors
            if hasattr(self, 'header'):
                self.header.bgcolor = colors["bg_secondary"]
                if hasattr(self.header, 'border'):
                    self.header.border = ft.border.only(bottom=ft.BorderSide(2, colors["border"]))
                
            # Update header buttons
            if hasattr(self, 'settings_button'):
                self.settings_button.icon_color = colors["text_primary"]
                self.settings_button.bgcolor = colors["bg_secondary"]
                self.settings_button.style = ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    overlay_color=colors["border"]
                )
                
            if hasattr(self, 'refresh_button'):
                self.refresh_button.icon_color = colors["text_primary"]
                self.refresh_button.bgcolor = colors["bg_secondary"]
                self.refresh_button.style = ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    overlay_color=colors["border"]
                )
                
            # Update main content container
            if hasattr(self, 'main_content'):
                self.main_content.bgcolor = colors["bg_primary"]
                
            # Update chat area colors
            if hasattr(self, 'chat_area'):
                self.chat_area.bgcolor = colors["bg_primary"]
                
            # Update input area colors
            if hasattr(self, 'input_area'):
                self.input_area.bgcolor = colors["bg_secondary"]
                
            # Update input field colors
            if hasattr(self, 'input_field'):
                self.input_field.bgcolor = colors["bg_secondary"]
                self.input_field.color = colors["text_primary"]
                self.input_field.border_color = colors["border"]
                self.input_field.focused_border_color = colors["accent"]
                
            # Update attach button colors
            if hasattr(self, 'attach_button'):
                if hasattr(self.attach_button, 'content'):
                    self.attach_button.content.icon_color = colors["text_secondary"]
                    self.attach_button.content.bgcolor = colors["bg_tertiary"]
                    
            # Update send button colors
            if hasattr(self, 'send_button'):
                # Find the IconButton inside the container
                if hasattr(self.send_button, 'content') and hasattr(self.send_button.content, 'bgcolor'):
                    self.send_button.content.bgcolor = colors["accent"]
                    
            # Update status area colors
            if hasattr(self, 'status_area'):
                self.status_area.bgcolor = colors["bg_secondary"]
                
            # Update status text color
            if hasattr(self, 'status_text'):
                self.status_text.color = colors["accent"]
                
            # Update file queue row colors
            if hasattr(self, 'file_queue_row'):
                self.file_queue_row.bgcolor = colors["bg_secondary"]
                if hasattr(self.file_queue_row, 'border'):
                    self.file_queue_row.border = ft.border.only(top=ft.BorderSide(1, colors["border"]))
                
                # Update file chips inside queue row
                if hasattr(self.file_queue_row, 'content') and self.file_queue_row.content is not None:
                    # Update queue header text color
                    if len(self.file_queue_row.content.controls) > 1 and hasattr(self.file_queue_row.content.controls[1], 'color'):
                        self.file_queue_row.content.controls[1].color = colors["text_secondary"]
                
        except Exception as e:
            print(f"Error applying colors to components: {e}")
        
    def on_tool_toggle(self, tool_name: str, enabled: bool):
        """Handle tool enable/disable toggle"""
        self.settings.set("tools", tool_name, enabled)
        self.settings_changed = True
        self.update_save_button_visibility()
        
    def update_save_button_visibility(self):
        """Update the save button state based on whether settings have changed"""
        if hasattr(self, 'save_button_widget') and self.save_button_widget:
            colors = self.settings.get_theme_colors()
            
            # Update button state
            self.save_button_widget.disabled = not self.settings_changed
            self.save_button_widget.bgcolor = colors["accent"] if self.settings_changed else colors["bg_secondary"]
            self.save_button_widget.color = "#ffffff" if self.settings_changed else colors["text_secondary"]
            
            # Update help text
            if hasattr(self, 'save_button_text') and self.save_button_text:
                help_text = "Make changes above to enable save" if not self.settings_changed else "⚠️ Settings require app restart to take effect"
                self.save_button_text.value = help_text
                
            # Update the page if we're on settings
            if hasattr(self, 'page') and self.current_page == "settings":
                self.page.update()
                
    def on_save_settings(self, e):
        """Handle save settings button click"""
        print("Debug: Save settings button clicked!")
        
        # Show popup informing user of manual restart requirement
        self.show_settings_saved_dialog()
        
    def show_settings_saved_dialog(self):
        """Show dialog informing user that settings are saved and require manual restart"""
        print("Debug: Adding settings saved dialog to overlay")
        
        # Get theme colors for consistent styling
        colors = self.settings.get_theme_colors()
        
        # Create semi-transparent background
        overlay_bg = ft.Container(
            bgcolor=ft.Colors.BLACK54,
            width=self.page.width,
            height=self.page.height,
            on_click=lambda event_param: self.dismiss_dialog()
        )
        
        # Create dialog content
        dialog = ft.Card(
            width=400,
            height=200,
            elevation=10,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    [   
                        ft.Text(
                            "Settings Saved",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=colors["text_primary"],
                        ),
                        ft.Divider(height=1, color=colors["border"]),
                        ft.Text(
                            "Your settings have been saved successfully. Changes will take effect the next time you start the application.",
                            size=14,
                            color=colors["text_secondary"],
                        ),
                        ft.Container(height=20),
                        ft.Row(
                            [   
                                ft.FilledButton(
                                    "OK",
                                    on_click=lambda event_param: self.dismiss_dialog(),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                ),
            ),
        )
        
        # Center the dialog
        dialog.left = (self.page.width - dialog.width) / 2
        dialog.top = (self.page.height - dialog.height) / 2
        
        self.page.overlay.clear()
        self.page.overlay.extend([overlay_bg, dialog])
        self.page.update()
        print("Debug: Settings saved dialog added to overlay")
    
    def dismiss_dialog(self):
        """Dismiss the dialog"""
        self.page.overlay.clear()
        self.page.update()
        
    def handle_input_key(self, e):
        """Handle input field key events for Enter key behavior"""
        # Note: In Flet, multiline TextFields with shift_enter=True should handle
        # Enter to send and Shift+Enter for new line automatically
        # This method can be used for additional input processing if needed
        pass
        
    def send_message(self, e):
        """Handle sending a message"""
        user_input = self.input_field.value.strip()
        if not user_input:
            return
            
        # Add user message to chat
        self.add_user_message(user_input)
        self.input_field.value = ""
        self.page.update()
        
        # Process message in background thread
        threading.Thread(target=self.process_message, args=(user_input,), daemon=True).start()
        
    def process_message(self, user_input: str):
        """Process the user message with Ollama"""
        try:
            self.update_status("✨ Thinking...", "#ff9500")
            
            # Prepare the message content with file attachments if any
            message_content = user_input
            
            # Include uploaded file contents if any
            if self.uploaded_files:
                file_contents = []
                for file_info in self.uploaded_files:
                    if file_info.get('content'):
                        file_contents.append(
                            f"\n--- FILE: {file_info['name']} ({file_info['document_type']}) ---\n" +
                            file_info['content'] +
                            f"\n--- END OF FILE: {file_info['name']} ---\n"
                        )
                    elif file_info.get('is_document') and file_info.get('processing_error'):
                        file_contents.append(
                            f"\n--- FILE: {file_info['name']} (Processing Error) ---\n" +
                            f"Error: {file_info['processing_error']}\n" +
                            f"--- END OF FILE: {file_info['name']} ---\n"
                        )
                
                if file_contents:
                    message_content = (
                        f"User message: {user_input}\n\n" +
                        f"Attached files ({len(file_contents)} document(s)):\n" +
                        "".join(file_contents)
                    )
                    
                    # Show user that files are being processed
                    processed_count = sum(1 for f in self.uploaded_files if f.get('content'))
                    if processed_count > 0:
                        self.add_system_message(
                            f"📄 Including {processed_count} processed document(s) in your message to the agent"
                        )
            
            # Add user message to conversation history
            self.messages.append({"role": "user", "content": message_content})
            
            # Debug: Show current tool settings
            print("\n=== CURRENT TOOL SETTINGS ===")
            tools_settings = self.settings.get("tools")
            print(f"Tools settings from file: {tools_settings}")
            
            # Make sure any MCP tools are dynamically attached if enabled and available
            try:
                self.try_attach_mcp_tools()
            except Exception as _mcp_attach_err:
                print(f"MCP attach warning: {_mcp_attach_err}")

            # Get available tools based on settings (now includes any mcp_* wrappers)
            available_tools = self.get_enabled_tools()
            
            # Get response from Ollama with tools
            current_model = self.settings.get("ai_model", "model")
            response: ChatResponse = chat(
                model=current_model,
                messages=self.messages,
                tools=available_tools,  # Only pass enabled tools
                stream=False
            )
            
            # Execute any requested tool calls
            for call in response.message.tool_calls or []:
                fn_name = call.function.name
                args = call.function.arguments or {}
                
                self.update_status(f"⚙️ Executing: {fn_name}...", "#00d4ff")
                
                # Check if the tool is enabled before executing
                if not self.is_tool_enabled(fn_name):
                    error_msg = f"This tool is disabled in settings: '{fn_name}'"
                    self.add_tool_message(fn_name, error_msg)
                    self.messages.append({
                        "role": "tool",
                        "name": fn_name,
                        "content": error_msg
                    })
                    continue
                
                # Execute the tool
                tool_functions = [tool.__name__ for tool in self.tools]
                if fn_name in tool_functions:
                    try:
                        # Get the function and its parameters for safer execution
                        tool_function = getattr(self, fn_name)
                        
                        # Special handling for PyInstaller packaged environment
                        try:
                            import inspect
                            # Get the function's parameter names
                            param_names = inspect.signature(tool_function).parameters.keys()
                            
                            # Filter arguments to only include those accepted by the function
                            filtered_args = {}
                            for param in param_names:
                                if param in args:
                                    filtered_args[param] = args[param]
                            
                            # Print debug info
                            print(f"Executing {fn_name} with args: {filtered_args}")
                            
                            # Execute with filtered arguments
                            result = tool_function(**filtered_args)
                            
                        except Exception as inner_error:
                            # Fallback method if inspect approach fails
                            print(f"Using fallback method for {fn_name}: {str(inner_error)}")
                            
                            # Directly map common argument names for specific functions
                            if fn_name == "launch_apps" and "app_name" in args:
                                result = tool_function(args["app_name"])
                            elif fn_name == "take_screenshot_wrapper" and "window_title" in args:
                                result = tool_function(args["window_title"])
                            elif fn_name == "web_search_wrapper" and "query" in args:
                                max_results = args.get("max_results", 5)
                                result = tool_function(args["query"], max_results)
                            elif fn_name == "get_system_info" and "info_type" in args:
                                result = tool_function(args["info_type"])
                            elif fn_name == "close_apps" and "app_name" in args:
                                result = tool_function(args["app_name"])
                            elif fn_name == "launch_game_wrapper" and "game_title" in args:
                                result = tool_function(args["game_title"])
                            else:
                                # For other functions, try with minimal arguments
                                result = tool_function() if not args else tool_function(**args)
                            
                        # Add the result to messages
                        self.add_tool_message(fn_name, result)
                        self.messages.append({
                            "role": "tool",
                            "name": fn_name,
                            "content": result
                        })
                    except Exception as tool_error:
                        error_msg = f"Error executing {fn_name}: {str(tool_error)}"
                        print(f"TOOL ERROR: {error_msg}")
                        self.add_tool_message(fn_name, error_msg)
                        self.messages.append({
                            "role": "tool",
                            "name": fn_name,
                            "content": error_msg
                        })
                else:
                    error_msg = f"Error: Tool '{fn_name}' is not available"
                    self.add_tool_message(fn_name, error_msg)
                    
                self.page.update()
            
            # Get final response incorporating tool results
            if response.message.tool_calls:
                self.update_status("💭 Generating response...", ft.Colors.BLUE_400)
                final: ChatResponse = chat(
                    model=current_model,
                    messages=self.messages
                )
                final_response = final.message.content
            else:
                final_response = response.message.content
                
            # Add agent response to chat
            self.add_agent_message(final_response)
            self.messages.append({"role": "assistant", "content": final_response})
            
            # Auto-clear file queue after successful message processing
            if self.uploaded_files:
                files_cleared = len(self.uploaded_files)
                self.clear_uploaded_files()
                self.update_uploaded_files_display()
                self.save_file_queue_state()
                self.add_system_message(
                    f"🧹 Cleared {files_cleared} file(s) from queue after successful processing"
                )
            
            self.update_status("🟢 Ready", "#00ff88")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.add_system_message(error_msg)
            self.update_status("🔴 Error", "#ff3333")
            
        self.page.update()

    def launch_apps(self, app_name: str = None) -> str:
        """Launch an application by name."""
        try:
            print(f"launch_apps called with: {app_name}")
            if not app_name:
                return "Error: No application name provided"
            result = launch_app(app_name)
            print(f"launch_app result: {result}")
            return result
        except Exception as e:
            print(f"Error in launch_apps: {str(e)}")
            return f"Error launching app: {str(e)}"

    def take_screenshot_wrapper(self, window_title: str = None) -> str:
        """Take a screenshot and save it to Desktop/Screenshots folder."""
        try:
            return take_screenshot(window_title=window_title)
        except Exception as exception_obj:
            import traceback
            error_message = traceback.format_exc()
            print(f"Screenshot error details: {error_message}")
            return f"Error taking screenshot: {str(exception_obj)}"

    def web_search_wrapper(self, query: str, max_results: int = 5) -> str:
        """Search the web for the given query using DuckDuckGo."""
        if isinstance(query, str) and query.strip():
            return web_search(query=query, max_results=max_results)
        else:
            return "Error: Invalid or empty search query. Please provide a valid search term."

    def get_system_info(self, info_type: str = "all") -> str:
        """Get system information based on the requested type."""
        return system_info(info_type=info_type)
        
    def close_apps(self, app_name: str) -> str:
        """Close applications by partial name match."""
        if isinstance(app_name, str) and app_name.strip():
            return close_app(app_name=app_name)
        else:
            return "Error: Invalid or empty application name. Please provide a valid application name."
            
    def launch_game_wrapper(self, game_title: str) -> str:
        """Find and launch a PC game by title."""
        if isinstance(game_title, str) and game_title.strip():
            return launch_game(game_title)
        else:
            return "Error: Invalid or empty game title. Please provide a valid game title."
            
    # File Operations Tool Wrappers
    def list_directory(self, path=None, pattern=None, show_hidden=False, sort_by="name", reverse=False) -> str:
        """List files and directories with filtering and sorting options.
        
        Args:
            path: Directory path to list (default: current working directory)
            pattern: Optional file pattern to filter (e.g., '*.txt')
            show_hidden: Whether to include hidden files
            sort_by: Sort method ('name', 'size', 'type', 'modified')
            reverse: Whether to reverse sort order
        """
        result = self.file_ops.list_directory(path, pattern, show_hidden, sort_by, reverse)
        if "error" in result and result["error"] is not None:
            return f"Error listing directory: {result['error']}"
        
        # Format the output in a readable way
        output = [f"📂 Directory: {result['current_path']}", ""] 
        
        # Directories
        if result['directories']:
            output.append(f"Directories ({result['total_dirs']}):")
            for idx, d in enumerate(result['directories'], 1):
                output.append(f"{idx}. 📁 {d['name']} - Modified: {d['modified_date']}")
            output.append("")
        
        # Files
        if result['files']:
            output.append(f"Files ({result['total_files']}):")
            for idx, f in enumerate(result['files'], 1):
                output.append(f"{idx}. 📄 {f['name']} - Size: {f['size_human']}, Modified: {f['modified_date']}")
        
        if not result['directories'] and not result['files']:
            output.append("(Empty directory)")
            
        return "\n".join(output)
    
    def copy_file(self, source, destination, overwrite=False) -> str:
        """Copy a file or directory to destination.
        
        Args:
            source: Source file or directory path
            destination: Destination path
            overwrite: Whether to overwrite if destination exists
        """
        result = self.file_ops.copy_item(source, destination, overwrite)
        if result.get("success"):
            item_type = result.get("type", "item")
            return f"✅ Successfully copied {item_type} from '{result['source']}' to '{result['destination']}'"
        else:
            return f"Error copying file: {result.get('error', 'Unknown error')}"
    
    def move_file(self, source, destination, overwrite=False) -> str:
        """Move a file or directory to destination.
        
        Args:
            source: Source file or directory path
            destination: Destination path
            overwrite: Whether to overwrite if destination exists
        """
        result = self.file_ops.move_item(source, destination, overwrite)
        if result.get("success"):
            item_type = result.get("type", "item")
            return f"✅ Successfully moved {item_type} from '{result['source']}' to '{result['destination']}'"
        else:
            return f"Error moving file: {result.get('error', 'Unknown error')}"
    
    def delete_file(self, path, recursive=False) -> str:
        """Delete a file or directory.
        
        Args:
            path: Path to delete
            recursive: For directories, whether to delete contents recursively
        """
        result = self.file_ops.delete_item(path, recursive)
        if result.get("success"):
            item_type = result.get("type", "item")
            return f"✅ Successfully deleted {item_type}: '{result['path']}'"
        else:
            return f"Error deleting file: {result.get('error', 'Unknown error')}"
    
    def rename_file(self, path, new_name) -> str:
        """Rename a file or directory.
        
        Args:
            path: Path to file or directory to rename
            new_name: New name (without path)
        """
        result = self.file_ops.rename_item(path, new_name)
        if result.get("success"):
            item_type = result.get("type", "item")
            return f"✅ Successfully renamed {item_type} from '{result['original']}' to '{result['new']}'"
        else:
            return f"Error renaming file: {result.get('error', 'Unknown error')}"
    
    def create_directory(self, path) -> str:
        """Create a new directory.
        
        Args:
            path: Directory path to create
        """
        result = self.file_ops.create_directory(path)
        if result.get("success"):
            return f"✅ Successfully created directory: '{result['path']}'"
        else:
            return f"Error creating directory: {result.get('error', 'Unknown error')}"
    
    def create_file(self, path, content="", overwrite=False, encoding="utf-8") -> str:
        """Create a new file with content.
        
        Args:
            path: File path to create
            content: Text content for the file
            overwrite: Whether to overwrite if file exists
            encoding: File encoding (default: utf-8)
        """
        result = self.file_ops.create_file(path, content, overwrite, encoding)
        if result.get("success"):
            return f"✅ Successfully created file: '{result['path']}' ({result['size']} bytes)"
        else:
            return f"Error creating file: {result.get('error', 'Unknown error')}"
    
    # Editor Tool Wrapper
    def open_in_editor(self, folder_path=None, editor_name=None) -> str:
        """Open a folder in code editor or file explorer.
        If no folder_path is provided, lists available editors on the system.
        
        Args:
            folder_path: Path to the folder to open (or None to list editors)
            editor_name: (Optional) Preferred editor name (e.g., 'vscode', 'pycharm')
        """
        # If no folder path provided, just list available editors
        if not folder_path:
            editors = get_available_editors()
            
            if isinstance(editors, dict) and "error" in editors:
                return f"Error listing editors: {editors['error']}"
                
            if not editors:
                return "No code editors were found on this system. Folders will open in the default file explorer."
            
            output = ["Available code editors:"]
            for idx, (name, path) in enumerate(editors.items(), 1):
                output.append(f"{idx}. {name} ({path})")
            
            return "\n".join(output)
        
        # Open folder in editor
        result = open_folder_in_editor(folder_path, editor_name)
        
        if result.get("success"):
            method = result.get("method", "editor")
            path = result.get("path", folder_path)
            return f"✅ Successfully opened folder: '{path}' in {method}"
        else:
            return f"Error opening folder: {result.get('error', 'Unknown error')}"
    
    def generate_image_wrapper(self, prompt: str, save_path: str = "output.png") -> str:
        """Generate an image using AI based on the provided prompt.
        
        Args:
            prompt: Text description of the image to generate
            save_path: Optional path where to save the generated image (default: output.png)
        """
        try:
            # Set API key from settings
            api_key = self.settings.get("api_keys", "replicate_api_key")
            if not api_key:
                return "❌ Replicate API key not configured. Please set it in Settings > API Keys."
            
            import os
            os.environ['REPLICATE_API_TOKEN'] = api_key
            
            result = generate_image(prompt, save_path)
            return result
        except Exception as e:
            return f"Error generating image: {str(e)}"
    
    def set_wallpaper_wrapper(self, image_path: str) -> str:
        """Set the Windows desktop wallpaper to the specified image.
        
        Args:
            image_path: Full path to the image file to set as wallpaper
        """
        try:
            result = set_wallpaper(image_path)
            return result
        except Exception as e:
            return f"Error setting wallpaper: {str(e)}"
            
    def extract_webpage_content(self, url: str) -> str:
        """Extract and return the full content of a webpage.
        
        Args:
            url: The URL of the webpage to extract content from
            
        Returns:
            str: The extracted content or error message
        """
        if not WEBPAGE_EXTRACTION_AVAILABLE:
            return "Webpage extraction tool is not available. Please check dependencies."
            
        try:
            result = load_web_content(url)
            if result.get("success", False):
                return result["content"]
            else:
                return f"Failed to extract webpage content: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error extracting webpage content: {str(e)}"

    def close_app_by_name_wrapper(self, app_name: str, force_kill: bool = False) -> str:
        """Close applications by partial process name match"""
        if not CLOSE_APP_BY_NAME_AVAILABLE:
            return "Close app by name tool is not available. Please check dependencies."
        try:
            result = close_app_by_name(app_name, force_kill)
            return result
        except Exception as e:
            return f"Error closing application: {str(e)}"

    def list_processes_wrapper(self):
        """List all running processes"""
        try:
            if CLOSE_APP_BY_NAME_AVAILABLE:
                return list_processes()
            else:
                return "Process listing tool is not available. Required dependencies may be missing."
        except Exception as e:
            return f"Error listing processes: {str(e)}"

    def set_timer_wrapper(self, duration: str) -> str:
        """Set a timer for the specified duration using natural language.
        
        Args:
            duration: Natural language duration (e.g., "5 minutes", "30 seconds", "1 hour")
            
        Returns:
            str: Success message or error message
        """
        if not TIMER_TOOL_AVAILABLE:
            return "Timer tool is not available. Please check dependencies."
            
        try:
            result = set_timer(duration)
            # Extract message from the result dictionary
            if isinstance(result, dict):
                if result.get('success', False):
                    return result.get('message', 'Timer set successfully')
                else:
                    return result.get('message', 'Failed to set timer')
            else:
                return str(result)
        except Exception as e:
            return f"Error setting timer: {str(e)}"
    
    def describe_image_wrapper(self, image_path: str, prompt: str = "Describe this image in as much detail as possible") -> str:
        """Analyze and describe an image using AI vision.
        
        Args:
            image_path: Full path to the image file to analyze
            prompt: Custom prompt for image description (optional)
            
        Returns:
            str: Detailed description of the image or error message
        """
        if not IMAGE_DESCRIPTION_AVAILABLE:
            return "Image description tool is not available. Please install replicate: pip install replicate"
        
        try:
            # Set API key from settings
            api_key = self.settings.get("api_keys", "replicate_api_key")
            if not api_key:
                return "❌ Replicate API key not configured. Please set it in Settings > API Keys."
            
            import os
            os.environ['REPLICATE_API_TOKEN'] = api_key
            
            result = describe_image(image_path, prompt)
            return result
        except Exception as e:
            return f"Error describing image: {str(e)}"

    def is_tool_enabled(self, tool_name):
        """Check if a specific tool is enabled in settings"""
        # Map tool function names to their setting keys
        tool_to_setting = {
            "take_screenshot_wrapper": "screenshot_tool",
            "web_search_wrapper": "web_search",
            "launch_apps": "file_operations",  # App launcher uses file_operations setting
            "get_system_info": "file_operations",  # System info uses file_operations setting
            "close_apps": "file_operations",  # Close apps uses file_operations setting
            "close_app_by_name_wrapper": "file_operations",  # Close app by name uses file_operations setting
            "list_processes_wrapper": "file_operations",  # List processes uses file_operations setting
            # File operations tools all use the file_operations setting
            "list_directory": "file_operations",
            "copy_file": "file_operations",
            "move_file": "file_operations",
            "delete_file": "file_operations",
            "rename_file": "file_operations",
            "create_directory": "file_operations",
            "create_file": "file_operations",
            "open_in_editor": "file_operations",  # Editor tool uses file_operations setting
            "launch_game_wrapper": "game_launcher",
            "generate_image_wrapper": "image_generation",
            "set_wallpaper_wrapper": "image_generation", # Wallpaper uses image generation setting
            "extract_webpage_content": "web_search",  # Web extraction uses web_search setting
            "set_timer_wrapper": "timer_tool",  # Timer tool
            "describe_image_wrapper": "image_description",  # Image description tool
        }

        # Default to disabled for tools without specific settings (security first)
        if tool_name == "mcp_call":
            mcp_enabled = bool(self.settings.get("mcp", "enabled"))
            # Allow if we either discovered tools OR at least have a configured server
            available = bool(getattr(self, "mcp_tool_names", [])) or bool(getattr(self, "mcp_server_conf", None))
            print(f"Debug: MCP tool 'mcp_call' enabled={mcp_enabled and available}")
            return mcp_enabled and available
        if tool_name.startswith("mcp_"):
            # Dynamically enabled only when MCP is enabled and this wrapper was discovered
            mcp_enabled = bool(self.settings.get("mcp", "enabled"))
            discovered = tool_name in getattr(self, "mcp_wrapper_names", [])
            print(f"Debug: MCP tool '{tool_name}' enabled={mcp_enabled and discovered}")
            return mcp_enabled and discovered
        if tool_name not in tool_to_setting:
            print(f"Warning: Tool '{tool_name}' not mapped to any setting, defaulting to disabled")
            return False
            
        setting_key = tool_to_setting[tool_name]
        tool_enabled = self.settings.get("tools", setting_key)
        print(f"Debug: Tool '{tool_name}' -> setting '{setting_key}' = {tool_enabled}")
        return tool_enabled
        
    def get_enabled_tools(self):
        """Return a list of enabled tools based on settings"""
        enabled_tools = []
        print(f"Debug: Checking {len(self.tools)} total tools...")
        for tool in self.tools:
            tool_name = tool.__name__
            if self.is_tool_enabled(tool_name):
                enabled_tools.append(tool)
                print(f"Debug: Tool '{tool_name}' is ENABLED")
            else:
                print(f"Debug: Tool '{tool_name}' is DISABLED")
                
        print(f"Debug: {len(enabled_tools)} tools enabled out of {len(self.tools)} total")
        return enabled_tools

    # ====================== MCP Dynamic Integration ======================
    def try_attach_mcp_tools(self):
        """Discover and expose MCP tools as dynamic wrappers if MCP is enabled and a server is configured.
        - No hardcoding: discards wrappers when MCP is disabled or no server.
        - Safe: requires 'mcp' package present; otherwise it is a no-op.
        """
        try:
            if not MCP_AVAILABLE:
                return
            if not self.settings.get("mcp", "enabled"):
                self._detach_mcp_wrappers()
                return
            servers = self.settings.get("mcp", "servers") or []
            if not servers:
                self._detach_mcp_wrappers()
                return

            # Choose the first configured server for now.
            srv = servers[0]
            if not getattr(self, "mcp_wrapper_names", []) and not getattr(self, "mcp_tool_names", []):
                tools = self._list_mcp_tools(srv)
                if tools:
                    self._attach_mcp_wrappers(srv, tools)
                else:
                    # Listing failed or returned empty: still expose generic mcp_call so the model can use it
                    self.mcp_server_conf = srv
                    self._ensure_mcp_call_tool()
                    detail = getattr(self, "last_mcp_list_error", None)
                    if not self.mcp_announce_done:
                        msg = "ℹ️ MCP server configured. Tools could not be listed right now; you can still call tools using mcp_call(tool_name, arguments)."
                        if detail:
                            msg += f"\nReason: {detail}"
                        self.add_system_message(msg)
        except Exception as ex:
            print(f"try_attach_mcp_tools error: {ex}")
            # Surface non-fatal problems to chat once so the user understands why MCP didn't appear
            try:
                self.add_system_message(f"⚠️ MCP attach issue: {str(ex)[:200]}")
            except Exception:
                pass

    def _detach_mcp_wrappers(self):
        names = getattr(self, "mcp_wrapper_names", [])
        if not names:
            names = []
        # Remove per-tool wrappers if any
        self.tools = [t for t in self.tools if t.__name__ not in names and t.__name__ != "mcp_call"]
        for n in names:
            if hasattr(self, n):
                try:
                    delattr(self, n)
                except Exception:
                    pass
        # Remove mcp_call if present
        if hasattr(self, "mcp_call"):
            try:
                delattr(self, "mcp_call")
            except Exception:
                pass
        self.mcp_wrapper_names = []
        self.mcp_tool_names = []
        self.mcp_server_conf = None

    def _normalize_wrapper_name(self, raw: str) -> str:
        safe = []
        for ch in raw:
            if ch.isalnum():
                safe.append(ch)
            else:
                safe.append("_")
        # Collapse multiple underscores
        name = "".join(safe)
        while "__" in name:
            name = name.replace("__", "_")
        return f"mcp_{name.strip('_').lower()}"

    def _attach_mcp_wrappers(self, srv: dict, tools_result) -> None:
        """Create per-tool wrappers and also expose a generic mcp_call(tool_name, arguments)."""
        tool_list = getattr(tools_result, "tools", None) or tools_result
        discovered_names = []
        wrapper_names = []
        for tool in tool_list:
            tname = getattr(tool, "name", None) or (tool.get("name") if isinstance(tool, dict) else None)
            if not tname:
                continue
            discovered_names.append(tname)
            wrapper = self._normalize_wrapper_name(tname)
            if any(getattr(fn, "__name__", "") == wrapper for fn in self.tools):
                wrapper_names.append(wrapper)
                continue
            # Build per-tool wrapper with explicit signature from schema
            try:
                fn = self._build_mcp_wrapper(srv, tool)
                bound = pytypes.MethodType(fn, self)
                setattr(self, wrapper, bound)
                self.tools.append(getattr(self, wrapper))
                wrapper_names.append(wrapper)
            except Exception as ex:
                print(f"Failed to build typed wrapper for MCP tool '{tname}': {ex}. Falling back to kwargs.")
                def _fallback(self, **kwargs):
                    return self._call_mcp_tool_once(srv, tname, kwargs)
                _fallback.__name__ = wrapper
                _fallback.__doc__ = f"Dynamic MCP tool wrapper for '{tname}' (fallback kwargs)."
                setattr(self, wrapper, pytypes.MethodType(_fallback, self))
                self.tools.append(getattr(self, wrapper))
                wrapper_names.append(wrapper)

        # Save discovery
        self.mcp_tool_names = discovered_names
        self.mcp_wrapper_names = wrapper_names
        self.mcp_server_conf = srv
        # Ensure generic call tool exists as well
        self._ensure_mcp_call_tool()
        self._announce_mcp_tools()

    def _build_mcp_wrapper(self, srv: dict, tool_obj):
        """Create a Python function object with explicit parameters derived from the tool's inputSchema.
        Returns the function object (unbound). The function name is normalized to mcp_<tool>.
        """
        tname = getattr(tool_obj, "name", None) or (tool_obj.get("name") if isinstance(tool_obj, dict) else None)
        if not tname:
            raise ValueError("tool name missing")
        wrapper_name = self._normalize_wrapper_name(tname)

        # Get schema and description
        schema = getattr(tool_obj, "inputSchema", None)
        if schema is not None and hasattr(schema, "model_dump"):
            schema = schema.model_dump()
        desc = getattr(tool_obj, "description", None) or (tool_obj.get("description") if isinstance(tool_obj, dict) else "")
        schema = schema or {}

        # Build parameter list from schema
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = schema.get("required", []) if isinstance(schema, dict) else []
        # Map JSON schema types to Python annotations
        def py_type(json_t):
            return {
                "string": "str",
                "number": "float",
                "integer": "int",
                "boolean": "bool",
                "array": "list",
                "object": "dict",
            }.get(json_t, "object")

        # Order required first, then optional
        req_params = []
        opt_params = []
        for key, spec in props.items():
            ann = py_type(spec.get("type")) if isinstance(spec, dict) else "object"
            if key in required:
                req_params.append(f"{key}: {ann}")
            else:
                opt_params.append(f"{key}: {ann} | None = None")
        param_names = list(props.keys())
        # Build source
        if req_params or opt_params:
            param_sig = ", ".join(req_params + opt_params + ["__server_conf=server_conf"])  # default binds
            args_build = ", ".join([f"'{k}': {k}" for k in param_names])
        else:
            param_sig = "__server_conf=server_conf"
            args_build = ""

        import json as _json
        schema_txt = _json.dumps(schema, indent=2) if isinstance(schema, dict) else str(schema)
        doc = f"""MCP tool '{tname}'. {desc}\nInput schema:\n{schema_txt}\n"""
        # Escape sequences that could break embedded triple quotes
        doc_escaped = doc.replace('"""', '\\"""').replace("'''", "\\'\\'\\'")

        # Build function source using triple-single-quoted outer string to avoid conflicts
        src = f'''
def {wrapper_name}(self, {param_sig}) -> str:
    """{doc_escaped}"""
    args = {{{args_build}}} if {bool(param_names)} else {{}}
    return self._call_mcp_tool_once(__server_conf, {tname!r}, args)
'''
        code_globals = {
            "server_conf": srv,
        }
        code_locals = {}
        exec(src, code_globals, code_locals)
        fn = code_locals[wrapper_name]
        return fn

    def _ensure_mcp_call_tool(self):
        """Create or update the generic MCP call tool exposed to the LLM."""
        # Define implementation
        def _mcp_call(self, tool_name: str, arguments: dict | None = None) -> str:
            # Allow calls even if discovery failed; server will return an error if the tool is unknown
            if not self.mcp_server_conf:
                return "MCP server configuration missing."
            return self._call_mcp_tool_once(self.mcp_server_conf, tool_name, arguments or {})

        # Bind or update
        _mcp_call.__name__ = "mcp_call"
        _mcp_call.__doc__ = (
            "Call a tool on the configured MCP server.\n"
            + (f"Available tool_name values: {', '.join(self.mcp_tool_names)}.\n" if self.mcp_tool_names else "")
            + "arguments: object with fields accepted by the server's tool input schema."
        )
        bound = pytypes.MethodType(_mcp_call, self)
        setattr(self, "mcp_call", bound)
        # Ensure the tools registry references the fresh bound method
        self.tools = [t for t in self.tools if getattr(t, "__name__", "") != "mcp_call"]
        self.tools.append(getattr(self, "mcp_call"))

    def _announce_mcp_tools(self):
        """Add a system message announcing discovered MCP tools (once per session)."""
        try:
            if self.mcp_announce_done:
                return
            if not self.mcp_tool_names:
                return
            wrappers = ", ".join(self.mcp_wrapper_names) if getattr(self, "mcp_wrapper_names", []) else "(wrappers pending)"
            tools = ", ".join(self.mcp_tool_names)
            msg = (
                "🔌 MCP server connected.\n"
                f"Discovered tools: {tools}.\n"
                f"Wrapper functions available: {wrappers}.\n"
                "Use either the specific wrapper, e.g., mcp_echo(text='hello'), or the generic mcp_call(tool_name='echo', arguments={ 'text': 'hello' })."
            )
            self.add_system_message(msg)
            self.mcp_announce_done = True
        except Exception as ex:
            print(f"announce MCP tools failed: {ex}")

    def _run_async(self, coro, timeout: float):
        """Run an async coroutine to completion even if a loop is already running.
        Falls back to a dedicated event loop thread if asyncio.run() is not allowed.
        """
        try:
            return asyncio.run(asyncio.wait_for(coro, timeout=timeout))
        except RuntimeError as ex:
            # Likely: "asyncio.run() cannot be called from a running event loop"
            if "asyncio.run()" in str(ex):
                box = {}
                def runner():
                    # On Windows, use SelectorEventLoop in the background thread so stdio pipes work.
                    try:
                        if sys.platform == "win32":
                            loop = asyncio.SelectorEventLoop()
                        else:
                            loop = asyncio.new_event_loop()
                    except Exception:
                        loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        box["value"] = loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass
                th = threading.Thread(target=runner, daemon=True)
                th.start(); th.join()
                return box.get("value")
            raise

    def _list_mcp_tools(self, srv: dict):
        """Return list of tools from the MCP server using a short-lived connection."""
        if not MCP_AVAILABLE:
            return []
        try:
            if (srv.get("type") or ("STDIO" if srv.get("command") else "HTTP")).upper() == "HTTP":
                # Normalize and derive /mcp from either base or /healthz
                base = (srv.get("url") or "").strip()
                norm = base.rstrip("/")
                if norm.endswith("/healthz"):
                    api = norm[: -len("/healthz")] + "/mcp"
                else:
                    api = norm + "/mcp"
                async def task():
                    async with streamablehttp_client(api, terminate_on_close=True) as (read, write, get_session_id):
                        session = ClientSession(read, write)
                        await session.initialize()
                        return await session.list_tools()
                return self._run_async(task(), timeout=20)
            else:
                cmd = srv.get("command")
                args = srv.get("args") or []
                # Auto-repair path tokens if necessary
                try:
                    args = self._repair_stdio_args(args)
                except Exception:
                    pass
                # Harden launch: add '-u' for python and '--mode stdio' if invoking a script and flag not present
                try:
                    base = os.path.basename(cmd or "").lower()
                except Exception:
                    base = ""
                final_args = list(args)
                try:
                    if base.startswith("python"):
                        # Ensure unbuffered
                        if not final_args or final_args[0] != "-u":
                            final_args = ["-u"] + final_args
                    # Ensure stdio mode if a .py script is present and no --mode provided
                    has_mode = any(a == "--mode" or a.startswith("--mode=") for a in final_args)
                    has_py = any(str(a).lower().endswith(".py") for a in final_args)
                    if has_py and not has_mode:
                        final_args += ["--mode", "stdio"]
                except Exception:
                    pass
                async def task():
                    import tempfile, os
                    # Use base env + overrides to avoid losing required Windows vars like SYSTEMROOT
                    env = os.environ.copy()
                    env.update({"PYTHONUNBUFFERED": "1", "DUMMY_MCP_LOG_LEVEL": "DEBUG", "PYTHONIOENCODING": "utf-8"})
                    # Capture server stderr as well for diagnosis
                    err_f = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False)
                    try:
                        # Derive cwd from script path if present
                        cwd = None
                        for tok in final_args:
                            if isinstance(tok, str) and tok.lower().endswith('.py') and os.path.isabs(tok) and os.path.exists(tok):
                                cwd = os.path.dirname(tok)
                                break
                        params = StdioServerParameters(command=cmd, args=list(final_args), env=env, cwd=cwd)
                        async with stdio_client(params, errlog=err_f) as (read, write):
                            session = ClientSession(read, write)
                            await session.initialize()
                            return await session.list_tools()
                    finally:
                        try:
                            err_f.flush(); err_f.close()
                        except Exception:
                            pass
                return self._run_async(task(), timeout=25)
        except Exception as ex:
            # Expand nested exception group details if present
            err = str(ex)
            try:
                if hasattr(ex, 'exceptions') and isinstance(getattr(ex, 'exceptions'), (list, tuple)):
                    eg_details = "".join([f"\n  [{i+1}] {type(s).__name__}: {s}" for i, s in enumerate(ex.exceptions)])
                    if eg_details:
                        err = f"{err}{eg_details}"
            except Exception:
                pass
            print(f"List MCP tools failed: {err}")
            try:
                self.last_mcp_list_error = err
            except Exception:
                pass
            return []

    def _call_mcp_tool_once(self, srv: dict, tool_name: str, arguments: dict) -> str:
        """Call a single MCP tool once and return a human-readable string.
        Opens a new short-lived connection each time for safety.
        """
        if not MCP_AVAILABLE:
            return "MCP client is not installed."
        try:
            def format_result(res):
                try:
                    # Prefer structured/text content
                    blocks = getattr(res, "content", None)
                    if blocks:
                        parts = []
                        for b in blocks:
                            # Support dict-like or pydantic object
                            t = getattr(b, "type", None) or b.get("type") if isinstance(b, dict) else None
                            if t == "text":
                                txt = getattr(b, "text", None) or b.get("text")
                                if txt:
                                    parts.append(txt)
                        if parts:
                            return "\n".join(parts)
                    # Fallback
                    return str(res)
                except Exception:
                    return str(res)

            if (srv.get("type") or ("STDIO" if srv.get("command") else "HTTP")).upper() == "HTTP":
                # Normalize URL and derive /mcp endpoint
                base = (srv.get("url") or "").strip()
                norm = base.rstrip("/")
                if norm.endswith("/healthz"):
                    api = norm[: -len("/healthz")] + "/mcp"
                else:
                    api = norm + "/mcp"
                async def task():
                    async with streamablehttp_client(api, terminate_on_close=True) as (read, write, get_session_id):
                        session = ClientSession(read, write)
                        await session.initialize()
                        res = await session.call_tool(tool_name, arguments or {})
                        return format_result(res)
                try:
                    return self._run_async(task(), timeout=30)
                except Exception as ex:
                    return f"MCP HTTP call failed (endpoint={api}, tool={tool_name}): {repr(ex)}"
            else:
                cmd = srv.get("command")
                args = srv.get("args") or []
                async def task():
                    params = StdioServerParameters(command=cmd, args=list(args))
                    async with stdio_client(params) as (read, write):
                        session = ClientSession(read, write)
                        await session.initialize()
                        res = await session.call_tool(tool_name, arguments or {})
                        return format_result(res)
                try:
                    return self._run_async(task(), timeout=30)
                except Exception as ex:
                    return f"MCP STDIO call failed (cmd={cmd} {args}, tool={tool_name}): {repr(ex)}"
        except Exception as ex:
            return f"MCP error calling '{tool_name}': {str(ex)}"
        
    def create_temp_directory(self) -> str:
        """Create a temporary directory for file uploads"""
        if self.temp_dir is None:
            # Create a temp directory in the system temp folder
            self.temp_dir = Path(tempfile.mkdtemp(prefix="ollama_agent_uploads_"))
            print(f"✅ Created temporary directory: {self.temp_dir}")
            self.add_system_message(f"📁 Created temporary directory for file uploads")
        return str(self.temp_dir)
        
    def handle_file_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker result and upload files"""
        if e.files:
            # Ensure temp directory exists
            temp_dir = self.create_temp_directory()
            
            uploaded_count = 0
            for file in e.files:
                try:
                    # Copy file to temp directory
                    source_path = file.path
                    dest_path = Path(temp_dir) / file.name
                    
                    # Copy the file
                    shutil.copy2(source_path, dest_path)
                    
                    # Process document content if it's a supported format
                    content_result = None
                    if DOCUMENT_LOADER_AVAILABLE and is_supported_document(str(dest_path)):
                        print(f"📄 Processing {get_document_type(str(dest_path))}: {file.name}")
                        content_result = load_document_content(str(dest_path))
                        
                        if content_result['success']:
                            print(f"✅ Extracted {len(content_result['content']):,} characters from {file.name}")
                        else:
                            print(f"⚠️ Could not extract content from {file.name}: {content_result['error']}")
                    
                    # Add to uploaded files list with content
                    file_info = {
                        'name': file.name,
                        'size': file.size,
                        'path': str(dest_path),
                        'original_path': source_path,
                        'content': content_result['content'] if content_result and content_result['success'] else None,
                        'content_preview': content_result['content_preview'] if content_result and content_result['success'] else None,
                        'document_type': get_document_type(str(dest_path)) if DOCUMENT_LOADER_AVAILABLE else 'Unknown',
                        'is_document': is_supported_document(str(dest_path)) if DOCUMENT_LOADER_AVAILABLE else False,
                        'processing_error': content_result['error'] if content_result and not content_result['success'] else None
                    }
                    self.uploaded_files.append(file_info)
                    uploaded_count += 1
                    
                    print(f"✅ Uploaded: {file.name} ({file.size} bytes) -> {dest_path}")
                    
                except Exception as ex:
                    print(f"❌ Error uploading {file.name}: {ex}")
                    self.add_system_message(f"❌ Failed to upload {file.name}: {str(ex)}")
                    
            if uploaded_count > 0:
                total_size = sum(f['size'] for f in self.uploaded_files)
                total_mb = total_size / (1024 * 1024)
                
                # Count processed documents
                processed_docs = sum(1 for f in self.uploaded_files if f.get('content') is not None)
                
                message = f"📎 Uploaded {uploaded_count} file(s) successfully!\n" + \
                         f"📊 Total files: {len(self.uploaded_files)} ({total_mb:.2f} MB)"
                
                if processed_docs > 0:
                    message += f"\n📄 Processed {processed_docs} document(s) for content extraction"
                    
                self.add_system_message(message)
                # Update the UI display and save state
                self.update_uploaded_files_display()
                self.save_file_queue_state()
                
    def open_file_picker(self, e):
        """Open file picker for file upload"""
        self.file_picker.pick_files(
            dialog_title="Select files to upload",
            allow_multiple=True
        )
        
    def clear_uploaded_files(self):
        """Clear all uploaded files and cleanup temp directory"""
        try:
            # Remove all files from temp directory
            for file_info in self.uploaded_files:
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
                    
            # Clear the list
            self.uploaded_files.clear()
            
            # Remove temp directory if empty
            if self.temp_dir and self.temp_dir.exists():
                try:
                    self.temp_dir.rmdir()  # Only removes if empty
                    print(f"✅ Removed temporary directory: {self.temp_dir}")
                    self.temp_dir = None
                    self.add_system_message("🧹 Cleared all uploaded files and cleaned up temporary directory")
                except OSError:
                    print("⚠️ Temporary directory not empty, keeping it")
                    
        except Exception as ex:
            print(f"❌ Error clearing files: {ex}")
            self.add_system_message(f"❌ Error clearing files: {str(ex)}")
            
    def update_uploaded_files_display(self):
        """Update the file queue display UI with compact chips"""
        if not self.uploaded_files:
            # Hide the file queue if no files
            self.file_queue_row.visible = False
        else:
            # Show the file queue and populate with file chips
            self.file_queue_row.visible = True
            
            # Get current theme colors
            colors = self.settings.get_theme_colors()
            
            # Clear existing file chips (keep icon and label)
            file_row = self.file_queue_row.content
            # Keep only the first 2 items (icon and "Files ready to send:" text)
            file_row.controls = file_row.controls[:2]
            
            # Add file chips
            for file_info in self.uploaded_files:
                file_size_mb = file_info['size'] / (1024 * 1024)
                
                # Determine file icon based on document type
                icon_color = colors["text_primary"]
                tooltip_text = f"{file_info['name']} ({file_size_mb:.1f}MB)"
                
                # Determine file icon and color based on document status
                if file_info.get('is_document', False):
                    # Choose icon based on document type
                    if 'pdf' in file_info.get('document_type', '').lower():
                        file_icon = ft.Icons.PICTURE_AS_PDF
                    elif 'word' in file_info.get('document_type', '').lower():
                        file_icon = ft.Icons.DESCRIPTION
                    elif 'text' in file_info.get('document_type', '').lower():
                        file_icon = ft.Icons.TEXT_SNIPPET
                    elif 'excel' in file_info.get('document_type', '').lower() or 'csv' in file_info.get('document_type', '').lower():
                        file_icon = ft.Icons.TABLE_CHART
                    else:
                        file_icon = ft.Icons.DOCUMENT_SCANNER
                    
                    # Determine status indicator
                    if file_info.get('content') is not None:
                        # Successfully extracted content
                        status_icon = ft.Icons.CHECK_CIRCLE
                        status_color = "#4CAF50"  # Green
                        chars_count = len(file_info.get('content', ''))
                        tooltip_text += f"\n✅ {file_info['document_type']}: {chars_count:,} characters extracted"
                        if file_info.get('content_preview'):
                            tooltip_text += f"\n\nPreview: {file_info['content_preview']}"
                    elif file_info.get('processing_error'):
                        # Processing error
                        status_icon = ft.Icons.ERROR
                        status_color = "#F44336"  # Red
                        tooltip_text += f"\n❌ Error: {file_info['processing_error']}"
                    else:
                        # Unknown state
                        status_icon = ft.Icons.HELP
                        status_color = "#FFC107"  # Amber
                        tooltip_text += "\n⚠️ Document not processed"
                else:
                    # Not a supported document
                    file_icon = ft.Icons.INSERT_DRIVE_FILE
                    status_icon = None
                    status_color = None
                
                # Create row content with icon, text, and optional status indicator
                row_content = [
                    ft.Icon(
                        file_icon,
                        size=14,
                        color=icon_color
                    ),
                    ft.Text(
                        f"{file_info['name']} ({file_size_mb:.1f}MB)",
                        size=11,
                        color=colors["text_primary"],
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )
                ]
                
                # Add status indicator if applicable
                if status_icon:
                    row_content.append(
                        ft.Icon(
                            status_icon,
                            size=12,
                            color=status_color
                        )
                    )
                
                # Add close button
                row_content.append(
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=12,
                        icon_color=colors["text_secondary"],
                        tooltip=f"Remove {file_info['name']}",
                        on_click=lambda event_param, f=file_info: self.remove_uploaded_file(f),
                        style=ft.ButtonStyle(
                            padding=ft.padding.all(2)
                        )
                    )
                )
                
                # Create compact file chip
                file_chip = ft.Container(
                    content=ft.Row(row_content, spacing=4, tight=True),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=colors["bg_tertiary"],
                    border=ft.border.all(1, colors["border"]),
                    border_radius=15,
                    margin=ft.margin.only(right=6),
                    tooltip=tooltip_text
                )
                
                file_row.controls.append(file_chip)
            
            # Add clear all button at the end
            clear_all_chip = ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.CLEAR_ALL,
                        size=12,
                        color=colors["text_secondary"]
                    ),
                    ft.Text(
                        "Clear all",
                        size=11,
                        color=colors["text_secondary"]
                    )
                ], spacing=4, tight=True),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                bgcolor=colors["bg_primary"],
                border=ft.border.all(1, colors["border"]),
                border_radius=15,
                margin=ft.margin.only(left=6),
                on_click=lambda event_param: self.clear_all_uploaded_files(),
                tooltip="Clear all files"
            )
            
            file_row.controls.append(clear_all_chip)
                
        self.page.update()
        
    def remove_uploaded_file(self, file_info: dict):
        """Remove a specific uploaded file"""
        try:
            # Remove from filesystem
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
                print(f"✅ Removed file: {file_info['name']}")
                
            # Remove from uploaded files list
            self.uploaded_files = [f for f in self.uploaded_files if f['path'] != file_info['path']]
            
            # Update the display and save state
            self.update_uploaded_files_display()
            self.save_file_queue_state()
            
            # Show confirmation message
            self.add_system_message(f"🗑️ Removed file: {file_info['name']}")
            
        except Exception as ex:
            print(f"❌ Error removing file: {ex}")
            self.add_system_message(f"❌ Error removing file: {str(ex)}")
            
    def clear_all_uploaded_files(self):
        """Clear all uploaded files (called from UI button)"""
        if self.uploaded_files:
            self.clear_uploaded_files()
            self.update_uploaded_files_display()
            self.save_file_queue_state()
            
    def save_file_queue_state(self):
        """Save the current file queue state to settings for persistence"""
        try:
            # Save uploaded files info and temp directory path
            file_queue_data = {
                'temp_dir': str(self.temp_dir) if self.temp_dir else None,
                'uploaded_files': self.uploaded_files.copy()
            }
            
            # Save to settings under a special key
            self.settings.set('file_queue', 'data', file_queue_data)
            print(f"✅ Saved file queue state: {len(self.uploaded_files)} files")
            
        except Exception as ex:
            print(f"❌ Error saving file queue state: {ex}")
            
    def load_file_queue_state(self):
        """Load the file queue state from settings to restore persistence"""
        try:
            # Load file queue data from settings
            file_queue_data = self.settings.get('file_queue', 'data')
            
            if file_queue_data and isinstance(file_queue_data, dict):
                # Restore temp directory path
                if file_queue_data.get('temp_dir'):
                    temp_dir_path = Path(file_queue_data['temp_dir'])
                    if temp_dir_path.exists():
                        self.temp_dir = temp_dir_path
                        print(f"✅ Restored temp directory: {self.temp_dir}")
                    else:
                        print(f"⚠️ Temp directory no longer exists: {temp_dir_path}")
                        # Clear the saved state since temp dir is gone
                        self.settings.set('file_queue', 'data', {})
                        return
                        
                # Restore uploaded files list, but verify files still exist
                uploaded_files = file_queue_data.get('uploaded_files', [])
                valid_files = []
                
                for file_info in uploaded_files:
                    if isinstance(file_info, dict) and 'path' in file_info:
                        if os.path.exists(file_info['path']):
                            valid_files.append(file_info)
                        else:
                            print(f"⚠️ File no longer exists: {file_info.get('name', 'unknown')}")
                            
                self.uploaded_files = valid_files
                
                if valid_files:
                    print(f"✅ Restored {len(valid_files)} uploaded files")
                    # Update display after UI is created
                    if hasattr(self, 'page'):
                        self.page.run_task(self.delayed_file_queue_update)
                else:
                    # No valid files, clear the saved state
                    self.settings.set('file_queue', 'data', {})
                    
        except Exception as ex:
            print(f"❌ Error loading file queue state: {ex}")
            # Clear invalid state
            self.settings.set('file_queue', 'data', {})
            
    async def delayed_file_queue_update(self):
        """Update file queue display after a short delay to ensure UI is ready"""
        import asyncio
        await asyncio.sleep(0.1)  # Small delay to ensure UI is fully initialized
        self.update_uploaded_files_display()
        
    def restore_file_queue_on_navigation(self):
        """Restore file queue display when navigating back to chat"""
        if self.current_page == "chat" and self.uploaded_files:
            self.delayed_file_queue_update()
    
    def on_audio_state_changed(self, e):
        """Handle audio recorder state changes"""
        if e.data == "recording":
            self.is_recording = True
            # Update mic button to show recording state
            self.mic_button.content.icon = ft.Icons.STOP_ROUNDED
            self.mic_button.content.icon_color = "#ff4444"
            self.mic_button.content.bgcolor = "#4a2a2a"
            self.mic_button.content.tooltip = "Stop recording"
            self.update_status("🔴 Recording audio...", "#ff4444")
        elif e.data == "stopped":
            self.is_recording = False
            # Reset mic button to normal state
            self.mic_button.content.icon = ft.Icons.MIC_ROUNDED
            self.mic_button.content.icon_color = "#888888"
            self.mic_button.content.bgcolor = "#2a2a2a"
            self.mic_button.content.tooltip = "Record voice message"
            if self.current_recording_path:
                self.update_status(f"✅ Audio recorded, transcribing...", "#00d4ff")
                # Start transcription in a separate thread
                threading.Thread(target=self.transcribe_and_update_input, daemon=True).start()
            else:
                self.update_status("🟢 Ready", "#00ff88")
        self.page.update()
    
    def toggle_recording(self, e):
        """Toggle audio recording on/off"""
        if not self.voice_supported or not self.audio_recorder:
            self.update_status("🎙️ Voice recording is not available in this build", "#ffaa00")
            self.page.update()
            return
        if not self.is_recording:
            # Start recording
            self.start_audio_recording()
        else:
            # Stop recording
            self.stop_audio_recording()
    
    def start_audio_recording(self):
        """Start audio recording and save to temp folder"""
        try:
            if not self.voice_supported or not self.audio_recorder:
                raise RuntimeError("AudioRecorder not available")
            # Create temp directory if it doesn't exist
            if not self.temp_dir:
                self.create_temp_directory()
            
            # Generate unique filename for recording
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_recording_path = os.path.join(self.temp_dir, f"voice_recording_{timestamp}.wav")
            
            # Start recording with output path
            self.audio_recorder.start_recording(output_path=self.current_recording_path)
            
        except Exception as e:
            self.update_status(f"❌ Error starting recording: {str(e)}", "#ff4444")
            self.page.update()
    
    def stop_audio_recording(self):
        """Stop audio recording"""
        try:
            if not self.voice_supported or not self.audio_recorder:
                raise RuntimeError("AudioRecorder not available")
            self.audio_recorder.stop_recording()
        except Exception as e:
            self.update_status(f"❌ Error stopping recording: {str(e)}", "#ff4444")
            self.is_recording = False
            # Reset mic button state
            self.mic_button.content.icon = ft.Icons.MIC_ROUNDED
            self.mic_button.content.icon_color = "#888888"
            self.mic_button.content.bgcolor = "#2a2a2a"
            self.mic_button.content.tooltip = "Record voice message"
            self.page.update()
    
    def transcribe_and_update_input(self):
        """Transcribe the recorded audio and update the input field"""
        if not self.current_recording_path or not WHISPER_AVAILABLE:
            if not WHISPER_AVAILABLE:
                self.update_status("❌ Whisper not available for transcription", "#ff4444")
            else:
                self.update_status("❌ No recording to transcribe", "#ff4444")
            return
        
        try:
            # Check if the recording file exists
            if not os.path.exists(self.current_recording_path):
                self.update_status("❌ Recording file not found", "#ff4444")
                return
            
            # Load Whisper model (base model for good balance of speed/accuracy)
            self.update_status("🔄 Loading Whisper model...", "#00d4ff")
            model = whisper.load_model("base")
            
            # Transcribe the audio
            self.update_status("🎤 Transcribing audio...", "#00d4ff")
            result = model.transcribe(self.current_recording_path)
            transcript = result["text"].strip()
            
            if transcript:
                # Update the input field with the transcribed text
                self.input_field.value = transcript
                self.update_status(f"✅ Voice transcribed: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}'", "#00ff88")
                
                # Focus the input field so user can see the transcribed text
                self.input_field.focus()
            else:
                self.update_status("⚠️ No speech detected in recording", "#ffaa00")
            
            # Clean up the recording file
            try:
                os.remove(self.current_recording_path)
            except:
                pass  # Ignore cleanup errors
            
            self.current_recording_path = None
            self.page.update()
            
        except Exception as e:
            self.update_status(f"❌ Transcription error: {str(e)}", "#ff4444")
            self.page.update()

def main(page: ft.Page):
    """Main entry point for the Flet app"""
    OllamaAgentGUI(page)


if __name__ == "__main__":
    ft.app(target=main)
