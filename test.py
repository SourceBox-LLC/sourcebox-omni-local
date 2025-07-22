#!/usr/bin/env python3
"""
File Upload Prototype for Local Ollama Agent
Simple console test to prototype file upload to temporary directory functionality
"""

import os
import shutil
from pathlib import Path
import tempfile

class FileUploadTest:
    def __init__(self):
        self.temp_dir = None
        self.uploaded_files = []
        
    def create_temp_directory(self) -> str:
        """Create a temporary directory for file uploads"""
        if self.temp_dir is None:
            # Create a temp directory in the system temp folder
            self.temp_dir = Path(tempfile.mkdtemp(prefix="ollama_agent_uploads_"))
            print(f"✅ Created temporary directory: {self.temp_dir}")
        return str(self.temp_dir)
        
    def upload_file(self, file_path: str) -> bool:
        """Upload a file to the temporary directory"""
        try:
            source_path = Path(file_path)
            
            # Check if source file exists
            if not source_path.exists():
                print(f"❌ File not found: {file_path}")
                return False
                
            # Ensure temp directory exists
            temp_dir = self.create_temp_directory()
            
            # Copy file to temp directory
            dest_path = Path(temp_dir) / source_path.name
            shutil.copy2(source_path, dest_path)
            
            # Get file info
            file_size = dest_path.stat().st_size
            file_info = {
                'name': source_path.name,
                'size': file_size,
                'path': str(dest_path),
                'original_path': str(source_path)
            }
            
            self.uploaded_files.append(file_info)
            
            print(f"✅ Uploaded: {source_path.name} ({file_size} bytes) -> {dest_path}")
            return True
            
        except Exception as ex:
            print(f"❌ Error uploading {file_path}: {ex}")
            return False
            
    def list_uploaded_files(self):
        """List all uploaded files"""
        if not self.uploaded_files:
            print("📁 No files uploaded yet")
            return
            
        print(f"\n📁 Uploaded Files ({len(self.uploaded_files)} total):")
        print("-" * 60)
        
        total_size = 0
        for i, file_info in enumerate(self.uploaded_files, 1):
            size_mb = file_info['size'] / (1024 * 1024)
            total_size += file_info['size']
            print(f"{i:2d}. {file_info['name']}")
            print(f"    Size: {size_mb:.2f} MB")
            print(f"    Path: {file_info['path']}")
            print()
            
        total_mb = total_size / (1024 * 1024)
        print(f"📊 Total size: {total_mb:.2f} MB")
        if self.temp_dir:
            print(f"📂 Temp directory: {self.temp_dir}")
            
    def remove_file(self, file_name: str) -> bool:
        """Remove a file from temp directory"""
        try:
            # Find the file
            file_info = None
            for f in self.uploaded_files:
                if f['name'] == file_name:
                    file_info = f
                    break
                    
            if not file_info:
                print(f"❌ File not found: {file_name}")
                return False
                
            # Remove from filesystem
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
                print(f"✅ Removed file: {file_name}")
                
            # Remove from uploaded files list
            self.uploaded_files = [f for f in self.uploaded_files if f['name'] != file_name]
            return True
            
        except Exception as ex:
            print(f"❌ Error removing file: {ex}")
            return False
            
    def clear_all_files(self):
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
                except OSError:
                    print("⚠️ Temporary directory not empty, keeping it")
                    
            print("✅ All files cleared")
            
        except Exception as ex:
            print(f"❌ Error clearing files: {ex}")
            
    def get_temp_directory(self) -> str:
        """Get the current temp directory path"""
        return str(self.temp_dir) if self.temp_dir else "No temp directory created yet"

def test_file_upload():
    """Test the file upload functionality"""
    print("🧪 File Upload Test - Console Version")
    print("=" * 50)
    
    uploader = FileUploadTest()
    
    while True:
        print("\n📋 Options:")
        print("1. Upload a file")
        print("2. List uploaded files")
        print("3. Remove a file")
        print("4. Clear all files")
        print("5. Show temp directory")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            file_path = input("Enter file path to upload: ").strip().strip('"')
            if file_path:
                uploader.upload_file(file_path)
            else:
                print("❌ No file path provided")
                
        elif choice == '2':
            uploader.list_uploaded_files()
            
        elif choice == '3':
            uploader.list_uploaded_files()
            if uploader.uploaded_files:
                file_name = input("Enter filename to remove: ").strip()
                if file_name:
                    uploader.remove_file(file_name)
                else:
                    print("❌ No filename provided")
                    
        elif choice == '4':
            uploader.clear_all_files()
            
        elif choice == '5':
            print(f"📂 Current temp directory: {uploader.get_temp_directory()}")
            
        elif choice == '6':
            print("\n🧹 Cleaning up...")
            uploader.clear_all_files()
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-6.")



if __name__ == "__main__":
    test_file_upload()
