#!/usr/bin/env python3
"""
Document Loader Tool for Local Ollama Agent
Loads and extracts content from various document formats using LangChain UnstructuredLoader

Supported formats:
- PDF files (.pdf)
- Word documents (.docx, .doc)
- Text files (.txt)
- JSON files (.json)
- CSV files (.csv)
- Excel files (.xlsx, .xls)
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# LangChain imports with fallback handling
try:
    from langchain_unstructured import UnstructuredLoader
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.document_loaders import UnstructuredFileLoader as UnstructuredLoader
        UNSTRUCTURED_AVAILABLE = True
    except ImportError:
        UNSTRUCTURED_AVAILABLE = False

class DocumentLoaderTool:
    """Tool for loading and extracting content from various document formats"""
    
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
        
    def extract_content(self, file_path: str) -> Dict[str, Any]:
        """
        Extract content from a document file
        
        Args:
            file_path (str): Path to the document file
            
        Returns:
            Dict containing success status, content, metadata, and any errors
        """
        if not UNSTRUCTURED_AVAILABLE:
            return {
                'success': False,
                'error': 'Document processing not available. Install langchain-unstructured.',
                'content': None,
                'metadata': None,
                'content_preview': None
            }
            
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'content': None,
                    'metadata': None,
                    'content_preview': None
                }
                
            # Check if file format is supported
            if not self.is_supported_file(file_path):
                return {
                    'success': False,
                    'error': f'Unsupported file format: {Path(file_path).suffix}',
                    'content': None,
                    'metadata': None,
                    'content_preview': None
                }
                
            # Load document using UnstructuredLoader
            loader = UnstructuredLoader(file_path)
            documents = loader.load()
            
            if not documents:
                return {
                    'success': False,
                    'error': 'No content extracted from document',
                    'content': None,
                    'metadata': None,
                    'content_preview': None
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
                'file_extension': file_path_obj.suffix.lower(),
                'content_length': len(content)
            })
            
            # Create content preview (first 200 characters)
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            return {
                'success': True,
                'error': None,
                'content': content,
                'metadata': metadata,
                'content_preview': content_preview,
                'document_count': len(documents)
            }
            
        except Exception as ex:
            return {
                'success': False,
                'error': f'Error processing document: {str(ex)}',
                'content': None,
                'metadata': None,
                'content_preview': None
            }

# Global instance for easy import
document_loader = DocumentLoaderTool()

def load_document_content(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to load document content
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        Dict containing extracted content and metadata
    """
    return document_loader.extract_content(file_path)

def is_supported_document(file_path: str) -> bool:
    """
    Check if a file is a supported document format
    
    Args:
        file_path (str): Path to check
        
    Returns:
        bool: True if file format is supported
    """
    return document_loader.is_supported_file(file_path)

def get_document_type(file_path: str) -> str:
    """
    Get human-readable document type
    
    Args:
        file_path (str): Path to the document
        
    Returns:
        str: Human-readable file type
    """
    return document_loader.get_file_type(file_path)
