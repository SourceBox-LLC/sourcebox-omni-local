#!/usr/bin/env python3
"""
Web Page Content Loader Tool
Loads and processes full web page contents for analysis and summarization
"""
from langchain_community.document_loaders import WebBaseLoader
from typing import List, Dict, Any, Union
import logging
from urllib.parse import urlparse

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_web_content(urls: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Load content from one or more web pages.
    
    Args:
        urls: Single URL string or list of URLs to load
        
    Returns:
        Dict containing success status, content, and metadata
    """
    try:
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
        
        # Validate URLs
        valid_urls = []
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.scheme in ['http', 'https'] and parsed.netloc:
                    valid_urls.append(url)
                else:
                    logger.warning(f"Invalid URL format: {url}")
            except Exception as e:
                logger.warning(f"Error parsing URL {url}: {e}")
        
        if not valid_urls:
            return {
                "success": False,
                "error": "No valid URLs provided",
                "content": ""
            }
        
        # Load content using LangChain WebBaseLoader
        loader = WebBaseLoader(valid_urls)
        documents = loader.load()
        
        if not documents:
            return {
                "success": False,
                "error": "No content could be loaded from the provided URLs",
                "content": ""
            }
        
        # Process and format the content
        processed_content = []
        total_chars = 0
        
        for doc in documents:
            # Get page metadata
            source = doc.metadata.get('source', 'Unknown URL')
            title = doc.metadata.get('title', 'No Title')
            
            # Get page content (full content, no truncation)
            content = doc.page_content.strip()
            
            processed_content.append({
                "url": source,
                "title": title,
                "content": content,
                "char_count": len(content)
            })
            
            total_chars += len(content)
        
        # Format final response
        if len(processed_content) == 1:
            # Single page response
            page = processed_content[0]
            formatted_content = f"**Title:** {page['title']}\n**URL:** {page['url']}\n**Content:**\n{page['content']}"
        else:
            # Multiple pages response
            formatted_parts = []
            for i, page in enumerate(processed_content, 1):
                formatted_parts.append(
                    f"**Page {i}:**\n**Title:** {page['title']}\n**URL:** {page['url']}\n**Content:**\n{page['content']}\n{'-'*50}"
                )
            formatted_content = "\n\n".join(formatted_parts)
        
        return {
            "success": True,
            "content": formatted_content,
            "metadata": {
                "pages_loaded": len(processed_content),
                "total_characters": total_chars,
                "urls_processed": valid_urls
            }
        }
        
    except Exception as e:
        logger.exception("Error loading web content")
        return {
            "success": False,
            "error": f"Error loading web content: {str(e)}",
            "content": ""
        }

def test_web_loader():
    """
    Test the web content loader with various scenarios.
    """
    print("Web Page Content Loader Tool Test")
    print("=" * 40)
    
    # Test 1: Single URL
    print("\n1. Testing single URL...")
    result = load_web_content("https://www.python.org")
    if result["success"]:
        print(f"✅ Successfully loaded content ({result['metadata']['total_characters']} chars)")
        print(f"Preview: {result['content'][:200]}...")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: Multiple URLs
    print("\n2. Testing multiple URLs...")
    urls = [
        "https://httpbin.org/json",
        "https://httpbin.org/html"
    ]
    result = load_web_content(urls)
    if result["success"]:
        print(f"✅ Successfully loaded {result['metadata']['pages_loaded']} pages")
        print(f"Total characters: {result['metadata']['total_characters']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 3: Interactive test
    print("\n3. Interactive test:")
    user_url = input("Enter a URL to load (or press Enter to skip): ").strip()
    if user_url:
        print(f"\nLoading content from: {user_url}")
        result = load_web_content(user_url)
        if result["success"]:
            print(f"\n✅ Content loaded successfully!")
            print(f"Characters: {result['metadata']['total_characters']}")
            print(f"\nContent preview:\n{'-'*30}")
            print(result['content'])
        else:
            print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    test_web_loader()
    