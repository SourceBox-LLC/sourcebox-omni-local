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
                     self.list_processes_wrapper]
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
            "19. list_processes_wrapper(): List all running processes on the system\n\n" +

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
        # Get current theme colors
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
        
        input_area = ft.Container(
            content=ft.Row([
                self.input_field,
                self.send_button
            ], spacing=15),
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
            self.input_area,
            self.status_area
        ])
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
            
            # Add user message to conversation history
            self.messages.append({"role": "user", "content": user_input})
            
            # Get response from Ollama with tools
            current_model = self.settings.get("ai_model", "model")
            response: ChatResponse = chat(
                model=current_model,
                messages=self.messages,
                tools=self.tools,
                stream=False
            )
            
            # Execute any requested tool calls
            for call in response.message.tool_calls or []:
                fn_name = call.function.name
                args = call.function.arguments or {}
                
                self.update_status(f"⚙️ Executing: {fn_name}...", "#00d4ff")
                
                # Execute the tool
                tool_functions = [tool.__name__ for tool in self.tools]
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
                    model="qwen3", #llama3.1
                    messages=self.messages
                )
                final_response = final.message.content
            else:
                final_response = response.message.content
                
            # Add agent response to chat
            self.add_agent_message(final_response)
            self.messages.append({"role": "assistant", "content": final_response})
            
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

    def list_processes_wrapper(self) -> str:
        """List all running processes"""
        if not CLOSE_APP_BY_NAME_AVAILABLE:
            return "Process listing tool is not available. Please check dependencies."
        try:
            result = list_processes()
            return result
        except Exception as e:
            return f"Error listing processes: {str(e)}"


def main(page: ft.Page):
    """Main entry point for the Flet app"""
    OllamaAgentGUI(page)


if __name__ == "__main__":
    ft.app(target=main)
