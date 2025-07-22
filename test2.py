#!/usr/bin/env python
"""
Audio Transcription Experiment - Offline Whisper Only
Transcribe audio files from Desktop/Recordings folder using OpenAI Whisper (local)
"""

import os
import sys
from pathlib import Path

def list_audio_files():
    """List all audio files in the Desktop/Recordings folder"""
    recordings_dir = Path.home() / "Desktop" / "Recordings"
    
    if not recordings_dir.exists():
        print(f"❌ Recordings folder not found: {recordings_dir}")
        return []
    
    # Look for common audio file extensions
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
    audio_files = []
    
    for file_path in recordings_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
            audio_files.append(file_path)
    
    return sorted(audio_files, key=lambda x: x.stat().st_mtime, reverse=True)

def transcribe_with_whisper(audio_file):
    """Transcribe audio using OpenAI Whisper (offline) with base model"""
    try:
        import whisper
        import os
        
        # Convert to Path object if it's a string
        audio_path = Path(audio_file) if isinstance(audio_file, str) else audio_file
        
        # Get absolute path and validate file
        absolute_path = audio_path.resolve()
        
        # Check if file exists
        if not absolute_path.exists():
            return f"❌ Error: File not found: {absolute_path}"
            
        # Check if file is accessible
        if not os.access(absolute_path, os.R_OK):
            return f"❌ Error: Cannot access file (permission denied): {absolute_path}"
        
        print("🔄 Loading Whisper base model... (This may take a moment on first run)")
        try:
            model = whisper.load_model("base")
        except Exception as e:
            return f"❌ Error loading Whisper model: {str(e)}\nMake sure you have the required dependencies installed."
        
        print(f"📂 Transcribing audio file: {audio_path.name}")
        print("⏳ This may take a moment...")
        
        try:
            # Transcribe the audio file
            result = model.transcribe(str(absolute_path))
            return result["text"].strip()
        except Exception as e:
            return f"❌ Error during transcription: {str(e)}\nMake sure the file is a valid audio file and FFmpeg is installed."
        
    except ImportError:
        return "❌ Error: whisper library not installed. Install with: pip install openai-whisper"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

def main():
    """Main function to list and transcribe audio files"""
    print("🎤 Offline Audio Transcription with Whisper")
    print("=" * 45)
    
    # List available audio files
    recordings_dir = Path.home() / "Desktop" / "Recordings"
    print(f"🔍 Looking for audio files in: {recordings_dir}")
    
    # Create Recordings directory if it doesn't exist
    if not recordings_dir.exists():
        try:
            recordings_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created Recordings directory at: {recordings_dir}")
        except Exception as e:
            print(f"❌ Failed to create Recordings directory: {e}")
    
    audio_files = list_audio_files()
    
    if not audio_files:
        print("📁 No audio files found in Desktop/Recordings folder")
        print("💡 Please add some audio files (WAV, MP3, M4A, FLAC, OGG, AAC) to the folder and try again.")
        print(f"   Folder location: {recordings_dir}")
        return
    
    print(f"📋 Found {len(audio_files)} audio file(s):")
    for i, file_path in enumerate(audio_files, 1):
        file_size = file_path.stat().st_size / 1024  # KB
        print(f"  {i}. {file_path.name} ({file_size:.1f} KB)")
    
    print("\n" + "=" * 45)
    
    # Let user choose which file to transcribe
    try:
        choice = input(f"\n🎯 Choose a file to transcribe (1-{len(audio_files)}) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Goodbye!")
            return
        
        file_index = int(choice) - 1
        if file_index < 0 or file_index >= len(audio_files):
            print("❌ Invalid choice")
            return
        
        selected_file = audio_files[file_index]
        print(f"\n🎵 Selected: {selected_file.name}")
        
        print("\n" + "=" * 45)
        print("🤖 Using OpenAI Whisper (base model)")
        print("🔒 100% offline and private!")
        
        transcript = transcribe_with_whisper(selected_file)
        
        print("\n📝 TRANSCRIPTION RESULT:")
        print("-" * 45)
        print(transcript)
        print("-" * 45)
        
        # Option to save transcript
        save_choice = input("\n💾 Save transcript to file? (y/n): ").strip().lower()
        if save_choice == 'y':
            transcript_file = selected_file.with_suffix('.txt')
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"Transcript of: {selected_file.name}\n")
                f.write(f"Whisper Model: base\n")
                f.write(f"Generated: {Path(__file__).name}\n")
                f.write("-" * 45 + "\n")
                f.write(transcript)
            print(f"✅ Transcript saved to: {transcript_file}")
        
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except ValueError:
        print("❌ Invalid input")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
