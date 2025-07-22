#!/usr/bin/env python
"""
Flet GUI for Local Ollama Agent
Beautiful graphical interface for the console-based agent
"""

import sys
import os
import threading
import time
from typing import List, Dict, Any
import flet as ft
import json
import threading
import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path
from ollama import chat, ChatResponse
import datetime
import platform
from settings import SettingsManager

# Add parent directory to path to import agent tools
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
                     self.set_timer_wrapper]
        self.setup_page()
        self.setup_system_message()
        self.create_ui()
        
    def setup_page(self):
        """Configure the main page settings"""
        self.page.title = "🤖 Local Ollama Agent"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 900
        self.page.window_min_height = 700
        self.page.window_title_bar_hidden = False
        self.page.window_title_bar_buttons_hidden = False
        
    def setup_system_message(self):
        """Initialize the system message (same as console agent)"""
        system_msg = (
            "You are an AI agent on Windows. You achieve goals by invoking under the hood, built in tools. " +
            
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
            "20. set_timer_wrapper(duration): Set a timer using natural language (e.g., '5 minutes', '30 seconds', '1 hour')\n\n" +

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
                        ft.Text("🤖 Local Ollama Agent", size=20, weight=ft.FontWeight.BOLD, color=colors["text_primary"])
                    ], spacing=10),
                    padding=ft.padding.only(left=20)
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Row([
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
        
        # Microphone button (placeholder for future audio-to-text functionality)
        self.mic_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.MIC_ROUNDED,
                on_click=lambda e: None,  # Placeholder, no functionality yet
                icon_color="#888888",
                bgcolor="#2a2a2a",
                style=ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    overlay_color="#444444"
                ),
                tooltip="Voice input (coming soon)"
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
                    "Powered by Ollama + Flet",
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
            "🚀 Welcome to Local Ollama Agent!\n\n" +
            "I'm your AI assistant with powerful local capabilities:\n\n" +
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
                                on_change=lambda e: self.on_tool_toggle("screenshot_tool", e.control.value)
                            ),
                            ft.Text("Screenshot Tool", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "web_search"),
                                active_color="#00d4ff",
                                on_change=lambda e: self.on_tool_toggle("web_search", e.control.value)
                            ),
                            ft.Text("Web Search", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "file_operations"),
                                active_color="#00d4ff",
                                on_change=lambda e: self.on_tool_toggle("file_operations", e.control.value)
                            ),
                            ft.Text("File Operations", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "game_launcher"),
                                active_color="#00d4ff",
                                on_change=lambda e: self.on_tool_toggle("game_launcher", e.control.value)
                            ),
                            ft.Text("Game Launcher", color=colors["text_primary"], size=14)
                        ]),
                        ft.Row([
                            ft.Checkbox(
                                value=self.settings.get("tools", "image_generation"),
                                active_color="#00d4ff",
                                on_change=lambda e: self.on_tool_toggle("image_generation", e.control.value)
                            ),
                            ft.Text("Image Generation", color=colors["text_primary"], size=14)
                        ])
                    ]),
                    padding=ft.padding.all(20),
                    margin=ft.margin.all(10),
                    bgcolor=colors["bg_secondary"],
                    border_radius=10,
                    border=ft.border.all(1, colors["border"])
                ),
                
                # About Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("ℹ️ About", size=18, weight=ft.FontWeight.W_500, color=colors["accent"]),
                        ft.Divider(color=colors["border"], height=1),
                        ft.Text("Local Ollama Agent v1.0", color=colors["text_primary"], size=14),
                        ft.Text("AI-powered desktop assistant", color=colors["text_secondary"], size=12),
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
        """Add an agent response to the chat"""
        colors = self.settings.get_theme_colors()
        agent_msg = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SMART_TOY, size=16, color=colors["accent"]),
                            ft.Text("Agent", size=13, weight=ft.FontWeight.W_600, color=colors["accent"])
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
            on_click=lambda e: self.dismiss_dialog()
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
                                    on_click=lambda e: self.dismiss_dialog(),
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
            
            # Get available tools based on settings
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
                tool_functions = [tool.__name__ for tool in available_tools]
                if fn_name in tool_functions:
                    try:
                        result = getattr(self, fn_name)(**args)
                        self.add_tool_message(fn_name, result)
                        self.messages.append({
                            "role": "tool",
                            "name": fn_name,
                            "content": result
                        })
                    except Exception as tool_error:
                        error_msg = f"Error executing {fn_name}: {str(tool_error)}"
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
        
    # Tool wrapper methods (same as console agent)
    def run_shell_commands(self, command: str) -> str:
        """Run a Windows shell command; return stdout or stderr."""
        return shell(command)

    def launch_apps(self, app_name: str) -> str:
        """Launch an application by name."""
        return launch_app(app_name)

    def take_screenshot_wrapper(self, window_title: str = None) -> str:
        """Take a screenshot and save it to Desktop/Screenshots folder."""
        return take_screenshot(window_title=window_title)

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
        }
        
        # Default to disabled for tools without specific settings (security first)
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
                        on_click=lambda e, f=file_info: self.remove_uploaded_file(f),
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
                on_click=lambda e: self.clear_all_uploaded_files(),
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
        if self.uploaded_files:
            print(f"✅ Restoring file queue display with {len(self.uploaded_files)} files")
            self.update_uploaded_files_display()


def main(page: ft.Page):
    """Main entry point for the Flet app"""
    OllamaAgentGUI(page)


if __name__ == "__main__":
    ft.app(target=main)
