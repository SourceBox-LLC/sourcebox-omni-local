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

# Add parent directory to path to import agent tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import tools from agent_tools package (same as console agent)
# Handle missing dependencies gracefully
try:
    from agent_tools.shell_tool import shell
except ImportError as e:
    def shell(command):
        return f"Error: Shell tool unavailable - {str(e)}"

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


class OllamaAgentGUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.messages = []
        # Initialize file operations tool
        self.file_ops = FileOperationsTool()
        self.tools = [self.launch_apps, self.take_screenshot_wrapper, 
                     self.web_search_wrapper, self.get_system_info, self.close_apps, 
                     self.launch_game_wrapper, 
                     # File operations tools
                     self.list_directory, self.copy_file, self.move_file, 
                     self.delete_file, self.rename_file, self.create_directory, 
                     self.create_file,
                     # Editor tool
                     self.open_in_editor]
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
        self.page.bgcolor = "#0a0a0a"
        self.page.window_title_bar_hidden = False
        self.page.window_title_bar_buttons_hidden = False
        
    def setup_system_message(self):
        """Initialize the system message (same as console agent)"""
        system_msg = (
            "You are an AI agent on Windows. You can ONLY perform actions by calling the exact Python functions " +
            "provided to you as tools. DO NOT HALLUCINATE OR INVENT tool calls or parameters that don't exist.\n\n" +
            
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
            "14. open_in_editor(folder_path=None, editor_name=None): Open a folder in code editor or file explorer (if no path provided, lists available editors)\n\n" +

            "IMPORTANT NOTE: the launch_apps tool and launch_game_wrapper tool are different.\n" +
            "the launch_app tool is for applications (steam, discord, spotify, etc) while the launch_game_wrapper tool is used ONLY for launching games.\n" +
            "SIMPLE WAY TO REMEMBER: VIDEO GAME = launch_game_wrapper tool, REGULAR APP = launch_app tool\n\n" +
            
            "CRITICAL RULES TO FOLLOW:\n" +
            "1. NEVER invent tools or parameters that weren't explicitly provided to you\n" +
            "2. ALWAYS use the exact function signatures as defined - no additional parameters\n" +
            "3. DO NOT fabricate tool outputs or responses - only report what the tools actually return\n" +
            "4. ONLY report the EXACT parameters that were actually provided to the tool\n" +
            "5. After calling a tool, DO NOT repeat or summarize the tool call with fabricated parameters\n" +
            "6. DO NOT generate fake command-line style arguments, quotes, or JSON output\n" +
            "7. With path handling, remember that Windows paths with spaces or special characters need proper quoting\n\n" +
            
            "CRITICAL WORKFLOW INSTRUCTIONS:\n" +
            "1. When a user asks you to perform an action, do NOT just state the tool call - ACTUALLY EXECUTE the appropriate tool\n" +
            "2. After the tool executes, ALWAYS respond to the user with the results - NEVER leave the tool output unexplained\n" +
            "3. DO NOT append text like '[Agent executes: tool_name()]' to your responses - this is ONLY for explanation in this prompt\n" +
            "4. IMMEDIATELY execute the tool when asked, then share and explain the results\n\n" +

            "typing your tools in text does nothing you must actually invoke them\n\n" +
            
            "Be direct, accurate and concise. Focus only on executing the requested tasks through the available tools\n" +
            "and following up with a conversation. You are an agent with tools but also conversational.\n\n" +
            
            "Reminder that you must ACTUALLY EXECUTE tools, not just state tool calls. No writing tool calls in the chat. only invoke them manually\n\n" +
            "ALWAYS END TOOL INVOKATION(S) WITH A REAL CONVERSATIONAL RESPONSE\n\n" +
            "ALWAYS END YOUR RESPONSE WITH A REAL CONVERSATIONAL RESPONSE"
        )
        self.messages = [{"role": "system", "content": system_msg}]
        
    def create_ui(self):
        """Create the main UI components"""
        # Modern Header with gradient-like effect
        header = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY, color="#00d4ff", size=32),
                        ft.Text(
                            "Local Ollama Agent", 
                            size=28, 
                            weight=ft.FontWeight.W_600,
                            color="#ffffff"
                        ),
                    ], spacing=12),
                    padding=ft.padding.only(left=20)
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Clear Chat",
                            on_click=self.clear_chat,
                            icon_color="#ffffff",
                            bgcolor="#1a1a1a",
                            style=ft.ButtonStyle(
                                shape=ft.CircleBorder(),
                                overlay_color="#333333"
                            )
                        )
                    ]),
                    padding=ft.padding.only(right=20)
                )
            ]),
            height=80,
            bgcolor="#1a1a1a",
            border=ft.border.only(bottom=ft.BorderSide(2, "#333333")),
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
            hint_text="✨ Ask me to launch apps, take screenshots, search the web, or get system info...",
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
            content_padding=ft.padding.all(15)
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
            "I'm your AI assistant ready to help with:\n" +
            "💻 Shell commands & system operations\n" +
            "🚀 Application launching\n" +
            "📸 Screenshot capture\n" +
            "🔍 Web search & research\n" +
            "📊 System information & monitoring\n\n" +
            "Just type your request below and I'll get to work!"
        )
        
        # Main layout with modern structure
        self.page.add(
            ft.Column([
                header,
                chat_area,
                input_area,
                status_area
            ], expand=True, spacing=0)
        )
        
    def add_user_message(self, message: str):
        """Add a user message to the chat"""
        user_msg = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, size=16, color="#00d4ff"),
                            ft.Text("You", size=13, weight=ft.FontWeight.W_600, color="#00d4ff")
                        ], spacing=8),
                        ft.Container(
                            content=ft.Text(
                                message, 
                                selectable=True,
                                size=14,
                                color="#ffffff"
                            ),
                            margin=ft.margin.only(top=8)
                        )
                    ]),
                    bgcolor="#1e3a5f",
                    padding=ft.padding.all(16),
                    border_radius=ft.border_radius.only(
                        top_left=20,
                        top_right=20,
                        bottom_left=20,
                        bottom_right=5
                    ),
                    width=500,
                    border=ft.border.all(1, "#2a4a6b")
                )
            ]),
            margin=ft.margin.only(bottom=15)
        )
        self.chat_container.controls.append(user_msg)
        
    def add_agent_message(self, message: str):
        """Add an agent response to the chat"""
        agent_msg = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SMART_TOY, size=16, color="#00ff88"),
                            ft.Text("Agent", size=13, weight=ft.FontWeight.W_600, color="#00ff88")
                        ], spacing=8),
                        ft.Container(
                            content=ft.Text(
                                message, 
                                selectable=True,
                                size=14,
                                color="#ffffff"
                            ),
                            margin=ft.margin.only(top=8)
                        )
                    ]),
                    bgcolor="#1a2f1a",
                    padding=ft.padding.all(16),
                    border_radius=ft.border_radius.only(
                        top_left=20,
                        top_right=20,
                        bottom_left=5,
                        bottom_right=20
                    ),
                    width=500,
                    border=ft.border.all(1, "#2a4a2a")
                ),
                ft.Container(expand=True)
            ]),
            margin=ft.margin.only(bottom=15)
        )
        self.chat_container.controls.append(agent_msg)
        
    def add_tool_message(self, tool_name: str, result: str):
        """Add a tool execution result to the chat"""
        tool_msg = ft.Container(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.BUILD, size=16, color="#ff9500"),
                        ft.Text(f"Tool: {tool_name}", size=13, weight=ft.FontWeight.W_600, color="#ff9500")
                    ], spacing=8),
                    ft.Container(
                        content=ft.Text(
                            result, 
                            selectable=True, 
                            size=13,
                            color="#e0e0e0",
                            font_family="Consolas"
                        ),
                        bgcolor="#2a1f0a",
                        padding=ft.padding.all(12),
                        border_radius=10,
                        margin=ft.margin.only(top=8),
                        border=ft.border.all(1, "#4a3f2a")
                    )
                ]),
                bgcolor="#1f1a0a",
                padding=ft.padding.all(16),
                border_radius=15,
                border=ft.border.all(1, "#3f3520"),
                margin=ft.margin.symmetric(horizontal=50)
            ),
            margin=ft.margin.only(bottom=15)
        )
        self.chat_container.controls.append(tool_msg)
        
    def add_system_message(self, message: str):
        """Add a system message to the chat"""
        system_msg = ft.Container(
            content=ft.Container(
                content=ft.Text(
                    message, 
                    size=14, 
                    color="#b0b0b0", 
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_400
                ),
                padding=ft.padding.all(20),
                bgcolor="#1a1a1a",
                border_radius=15,
                border=ft.border.all(1, "#333333"),
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
            response: ChatResponse = chat(
                model="llama3.1",
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
                    model="llama3.1",
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


def main(page: ft.Page):
    """Main entry point for the Flet app"""
    OllamaAgentGUI(page)


if __name__ == "__main__":
    ft.app(target=main)
