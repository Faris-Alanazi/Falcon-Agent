import os
import requests
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, Field

from crewai.tools import BaseTool
from src.config.config import BRAVE_SEARCH_API_KEY, BRAVE_SEARCH_MCP_URL
from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class BraveSearchToolInput(BaseModel):
    """Input for the Brave Search Tool."""
    query: str = Field(..., description="The search query to use.")
    count: int = Field(5, description="Number of search results to return (1-20).")
    offset: int = Field(0, description="Starting offset for pagination (0-9).")

class BraveSearchTool(BaseTool):
    """
    Tool to search the web using Brave Search API.
    Uses the MCP server specified in the config.
    """
    
    name: str = "brave_search"
    description: str = "Search the web for information using Brave Search."
    args_schema: Type[BaseModel] = BraveSearchToolInput
    
    def _run(self, query: str, count: int = 5, offset: int = 0) -> str:
        """
        Execute the web search using Brave Search API.
        
        Args:
            query (str): The search query
            count (int): Number of results to return (1-20)
            offset (int): Starting offset for pagination (0-9)
            
        Returns:
            str: Search results in a formatted string
        """
        try:
            # Ensure valid parameter values
            count = min(max(count, 1), 20)  # between 1 and 20
            offset = min(max(offset, 0), 9)  # between 0 and 9
            
            # Call the Brave Search MCP server
            response = self._call_brave_search_mcp(query, count, offset)
            
            # Format the results
            formatted_results = self._format_results(response)
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error executing Brave Search: {str(e)}")
            return f"Error executing search: {str(e)}"
    
    def _call_brave_search_mcp(self, query: str, count: int, offset: int) -> Dict[str, Any]:
        """
        Call the Brave Search MCP server.
        
        Args:
            query (str): The search query
            count (int): Number of results to return
            offset (int): Starting offset for pagination
            
        Returns:
            Dict[str, Any]: The response from the MCP server
        """
        # If we're using direct API
        if BRAVE_SEARCH_API_KEY:
            return self._call_brave_search_api(query, count, offset)
        
        # Using MCP server
        try:
            mcp_endpoint = f"{BRAVE_SEARCH_MCP_URL}/search"
            payload = {
                "query": query,
                "count": count,
                "offset": offset
            }
            
            response = requests.post(mcp_endpoint, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error calling Brave Search MCP: {str(e)}")
            # Fallback to direct API if available
            if BRAVE_SEARCH_API_KEY:
                logger.info("Falling back to direct Brave Search API")
                return self._call_brave_search_api(query, count, offset)
            raise
    
    def _call_brave_search_api(self, query: str, count: int, offset: int) -> Dict[str, Any]:
        """
        Call the Brave Search API directly.
        
        Args:
            query (str): The search query
            count (int): Number of results to return
            offset (int): Starting offset for pagination
            
        Returns:
            Dict[str, Any]: The response from the API
        """
        if not BRAVE_SEARCH_API_KEY:
            raise ValueError("Brave Search API key not set")
        
        api_url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_SEARCH_API_KEY}
        params = {
            "q": query,
            "count": count,
            "offset": offset
        }
        
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def _format_results(self, response: Dict[str, Any]) -> str:
        """
        Format the search results in a readable format.
        
        Args:
            response (Dict[str, Any]): The response from the API
            
        Returns:
            str: Formatted search results
        """
        if not response or "results" not in response or not response["results"]:
            return "No search results found."
        
        results = response.get("results", [])
        formatted_results = "## Search Results\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "No Title")
            url = result.get("url", "")
            description = result.get("description", "No description available.")
            
            formatted_results += f"### {i}. {title}\n"
            formatted_results += f"URL: {url}\n"
            formatted_results += f"Description: {description}\n\n"
        
        return formatted_results 