#!/usr/bin/env python
import sys, os
import subprocess
from colorama import init, Fore, Style
from ollama import chat, ChatResponse

# Import tools from agent_tools package
from agent_tools.shell_tool import shell
from agent_tools.launch_app_tool import launch_app
from agent_tools.screenshot_tool import take_screenshot
from agent_tools.web_search_tool import web_search
from agent_tools.system_info_tool import system_info



# Initialize colorama for colored console output
init(autoreset=True)


# ------------------------- Tool Wrappers -------------------------
def run_shell_commands(command: str) -> str:
    """Run a Windows shell command; return stdout or stderr."""
    return shell(command)

def launch_apps(app_name: str) -> str:
    """Launch an application by name."""
    return launch_app(app_name)


def take_screenshot_wrapper(save_path: str = None, window_title: str = None) -> str:
    """Take a screenshot and save it to the specified path."""
    return take_screenshot(save_path=save_path, window_title=window_title)


def web_search_wrapper(query: str, max_results: int = 5) -> str:
    """Search the web for the given query using DuckDuckGo."""
    # Debug the received parameters
    print(f"Debug - Web search wrapper received: query='{query}', max_results={max_results}")
    # Ensure the query is a clean string
    if isinstance(query, str) and query.strip():
        return web_search(query=query, max_results=max_results)
    else:
        return "Error: Invalid or empty search query. Please provide a valid search term."


def get_system_info(info_type: str = "all") -> str:
    """Get system information based on the requested type.
    
    Args:
        info_type: The type of information to retrieve ('all', 'cpu', 'memory', 'disk', 'network', 'os', 'processes')
        
    Returns:
        Formatted system information as a string
    """
    print(f"Debug - System info wrapper received: info_type='{info_type}'")
    return system_info(info_type)


def main():
    system_msg = (
        "You are an AI agent on Windows. You can ONLY perform actions by calling the exact Python functions " +
        "provided to you as tools. DO NOT HALLUCINATE OR INVENT tool calls or parameters that don't exist.\n\n" +
        
        "AVAILABLE TOOLS:\n" +
        "1. run_shell_commands(command): Execute Windows shell commands\n" +
        "2. launch_apps(app_name): Launch applications by name\n" +
        "3. take_screenshot_wrapper(save_path=None, window_title=None): Capture screenshot; optionally specify path and window\n" +
        "4. web_search_wrapper(query, max_results=5): Search the web using DuckDuckGo\n" +
        "5. get_system_info(info_type='all'): Get system information - options: 'all', 'cpu', 'memory', 'disk', 'network', 'os', 'processes'\n\n" +
        
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

        "EXAMPLES OF CORRECT TOOL USAGE AND WORKFLOW:\n" +
        "Example 1:\n" +
        "User: run dir command\n" +
        "Agent: I'll show you the directory contents.\n" +
        "(Tool run_shell_commands executes with command='dir')\n" +
        "Agent: Here are the files in the current directory: [lists actual files from command output]\n\n" +
        
        "Example 2:\n" +
        "User: open calculator\n" +
        "Agent: I'll launch the calculator for you.\n" +
        "(Tool launch_apps executes with app_name='calculator')\n" +
        "Agent: Calculator has been launched successfully.\n\n" +
        
        "Example 3:\n" +
        "User: take a screenshot\n" +
        "Agent: I'll capture a screenshot for you.\n" +
        "(Tool take_screenshot_wrapper executes)\n" +
        "Agent: Screenshot captured and saved to [shows actual path from tool result].\n\n" +
        
        "Example 4:\n" +
        "User: search for latest AI research\n" +
        "Agent: I'll search the web for that information.\n" +
        "(Tool web_search_wrapper executes with query='latest AI research')\n" +
        "Agent: Here's what I found about the latest AI research: [provides actual search results from tool].\n\n" +
        
        "Example 5:\n" +
        "User: how much memory does my system have?\n" +
        "Agent: Let me check your system information.\n" +
        "(Tool get_system_info executes with info_type='memory')\n" +
        "Agent: Your system has 16GB of RAM with 8GB currently available.\n\n" +
        
        "EXAMPLES OF INCORRECT TOOL USAGE (NEVER DO THESE):\n" +
        "❌ NEVER generate fake command line: run_shell_commands(command=\"python -c \\\"print(...)\")\n" +
        "❌ NEVER invent parameters: launch_apps(app_name='notepad', arguments=['-n'])\n" +
        "❌ NEVER use invalid paths: take_screenshot_wrapper(save_path='C:/invalid/\\file*path.png')\n" +
        "❌ NEVER make up search results: web_search_wrapper(query='stock prices', results=[...])\n" +
        "❌ NEVER use invalid info types: get_system_info(info_type='ram_details', format='json')\n\n" +
        
        "Be direct, accurate and concise. Focus only on executing the requested tasks through the available tools."
    )

    messages = [{"role": "system", "content": system_msg}]
    tools = [run_shell_commands, launch_apps, take_screenshot_wrapper, web_search_wrapper, get_system_info]

    print(Fore.GREEN + "Agent ready! Type 'exit' to quit." + Style.RESET_ALL)

    while True:
        user_input = input(Fore.CYAN + "User query: " + Style.RESET_ALL)
        if not user_input or user_input.lower() in ("exit", "quit"):
            print(Fore.YELLOW + "Goodbye!" + Style.RESET_ALL)
            sys.exit(0)

        # Add user message and ask Ollama to decide on tool calls
        messages.append({"role": "user", "content": user_input})
        response: ChatResponse = chat(
            model="llama3.1",
            messages=messages,
            tools=tools,
            stream=False
        )

        # Execute any requested tool calls immediately
        for call in response.message.tool_calls or []:
            fn_name = call.function.name
            args = call.function.arguments or {}
            
            # Debug to see what args are being received
            print(f"Debug - Tool args received: {args}")
            
            # Special handling for paths with apostrophes
            if fn_name == "summarize_pdf" and "pdf_path" in args:
                # Check if path might be truncated at apostrophe
                path = args["pdf_path"]
                if path.startswith("C:\\Users\\S") and not path.startswith("C:\\Users\\S'"):
                    # Likely truncated at S' - try to reconstruct
                    full_path = f"C:\\Users\\S'Bussiso\\Desktop\\ollama agent\\NTV (3).pdf"
                    print(f"Fixing truncated path: {path} → {full_path}")
                    args["pdf_path"] = full_path
            
            # Safety check: only execute functions that are in the tools list
            tool_functions = [tool.__name__ for tool in tools]
            if fn_name in tool_functions:
                result = globals()[fn_name](**args)
                print(Fore.YELLOW + f"[Tool → {fn_name}]\n{result}" + Style.RESET_ALL)
            else:
                error_msg = f"Error: Tool '{fn_name}' is not available in this agent"
                print(Fore.RED + f"[Tool Error]\n{error_msg}" + Style.RESET_ALL)
            messages.append({
                "role": "tool",
                "name": fn_name,
                "content": result
            })

        # Now get the assistant’s final reply incorporating tool output
        final: ChatResponse = chat(
            model="llama3.1",
            messages=messages
        )
        print(Fore.MAGENTA + final.message.content + Style.RESET_ALL)
        messages.append({"role": "assistant", "content": final.message.content})


if __name__ == "__main__":
    main()
