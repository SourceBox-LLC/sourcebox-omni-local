#!/usr/bin/env python3
"""
PDF Summary Tool - Extracts and summarizes content from a PDF file

Takes a PDF file path and returns a summary of its contents.
"""

import os
import requests
from pathlib import Path

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PDFMinerLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file using multiple methods.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text or error message
    """
    # Handle various path formats - try multiple approaches
    import os
    
    # Print received path for debugging
    print(f"Received path: {pdf_path!r}")
    
    # Check for common issues in Windows paths with apostrophes
    if "\\" in pdf_path and "'" not in pdf_path and "S" in pdf_path and "Bussiso" in pdf_path:
        # Fix known issue where apostrophe is removed between S and Bussiso
        if "S\\Bussiso" in pdf_path:
            corrected_path = pdf_path.replace("S\\Bussiso", "S'Bussiso")
            print(f"Corrected path with missing apostrophe: {corrected_path!r}")
            pdf_path = corrected_path
    
    # Try different path variations
    paths_to_try = [
        pdf_path,                                  # Original path
        pdf_path.replace("\\", "/"),               # Forward slashes
        r"{}".format(pdf_path),                      # Raw string format
        pdf_path.replace("'", ""),                  # Without apostrophes
        pdf_path.replace("S\\Bussiso", "S'Bussiso"), # Fix removed apostrophe
    ]
    
    # Try each path variation
    for i, path_to_try in enumerate(paths_to_try):
        if os.path.exists(path_to_try):
            print(f"Found file at variation #{i}: {path_to_try!r}")
            path = Path(path_to_try)
            break
    else:  # No break occurred (file not found)
        # As a last resort, try listing the directory to find similar files
        if "\\" in pdf_path:
            parent_dir = os.path.dirname(pdf_path)
            if os.path.exists(parent_dir):
                print(f"Listing directory {parent_dir} to find similar files:")
                files = os.listdir(parent_dir)
                pdf_files = [f for f in files if f.lower().endswith('.pdf')]
                if pdf_files:
                    print(f"Found PDF files: {pdf_files}")
                    # Try to find an exact match
                    target_name = os.path.basename(pdf_path)
                    for pdf_file in pdf_files:
                        if pdf_file == target_name:
                            path = Path(os.path.join(parent_dir, pdf_file))
                            print(f"Found exact match: {path}")
                            break
                    else:
                        # No exact match found
                        return f"Error: File not found at {pdf_path}\nAvailable PDFs: {pdf_files}"
                else:
                    return f"Error: No PDF files found in {parent_dir}"
            else:
                return f"Error: Directory not found: {parent_dir}"
        return f"Error: File not found at {pdf_path}"
    
    # Try different PDF extraction methods
    extraction_methods = [
        ("PyPDFLoader", PyPDFLoader),
        ("PDFMinerLoader", PDFMinerLoader),
        ("UnstructuredPDFLoader", UnstructuredPDFLoader)
    ]
    
    text = ""
    errors = []
    
    # Try each extraction method until one works
    for method_name, loader_class in extraction_methods:
        try:
            loader = loader_class(str(path))
            documents = loader.load()
            
            # Extract text from documents
            method_text = ""
            for doc in documents:
                method_text += doc.page_content + "\n\n"
                
            # If we got text, use it
            if method_text.strip():
                print(f"Successfully extracted text using {method_name}")
                text = method_text
                break
        except Exception as e:
            errors.append(f"{method_name} error: {str(e)}")
            continue
    
    # If we didn't get any text, return error
    if not text.strip():
        error_message = f"Error: Failed to extract text from PDF using all methods. Errors: {'; '.join(errors)}"
        return error_message
    
    return text


def summarize_text(text, model="llama3.1", max_tokens=500):
    """
    Summarize text using Ollama API.
    
    Args:
        text (str): Text to summarize
        model (str): Ollama model to use
        max_tokens (int): Maximum tokens for summary
        
    Returns:
        str: Summary or error message
    """
    try:
        # Prepare prompt for summarization
        prompt = f"Please provide a concise summary of the following text:\n\n{text}\n\nSummary:"
        
        # Call Ollama API
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }
        
        response = requests.post(url, json=payload)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response received")
        else:
            return f"Error: Ollama API returned status code {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def summarize_pdf_file(pdf_path, model="llama3.1", max_tokens=500, chunk_size=5000):
    # HARDCODED FIX: If this is the NTV PDF, use the direct path
    if "NTV (3).pdf" in pdf_path:
        pdf_path = r"C:\Users\S'Bussiso\Desktop\ollama agent\NTV (3).pdf"
    """
    Extract text from a PDF and generate a summary.
    
    Args:
        pdf_path (str): Path to the PDF file
        model (str): Ollama model to use for summarization
        max_tokens (int): Maximum tokens for the summary
        chunk_size (int): Size of chunks for long documents
        
    Returns:
        str: Summary text if successful, error message if failed
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Check if extraction was successful
    if isinstance(text, str) and text.startswith("Error:"):
        return text
    
    # For short documents, summarize the whole text
    if len(text) <= chunk_size:
        return summarize_text(text, model, max_tokens)
    
    # For longer documents, split into chunks and summarize each chunk
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=200,
        length_function=len
    )
    
    # Split the text into chunks
    chunks = text_splitter.split_text(text)
    
    # Summarize each chunk
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        chunk_summary = summarize_text(chunk, model, max(200, max_tokens // len(chunks)))
        if not chunk_summary.startswith("Error:"):
            chunk_summaries.append(chunk_summary)
    
    # If no summaries were generated, return error
    if not chunk_summaries:
        return "Error: Failed to generate summaries for all chunks"
    
    # Generate final summary from chunk summaries
    combined_summary = "\n\n".join(chunk_summaries)
    
    # If the combined summary is still too long, summarize it again
    if len(combined_summary) > chunk_size:
        return summarize_text(combined_summary, model, max_tokens)
    
    return combined_summary


# Test when run directly
if __name__ == "__main__":
    test_pdf = r"C:\Users\S'Bussiso\Desktop\ollama agent\NTV (3).pdf"
    if os.path.exists(test_pdf):
        print(f"Testing with: {test_pdf}")
        summary = summarize_pdf_file(test_pdf)
        print("\nSUMMARY:")
        print("=========")
        print(summary)
    else:
        print(f"Test PDF not found: {test_pdf}")
