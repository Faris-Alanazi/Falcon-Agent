"""
AI integration utilities for the Falcon Agent System.

This module provides integrations with various AI platforms including Ollama
for local LLM execution and MCP (Model Context Protocol) servers for enhanced
agent capabilities.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union

import requests
import ollama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class OllamaIntegration:
    """Interface for interacting with Ollama to run models locally."""
    
    def __init__(self, model_name: str = "qwen3:8b"):
        """
        Initialize the Ollama integration.
        
        Args:
            model_name: The name of the model to use. Defaults to "qwen3:8b".
        """
        self.model_name = model_name
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """
        Check if Ollama is available and the specified model exists.
        
        Returns:
            bool: True if Ollama is available and model exists, False otherwise.
        """
        try:
            # Check if Ollama server is running
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                logger.warning("Ollama server is not running. Please start it with 'ollama serve'")
                return False
            
            # Check if the model exists
            models = response.json().get("models", [])
            model_exists = any(model["name"] == self.model_name for model in models)
            
            if not model_exists:
                logger.info(f"Model {self.model_name} not found. Will pull when used.")
            
            return True
        except requests.RequestException:
            logger.warning("Could not connect to Ollama server. Make sure it's installed and running.")
            return False
    
    def pull_model(self) -> bool:
        """
        Pull the specified model to local storage.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info(f"Pulling model {self.model_name}...")
            ollama.pull(self.model_name)
            logger.info(f"Model {self.model_name} pulled successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {self.model_name}: {str(e)}")
            return False
    
    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a response using the Ollama model.
        
        Args:
            prompt: The user prompt
            system: Optional system message
            **kwargs: Additional parameters to pass to Ollama
            
        Returns:
            Dict containing the response
        """
        try:
            # Set default parameters if not provided
            params = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                    "top_k": kwargs.get("top_k", 40),
                }
            }
            
            # Add system message if provided
            if system:
                params["system"] = system
            
            # Generate response
            response = ollama.generate(**params)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {"error": str(e)}
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Have a chat conversation with the Ollama model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters to pass to Ollama
            
        Returns:
            Dict containing the response
        """
        try:
            # Set default parameters if not provided
            params = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                    "top_k": kwargs.get("top_k", 40),
                }
            }
            
            # Generate chat response
            response = ollama.chat(**params)
            return response
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return {"error": str(e)}


class MCPServerIntegration:
    """Interface for interacting with MCP servers."""
    
    def __init__(self):
        """Initialize the MCP server integration."""
        self.active_sessions = {}
    
    async def connect_to_server(self, server_name: str, command: str, args: List[str], 
                               env: Optional[Dict[str, str]] = None) -> Optional[ClientSession]:
        """
        Connect to an MCP server.
        
        Args:
            server_name: Name identifier for the server connection
            command: Command to execute the server
            args: Arguments to pass to the command
            env: Optional environment variables
            
        Returns:
            Optional ClientSession if successful, None otherwise
        """
        try:
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env
            )
            
            # Connect to the server
            stdio_transport = await stdio_client(server_params)
            read_stream, write_stream = stdio_transport
            
            # Create a session
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            
            # Store the session
            self.active_sessions[server_name] = session
            
            logger.info(f"Connected to MCP server: {server_name}")
            return session
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {str(e)}")
            return None
    
    async def connect_brave_search(self, api_key: str) -> Optional[ClientSession]:
        """
        Connect to the Brave Search MCP server.
        
        Args:
            api_key: Brave Search API key
            
        Returns:
            Optional ClientSession if successful, None otherwise
        """
        env = {"BRAVE_API_KEY": api_key}
        return await self.connect_to_server(
            server_name="brave-search",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env=env
        )
    
    async def connect_sequential_thinking(self) -> Optional[ClientSession]:
        """
        Connect to the Sequential Thinking MCP server.
        
        Returns:
            Optional ClientSession if successful, None otherwise
        """
        return await self.connect_to_server(
            server_name="sequential-thinking",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
        )
    
    async def connect_context7(self) -> Optional[ClientSession]:
        """
        Connect to the Context7 MCP server for documentation access.
        
        Returns:
            Optional ClientSession if successful, None otherwise
        """
        return await self.connect_to_server(
            server_name="context7",
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"]
        )
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        """
        Call a tool on an MCP server.
        
        Args:
            server_name: Name of the server to use
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Optional result if successful, None otherwise
        """
        session = self.active_sessions.get(server_name)
        if not session:
            logger.error(f"No active session for server: {server_name}")
            return None
        
        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on server {server_name}: {str(e)}")
            return None
    
    async def close_all_sessions(self):
        """Close all active MCP server sessions."""
        for server_name, session in self.active_sessions.items():
            try:
                await session.close()
                logger.info(f"Closed session for server: {server_name}")
            except Exception as e:
                logger.error(f"Error closing session for server {server_name}: {str(e)}")
        
        self.active_sessions = {} 