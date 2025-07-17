#!/usr/bin/env python
"""
Launcher script for Local Ollama Agent
Allows users to choose between console and GUI versions
"""

import sys
import os
import subprocess

def main():
    print("=" * 50)
    print("🤖 Local Ollama Agent Launcher")
    print("=" * 50)
    print()
    print("Choose your preferred interface:")
    print("1. Console Interface (Original)")
    print("2. GUI Interface (Flet)")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🖥️  Starting Console Interface...")
            try:
                # Run the original console agent
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                agent_path = os.path.join(parent_dir, "agent.py")
                subprocess.run([sys.executable, agent_path], cwd=parent_dir)
            except KeyboardInterrupt:
                print("\n👋 Console agent stopped.")
            except Exception as e:
                print(f"\n❌ Error starting console agent: {e}")
            break
            
        elif choice == "2":
            print("\n🎨 Starting GUI Interface...")
            try:
                # Run the Flet GUI agent
                gui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_agent.py")
                subprocess.run([sys.executable, gui_path])
            except KeyboardInterrupt:
                print("\n👋 GUI agent stopped.")
            except Exception as e:
                print(f"\n❌ Error starting GUI agent: {e}")
            break
            
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
