# Local Ollama Agent - GUI Version

A beautiful graphical user interface for the Local Ollama Agent, built with Flet framework.

## Features

🎨 **Beautiful Modern UI**
- Dark theme with intuitive chat interface
- Real-time status updates
- Tool execution visualization
- Responsive design

🛠️ **Full Tool Support**
- Shell command execution
- Application launcher
- Screenshot capture
- Web search (DuckDuckGo)
- System information retrieval

💬 **Chat Interface**
- Conversation history
- Message threading
- Clear chat functionality
- Auto-scrolling

## Installation

1. Make sure you have Python 3.9+ installed
2. Install Flet if not already installed:
   ```bash
   pip install flet
   ```

## Usage

### Option 1: Use the Launcher (Recommended)
```bash
python flet_ui/launcher.py
```
This will give you a choice between console and GUI versions.

### Option 2: Run GUI Directly
```bash
python flet_ui/gui_agent.py
```

### Option 3: Run Console Version
```bash
python agent.py
```

## Interface Overview

- **Header**: Shows agent status and clear chat button
- **Chat Area**: Displays conversation with color-coded messages:
  - Blue: Your messages
  - Green: Agent responses
  - Orange: Tool execution results
- **Input Area**: Type your requests and send them
- **Status Bar**: Shows current agent activity

## Example Commands

Try these commands to test the agent:

```
Take a screenshot
```

```
Search for latest Python news
```

```
Get system memory info
```

```
Launch notepad
```

```
Run dir command
```

## Technical Details

- Built with Flet framework (Python + Flutter)
- Uses same Ollama backend as console version
- Maintains conversation context
- Thread-safe UI updates
- Error handling and status feedback

## Troubleshooting

1. **Agent not responding**: Make sure Ollama is running with llama3.1 model
2. **Tool errors**: Check that all dependencies are installed
3. **UI issues**: Try restarting the application

## Development

The GUI is designed to be a drop-in replacement for the console interface:
- Same tool functions
- Same system prompts
- Same conversation flow
- No modifications to original agent code

Enjoy your beautiful new agent interface! 🚀
