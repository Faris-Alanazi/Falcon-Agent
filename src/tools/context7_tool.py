import os
import json
import requests
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, Field

from crewai.tools import BaseTool
from src.config.config import CONTEXT7_MCP_URL
from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class Context7Input(BaseModel):
    """Input for the Context7 Tool."""
    library_name: str = Field(..., description="The name of the library to get documentation for.")
    topic: str = Field("", description="Specific topic or function to focus on (optional).")
    tokens: int = Field(5000, description="Maximum number of tokens to retrieve.")

class Context7Tool(BaseTool):
    """
    Tool to retrieve programming documentation using the Context7 MCP server.
    """
    
    name: str = "context7_docs"
    description: str = "Retrieve documentation for programming libraries, frameworks, and functions."
    args_schema: Type[BaseModel] = Context7Input
    
    def _run(self, library_name: str, topic: str = "", tokens: int = 5000) -> str:
        """
        Retrieve programming documentation.
        
        Args:
            library_name (str): The name of the library
            topic (str): Specific topic or function to focus on
            tokens (int): Maximum number of tokens to retrieve
            
        Returns:
            str: The documentation content
        """
        try:
            # Ensure valid parameter values
            tokens = min(max(tokens, 1000), 10000)  # between 1000 and 10000
            
            # Resolve the library ID first
            library_id = self._resolve_library_id(library_name)
            if not library_id:
                return f"Could not find documentation for library: {library_name}"
            
            # Retrieve the documentation
            response = self._get_library_docs(library_id, topic, tokens)
            
            # Format the results
            formatted_results = self._format_results(response, library_name)
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving documentation: {str(e)}")
            return f"Error retrieving documentation: {str(e)}"
    
    def _resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        Resolve a library name to a Context7-compatible library ID.
        
        Args:
            library_name (str): The library name to resolve
            
        Returns:
            Optional[str]: The resolved library ID or None if not found
        """
        try:
            mcp_endpoint = f"{CONTEXT7_MCP_URL}/resolve-library-id"
            payload = {
                "libraryName": library_name
            }
            
            response = requests.post(mcp_endpoint, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract the library ID from the response
            if "libraries" in data and data["libraries"]:
                # Return the first match
                return data["libraries"][0]["context7CompatibleLibraryID"]
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error resolving library ID: {str(e)}")
            return None
    
    def _get_library_docs(self, library_id: str, topic: str, tokens: int) -> Dict[str, Any]:
        """
        Retrieve documentation for a library.
        
        Args:
            library_id (str): The Context7-compatible library ID
            topic (str): Specific topic or function to focus on
            tokens (int): Maximum number of tokens to retrieve
            
        Returns:
            Dict[str, Any]: The documentation data
        """
        try:
            mcp_endpoint = f"{CONTEXT7_MCP_URL}/get-library-docs"
            payload = {
                "context7CompatibleLibraryID": library_id,
                "tokens": tokens
            }
            
            if topic:
                payload["topic"] = topic
            
            response = requests.post(mcp_endpoint, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving library docs: {str(e)}")
            # Return an empty response
            return {
                "library_id": library_id,
                "topic": topic,
                "sections": [],
                "error": str(e)
            }
    
    def _format_results(self, response: Dict[str, Any], library_name: str) -> str:
        """
        Format the documentation results in a readable format.
        
        Args:
            response (Dict[str, Any]): The response from the MCP
            library_name (str): The original library name
            
        Returns:
            str: Formatted documentation
        """
        if "error" in response and response["error"]:
            return f"Error retrieving documentation for {library_name}: {response['error']}"
        
        if not response or "sections" not in response or not response["sections"]:
            return f"No documentation found for {library_name}."
        
        sections = response.get("sections", [])
        
        formatted_results = f"## Documentation for {library_name}\n\n"
        
        for section in sections:
            title = section.get("title", "Untitled Section")
            language = section.get("language", "")
            code = section.get("code", "")
            description = section.get("description", "")
            source = section.get("source", "")
            
            formatted_results += f"### {title}\n"
            
            if description:
                formatted_results += f"{description}\n\n"
            
            if source:
                formatted_results += f"Source: {source}\n\n"
            
            if code:
                if language:
                    formatted_results += f"```{language}\n{code}\n```\n\n"
                else:
                    formatted_results += f"```\n{code}\n```\n\n"
            
            formatted_results += "---\n\n"
        
        return formatted_results 