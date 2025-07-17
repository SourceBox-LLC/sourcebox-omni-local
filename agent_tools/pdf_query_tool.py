import os
import glob
import time
from pathlib import Path
import json
import requests

# PDF processing
import PyPDF2

# Vector DB and embeddings
from chromadb import PersistentClient

class PDFQueryTool:
    def __init__(self, pdf_dir=None, db_dir="./pdf_vector_db"):
        """
        Initialize the PDF Query Tool with directories for PDFs and vector database
        
        Args:
            pdf_dir (str): Directory containing PDF files to index
            db_dir (str): Directory to store the vector database
        """
        self.pdf_dir = pdf_dir or str(Path.home() / "Documents")
        self.db_dir = db_dir
        self.collection_name = "pdf_documents"
        self.client = PersistentClient(path=db_dir)
        
        # Create or get existing collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"Using existing collection with {self.collection.count()} documents")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Created new collection: {self.collection_name}")
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text content from a PDF file with timeouts and error handling
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        try:
            # First check if file is accessible and not too large
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # Size in MB
            if file_size > 100:  # Skip files larger than 100MB
                print(f"Skipping large file ({file_size:.1f} MB): {pdf_path}")
                return ""
                
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                total_pages = len(reader.pages)
                print(f"Extracting text from {total_pages} pages")
                
                # Process a maximum of 50 pages to avoid huge files
                pages_to_process = min(total_pages, 50)
                
                for page_num in range(pages_to_process):
                    try:
                        # Add timeout protection by checking time elapsed
                        start_time = time.time()
                        page_text = reader.pages[page_num].extract_text()
                        text += page_text + "\n"
                        
                        # Report progress periodically
                        if (page_num + 1) % 5 == 0:
                            print(f"  Processed {page_num + 1}/{pages_to_process} pages...")
                            
                        # If a single page takes too long, skip remaining pages
                        if time.time() - start_time > 5:  # 5 second timeout per page
                            print(f"  Page {page_num} took too long to process, skipping remaining pages")
                            break
                            
                    except Exception as e:
                        print(f"  Error on page {page_num}: {str(e)}")
                        continue
                        
                if total_pages > pages_to_process:
                    print(f"  Note: Only processed {pages_to_process} of {total_pages} total pages")
                    
                return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def chunk_text(self, text, chunk_size=1000, overlap=100):
        """
        Split text into overlapping chunks for better context retention with safeguards
        
        Args:
            text (str): Text to split into chunks
            chunk_size (int): Maximum characters per chunk
            overlap (int): Overlap between chunks in characters
            
        Returns:
            list: List of text chunks
        """
        print("Starting text chunking...")
        
        # Handle empty or very small texts
        if not text:
            print("Warning: Empty text provided to chunker")
            return []
            
        if len(text) < chunk_size:
            print(f"Text is smaller than chunk size ({len(text)} chars), using as single chunk")
            return [text]
        
        print(f"Chunking {len(text)} characters of text into ~{chunk_size} char chunks")
        
        # Simple and robust chunking - split by newlines first, then combine
        lines = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for i, line in enumerate(lines):
            # Progress reporting
            if i % 100 == 0 and i > 0:
                print(f"  Processed {i}/{len(lines)} lines...")
                
            # If adding this line would exceed chunk size, finalize current chunk
            if len(current_chunk) + len(line) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                
                # For overlap, include the last few lines from previous chunk
                # Find the approximate position for overlap
                overlap_start = max(0, len(current_chunk) - overlap)
                if ' ' in current_chunk[overlap_start:]:
                    # Find the first space after overlap_start for a clean break
                    space_pos = current_chunk.find(' ', overlap_start)
                    if space_pos != -1:
                        overlap_start = space_pos + 1
                        
                current_chunk = current_chunk[overlap_start:]
            
            # Add the current line to the chunk
            current_chunk += line + "\n"
            
            # Safety check - if current_chunk is getting too large, force a break
            if len(current_chunk) > chunk_size * 1.5:
                chunks.append(current_chunk)
                current_chunk = ""
        
        # Don't forget to add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
            
        print(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def generate_embeddings(self, text_chunks, is_query=False):
        """
        Generate embeddings using Ollama's HTTP API with timeouts and robust error handling
        
        Args:
            text_chunks (list): List of text chunks to embed
            is_query (bool): Whether this is for a search query (allow shorter text)
            
        Returns:
            list: List of embedding vectors
        """
        embeddings = []
        total_chunks = len(text_chunks)
        print(f"Generating embeddings for {total_chunks} chunks")
        
        # Ollama API URL
        api_url = "http://localhost:11434/api/embeddings"
        model = "mxbai-embed-large"
        
        # Debug: Print all available models
        print("  Checking for available Ollama models...")
        try:
            # Use the correct endpoint to list models
            model_check = requests.get("http://localhost:11434/api/tags")
            if model_check.status_code == 200:
                # Debug the response
                print(f"  API response: {model_check.text[:200]}...")
                
                # For the tags endpoint, models are usually directly in the list
                models_list = model_check.json().get("models", [])
                if models_list:
                    model_names = [m.get("name", "").split(":")[0] for m in models_list]
                    print(f"  Available models: {model_names}")
                    
                    if "mxbai-embed-large" in model_names:
                        model = "mxbai-embed-large"
                        print(f"  Using model: {model}")
                    elif "llama3" in model_names:
                        model = "llama3"
                        print(f"  Using model: {model}")
                    elif any("llama" in m.lower() for m in model_names):
                        # Find any llama model
                        for m in model_names:
                            if "llama" in m.lower():
                                model = m
                                print(f"  Using model: {model}")
                                break
                    else:
                        # Use the first available model
                        if model_names:
                            model = model_names[0]
                            print(f"  Using first available model: {model}")
                        else:
                            print("  No models found in the response")
                            return [None] * total_chunks
                else:
                    print("  No models found in the API response")
                    return [None] * total_chunks
            else:
                print(f"  Failed to get model list from Ollama API: {model_check.status_code}")
                # Try to continue with the default model anyway
                print(f"  Attempting to use default model: {model}")
        except Exception as e:
            print(f"  Error checking available models: {str(e)}")
            # Try to continue with the default model anyway
            print(f"  Attempting to use default model: {model} despite error")
        
        for i, chunk in enumerate(text_chunks):
            try:
                # Skip empty chunks
                if not chunk:
                    print(f"  Skipping empty chunk")
                    embeddings.append(None)
                    continue
                    
                # For short chunks, handle differently if it's a query
                min_length = 3 if is_query else 50  # Much smaller minimum for queries
                
                if len(chunk) < min_length:
                    if is_query:
                        # For short queries, pad with repetition or context
                        print(f"  Query is short ({len(chunk)} chars), padding for better embedding")
                        # Pad by repeating and adding context
                        clean_chunk = f"Find information about: {chunk} {chunk} {chunk}"
                    else:
                        print(f"  Skipping too short chunk ({len(chunk)} chars)")
                        embeddings.append(None)
                        continue
                else:
                    # Clean and limit the chunk size (prevent large inputs)
                    clean_chunk = chunk[:1000].replace('\n', ' ').strip()
                
                # Report progress periodically
                if (i + 1) % 5 == 0 or i == 0:
                    print(f"  Generating embedding for chunk {i+1}/{total_chunks}...")
                
                # Use Ollama's HTTP API to generate embeddings
                payload = {
                    "model": model,
                    "prompt": clean_chunk
                }
                
                try:
                    response = requests.post(api_url, json=payload, timeout=15)
                    
                    if response.status_code == 200:
                        embedding_data = response.json()
                        if 'embedding' in embedding_data:
                            embeddings.append(embedding_data['embedding'])
                        else:
                            print(f"  Missing embedding in response")
                            embeddings.append(None)
                    else:
                        print(f"  Error from Ollama API: HTTP {response.status_code}, {response.text[:100]}")
                        embeddings.append(None)
                        
                except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                    print(f"  API request failed for chunk {i+1}: {str(e)}")
                    embeddings.append(None)
                    
                # Add a small delay to avoid overwhelming Ollama
                time.sleep(0.2)
                
            except Exception as e:
                print(f"  Failed to generate embedding for chunk {i+1}: {str(e)}")
                embeddings.append(None)
        
        valid_count = sum(1 for e in embeddings if e is not None)
        print(f"Successfully generated {valid_count}/{total_chunks} embeddings")
        return embeddings
    
    def index_pdfs(self, refresh=False):
        """
        Index all PDFs in the specified directory
        
        Args:
            refresh (bool): If True, reindex all PDFs even if already indexed
            
        Returns:
            str: Summary of indexing operation
        """
        if refresh:
            # Delete and recreate collection if refresh is requested
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Recreated collection: {self.collection_name}")
            
        # Find all PDF files in the directory
        pdf_files = glob.glob(os.path.join(self.pdf_dir, "**/*.pdf"), recursive=True)
        
        if not pdf_files:
            print(f"No PDF files found in {self.pdf_dir}")
            return {"status": "error", "message": f"No PDF files found in {self.pdf_dir}"}
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        indexed_count = 0
        failed_count = 0
        
        # Set a maximum number of PDFs to process to avoid long-running operations
        max_pdfs = min(10, len(pdf_files))  # Process up to 10 PDFs at a time
        if len(pdf_files) > max_pdfs:
            print(f"NOTE: Processing only the first {max_pdfs} PDFs out of {len(pdf_files)} total")
        
        for i, pdf_path in enumerate(pdf_files[:max_pdfs]):
            try:
                print(f"\nProcessing PDF {i+1}/{max_pdfs}: {pdf_path}")
                
                # Set overall timeout for processing this PDF
                start_time = time.time()
                max_processing_time = 120  # 2 minutes max per PDF
                
                # Extract text from the PDF
                text = self.extract_text_from_pdf(pdf_path)
                if not text or len(text) < 100:  # Require at least 100 chars
                    print(f"  Insufficient text extracted from {pdf_path}, skipping...")
                    failed_count += 1
                    continue
                print(f"  Text extraction completed ({len(text)} characters)")
                
                # Check if we're taking too long
                if time.time() - start_time > max_processing_time:
                    print(f"  Processing timeout for {pdf_path}, moving to next file")
                    failed_count += 1
                    continue
                    
                # Split the text into chunks
                try:
                    chunks = self.chunk_text(text)
                    if not chunks:
                        print(f"  No chunks created for {pdf_path}, skipping...")
                        failed_count += 1
                        continue
                    print(f"  Created {len(chunks)} text chunks")
                except Exception as e:
                    print(f"  Error during text chunking: {str(e)}")
                    failed_count += 1
                    continue
                
                # Check if we're taking too long
                if time.time() - start_time > max_processing_time:
                    print(f"  Processing timeout for {pdf_path}, moving to next file")
                    failed_count += 1
                    continue
                    
                # Generate embeddings for the chunks
                try:
                    print("  Generating embeddings...")
                    embeddings = self.generate_embeddings(chunks)
                    print(f"  Embedding generation completed")
                except Exception as e:
                    print(f"  Error during embedding generation: {str(e)}")
                    failed_count += 1
                    continue
                
                # Create document IDs and metadata
                print("  Preparing document metadata...")
                ids = [f"{Path(pdf_path).stem}-{i}" for i in range(len(chunks))]
                metadatas = [
                    {
                        "source": pdf_path,
                        "page": f"chunk-{i}",
                        "filename": Path(pdf_path).name
                    } 
                    for i in range(len(chunks))
                ]
                
                # Filter out any chunks where embedding failed
                valid_chunks = []
                valid_embeddings = []
                valid_ids = []
                valid_metadatas = []
                
                for i, embedding in enumerate(embeddings):
                    if embedding is not None:
                        valid_chunks.append(chunks[i])
                        valid_embeddings.append(embedding)
                        valid_ids.append(ids[i])
                        valid_metadatas.append(metadatas[i])
                
                if not valid_chunks:
                    print(f"  No valid embeddings created for {pdf_path}, skipping...")
                    failed_count += 1
                    continue
                
                # Add to ChromaDB
                print(f"  Adding {len(valid_chunks)} chunks to ChromaDB...")
                try:
                    self.collection.add(
                        documents=valid_chunks,
                        embeddings=valid_embeddings,
                        ids=valid_ids,
                        metadatas=valid_metadatas
                    )
                    print("  Successfully added to database")
                    indexed_count += 1
                except Exception as e:
                    print(f"  Error adding to ChromaDB: {str(e)}")
                    failed_count += 1
                
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                failed_count += 1
                
        # Final report
        print(f"\nIndexing complete: {indexed_count} PDFs indexed successfully, {failed_count} failed")
                
        return {
            "status": "success" if indexed_count > 0 else "warning",
            "indexed": indexed_count,
            "failed": failed_count,
            "total": len(pdf_files)
        }
    
    def query_pdfs(self, query_text, n_results=5):
        """
        Search indexed PDF content based on a query
        
        Args:
            query_text (str): Query text to search for
            n_results (int): Number of results to return
            
        Returns:
            dict: Results with chunks and metadata
        """
        try:
            # Generate embedding for query - mark as is_query=True for special handling
            query_embedding = self.generate_embeddings([query_text], is_query=True)[0]
            
            if query_embedding is None:
                print("\nFailed to generate embedding for query")
                return None
                
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            if not results["ids"][0]:
                return "No results found for query"
                
            # Format results
            response = f"Results for query: '{query_text}'\n{'-' * 60}\n"
            
            for i, (chunk, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                source = metadata["source"]
                filename = metadata["filename"]
                relevance = 100 * (1 - distance)  # Convert distance to percentage relevance
                
                response += f"\n[{i+1}] {filename} (Relevance: {relevance:.1f}%)\n"
                response += f"Source: {source}\n"
                response += f"Text: {chunk[:300]}...\n"
            
            return response
            
        except Exception as e:
            return f"Error querying documents: {str(e)}"


def main():
    print("PDF Query Tool Test")
    print("-" * 60)
    
    # Get PDF directory from user or use default
    default_dir = str(Path.home() / "Documents")
    pdf_dir = input(f"Enter directory with PDFs to index [default: {default_dir}]: ").strip()
    if not pdf_dir:
        pdf_dir = default_dir
    
    # Initialize the tool
    tool = PDFQueryTool(pdf_dir=pdf_dir)
    
    # Interactive menu
    while True:
        print("\n" + "-" * 60)
        print("1. Index PDF files")
        print("2. Query indexed documents")
        print("3. Exit")
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            refresh = input("Re-index all PDFs? (y/n): ").lower().startswith('y')
            result = tool.index_pdfs(refresh=refresh)
            print(f"\n{result}")
            
        elif choice == '2':
            if tool.collection.count() == 0:
                print("\nNo documents indexed yet. Please index PDFs first.")
                continue
                
            query = input("\nEnter your query: ").strip()
            if not query:
                continue
                
            n_results = int(input("Number of results to return [default: 5]: ") or "5")
            result = tool.query_pdfs(query, n_results=n_results)
            print(f"\n{result}")
            
        elif choice == '3':
            print("\nExiting PDF Query Tool")
            break
            
        else:
            print("\nInvalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
