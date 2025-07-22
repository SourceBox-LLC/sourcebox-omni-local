#!/usr/bin/env python3
"""
Universal Document Loader Test Script
Tests loading various document formats using LangChain UnstructuredLoader

Supported formats:
- PDF files (.pdf)
- Word documents (.docx, .doc)
- Text files (.txt)
- JSON files (.json)
- CSV files (.csv)
- Excel files (.xlsx, .xls)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# LangChain imports
try:
    from langchain_unstructured import UnstructuredLoader
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    print("⚠️ langchain_unstructured not available, trying alternative imports...")
    try:
        from langchain_community.document_loaders import UnstructuredFileLoader as UnstructuredLoader
        UNSTRUCTURED_AVAILABLE = True
    except ImportError:
        print("❌ UnstructuredLoader not available. Install with: pip install langchain-unstructured")
        UNSTRUCTURED_AVAILABLE = False

class DocumentLoader:
    def __init__(self):
        self.supported_extensions = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document (DOCX)',
            '.doc': 'Word Document (DOC)',
            '.txt': 'Text File',
            '.json': 'JSON File',
            '.csv': 'CSV File',
            '.xlsx': 'Excel File (XLSX)',
            '.xls': 'Excel File (XLS)'
        }
        
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file format is supported"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_extensions
        
    def get_file_type(self, file_path: str) -> str:
        """Get human-readable file type"""
        file_ext = Path(file_path).suffix.lower()
        return self.supported_extensions.get(file_ext, 'Unknown')
        
    def load_document(self, file_path: str) -> Dict[str, Any]:
        """Load document content using UnstructuredLoader"""
        if not UNSTRUCTURED_AVAILABLE:
            return {
                'success': False,
                'error': 'UnstructuredLoader not available. Install langchain-unstructured.',
                'content': None,
                'metadata': None
            }
            
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'content': None,
                    'metadata': None
                }
                
            # Check if file format is supported
            if not self.is_supported_file(file_path):
                return {
                    'success': False,
                    'error': f'Unsupported file format: {Path(file_path).suffix}',
                    'content': None,
                    'metadata': None
                }
                
            print(f"📄 Loading {self.get_file_type(file_path)}: {Path(file_path).name}")
            
            # Load document using UnstructuredLoader
            loader = UnstructuredLoader(file_path)
            documents = loader.load()
            
            if not documents:
                return {
                    'success': False,
                    'error': 'No content extracted from document',
                    'content': None,
                    'metadata': None
                }
                
            # Extract content and metadata from first document
            doc = documents[0]
            content = doc.page_content
            metadata = doc.metadata
            
            # Add file information to metadata
            file_path_obj = Path(file_path)
            metadata.update({
                'file_name': file_path_obj.name,
                'file_size': file_path_obj.stat().st_size,
                'file_type': self.get_file_type(file_path),
                'file_extension': file_path_obj.suffix.lower()
            })
            
            return {
                'success': True,
                'error': None,
                'content': content,
                'metadata': metadata,
                'document_count': len(documents)
            }
            
        except Exception as ex:
            return {
                'success': False,
                'error': f'Error loading document: {str(ex)}',
                'content': None,
                'metadata': None
            }
            
    def load_multiple_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Load multiple documents"""
        results = []
        for file_path in file_paths:
            result = self.load_document(file_path)
            results.append(result)
        return results
        
    def print_document_summary(self, result: Dict[str, Any]):
        """Print a summary of loaded document"""
        if not result['success']:
            print(f"❌ Error: {result['error']}")
            return
            
        content = result['content']
        metadata = result['metadata']
        
        print(f"✅ Successfully loaded: {metadata.get('file_name', 'Unknown')}")
        print(f"📊 File Type: {metadata.get('file_type', 'Unknown')}")
        print(f"📏 File Size: {metadata.get('file_size', 0):,} bytes")
        print(f"📝 Content Length: {len(content):,} characters")
        
        # Show first 200 characters of content
        preview = content[:200] + "..." if len(content) > 200 else content
        print(f"\n📖 Content Preview:")
        print("-" * 40)
        print(preview)
        print("-" * 40)
        
        # Show metadata
        print(f"\n🏷️ Metadata:")
        for key, value in metadata.items():
            if key not in ['file_name', 'file_type', 'file_size']:  # Skip already shown
                print(f"  {key}: {value}")
        print()

def test_document_loader():
    """Interactive test for document loading"""
    print("📚 Universal Document Loader Test")
    print("=" * 50)
    
    if not UNSTRUCTURED_AVAILABLE:
        print("❌ UnstructuredLoader not available.")
        print("Install with: pip install langchain-unstructured")
        return
        
    loader = DocumentLoader()
    
    print(f"\n🎯 Supported file formats:")
    for ext, desc in loader.supported_extensions.items():
        print(f"  {ext} - {desc}")
    
    while True:
        print("\n📋 Options:")
        print("1. Load a single document")
        print("2. Load multiple documents")
        print("3. List supported formats")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            file_path = input("Enter file path: ").strip().strip('"')
            if file_path:
                print(f"\n🔄 Processing: {file_path}")
                result = loader.load_document(file_path)
                loader.print_document_summary(result)
            else:
                print("❌ No file path provided")
                
        elif choice == '2':
            print("Enter file paths (one per line, empty line to finish):")
            file_paths = []
            while True:
                path = input("File path: ").strip().strip('"')
                if not path:
                    break
                file_paths.append(path)
                
            if file_paths:
                print(f"\n🔄 Processing {len(file_paths)} files...")
                results = loader.load_multiple_documents(file_paths)
                
                success_count = 0
                for i, result in enumerate(results, 1):
                    print(f"\n📄 Document {i}:")
                    loader.print_document_summary(result)
                    if result['success']:
                        success_count += 1
                        
                print(f"\n📊 Summary: {success_count}/{len(file_paths)} documents loaded successfully")
            else:
                print("❌ No file paths provided")
                
        elif choice == '3':
            print(f"\n🎯 Supported file formats:")
            for ext, desc in loader.supported_extensions.items():
                print(f"  {ext} - {desc}")
                
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    test_document_loader()
