"""Web Search Tool - Perform web searches with DuckDuckGo

This module provides a simple function to search the web using DuckDuckGo.
"""

# Import the proper tools from langchain-community
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

def web_search(query: str, max_results: int = 5) -> str:
    """Perform a web search using DuckDuckGo and return relevant results.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
        
    Returns:
        str: Formatted search results
    """
    try:
        # Create a custom wrapper with more specific parameters
        search_wrapper = DuckDuckGoSearchAPIWrapper(
            max_results=max_results,  # More results
            time='d',                  # Time='d' means search in the last day (recent)
            safesearch='moderate'      # Moderate safe search
        )
        
        # Create the search tool with our custom wrapper
        search_tool = DuckDuckGoSearchResults(api_wrapper=search_wrapper)
        
        # Print debug information
        print(f"Web search executing with query: '{query}'")
        
        # Use the query as provided - no automatic enhancement
        # Get search results
        results = search_tool.invoke(query)
        
        # Format and return the results
        if results and isinstance(results, list) and len(results) > 0:
            formatted_results = ["Search results:"]
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                link = result.get("link", "No link")
                snippet = result.get("snippet", "")
                formatted_result = f"{i}. {title}\nURL: {link}"
                if snippet:
                    formatted_result += f"\nSnippet: {snippet}"
                formatted_results.append(formatted_result)
            return "\n\n".join(formatted_results)
        elif isinstance(results, str) and results.strip():
            # If results is a string (from DuckDuckGoSearchRun)
            return f"Search results:\n{results}"
        else:
            return f"No search results found for '{query}'. Try a different search term."
    except Exception as e:
        # Handle any errors that might occur
        return f"Error while searching for '{query}': {str(e)}. Please try again with a different query."




if __name__ == "__main__":
    search = web_search("current news on bitcoin")
    print(search)
