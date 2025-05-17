"""
Falcon Agent main module.

This is the entry point for the Falcon Agent system.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional

from src.config.config import config
from src.utils.logging_utils import setup_logging
from src.utils.ai_integration import OllamaIntegration, MCPServerIntegration
from src.utils.agent_manager import AgentManager

logger = logging.getLogger(__name__)

async def setup_mcp_servers(mcp_integration: MCPServerIntegration) -> bool:
    """
    Set up MCP servers based on configuration.
    
    Args:
        mcp_integration: The MCP server integration instance.
        
    Returns:
        bool: True if at least one server was set up successfully, False otherwise.
    """
    success = False
    
    # Set up Brave Search if enabled and API key is available
    if config.get('mcp.brave_search.enabled', True) and config.get('mcp.brave_search.api_key'):
        api_key = config.get('mcp.brave_search.api_key')
        session = await mcp_integration.connect_brave_search(api_key)
        if session:
            logger.info("Brave Search MCP server connected successfully")
            success = True
        else:
            logger.warning("Failed to connect to Brave Search MCP server")
    
    # Set up Sequential Thinking if enabled
    if config.get('mcp.sequential_thinking.enabled', True):
        session = await mcp_integration.connect_sequential_thinking()
        if session:
            logger.info("Sequential Thinking MCP server connected successfully")
            success = True
        else:
            logger.warning("Failed to connect to Sequential Thinking MCP server")
    
    # Set up Context7 if enabled
    if config.get('mcp.context7.enabled', True):
        session = await mcp_integration.connect_context7()
        if session:
            logger.info("Context7 MCP server connected successfully")
            success = True
        else:
            logger.warning("Failed to connect to Context7 MCP server")
    
    return success

async def main() -> None:
    """Main entry point for the Falcon Agent system."""
    # Setup logging
    setup_logging(level=config.get('logging.level', 'INFO'))
    logger.info("Starting Falcon Agent system")
    
    # Initialize Ollama integration if enabled
    ollama_integration = None
    if config.get('ollama.enabled', True):
        model_name = config.get('ollama.model', 'qwen3:8b')
        logger.info(f"Initializing Ollama with model: {model_name}")
        ollama_integration = OllamaIntegration(model_name)
        
        # Ensure model is available (will pull if needed)
        ollama_integration.pull_model()
    else:
        logger.info("Ollama integration is disabled")
    
    # Initialize MCP server integration if enabled
    mcp_integration = None
    if config.get('mcp.enabled', True):
        logger.info("Initializing MCP server integration")
        mcp_integration = MCPServerIntegration()
        
        # Set up MCP servers
        mcp_servers_ready = await setup_mcp_servers(mcp_integration)
        if not mcp_servers_ready:
            logger.warning("No MCP servers were successfully connected")
    else:
        logger.info("MCP server integration is disabled")
    
    # Initialize agent manager
    agent_manager = AgentManager(
        ollama_integration=ollama_integration,
        mcp_integration=mcp_integration
    )
    
    # Start the agent system
    try:
        await agent_manager.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
    finally:
        # Clean up
        if mcp_integration:
            await mcp_integration.close_all_sessions()
        logger.info("Falcon Agent system shutdown complete")

if __name__ == "__main__":
    asyncio.run(main()) 