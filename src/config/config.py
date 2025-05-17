"""
Configuration module for Falcon Agent system.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration manager for the Falcon Agent system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration with values from YAML file and environment.
        
        Args:
            config_path: Path to the YAML configuration file.
                         If None, default to config/config.yaml.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            "config.yaml"
        )
        self.config = self._load_config()
        
        # Ensure required directories exist
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file and override with environment variables.
        
        Returns:
            Dict containing configuration values.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    config = yaml.safe_load(file) or {}
            else:
                logger.warning(f"Config file {self.config_path} not found. Using default values.")
                config = {}
            
            # Override with environment variables
            self._override_from_env(config)
            
            # Set default values if not specified
            self._set_defaults(config)
            
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return self._set_defaults({})
    
    def _override_from_env(self, config: Dict[str, Any]) -> None:
        """
        Override configuration values with environment variables.
        
        Args:
            config: Configuration dictionary to update.
        """
        # AI Model settings
        config['ai'] = config.get('ai', {})
        config['ai']['model'] = os.environ.get('FALCON_AI_MODEL', config['ai'].get('model'))
        config['ai']['api_key'] = os.environ.get('FALCON_AI_API_KEY', config['ai'].get('api_key'))
        
        # CrewAI settings
        config['crewai'] = config.get('crewai', {})
        config['crewai']['sequential'] = os.environ.get('FALCON_CREWAI_SEQUENTIAL', 
                                                        config['crewai'].get('sequential', 'True')).lower() == 'true'
        
        # Logging settings
        config['logging'] = config.get('logging', {})
        config['logging']['level'] = os.environ.get('FALCON_LOGGING_LEVEL', 
                                                   config['logging'].get('level', 'INFO'))
        
        # File System settings
        config['file_system'] = config.get('file_system', {})
        config['file_system']['base_dir'] = os.environ.get('FALCON_FILE_SYSTEM_BASE_DIR', 
                                                          config['file_system'].get('base_dir', 'data'))
        
        # Web Interface settings
        config['web'] = config.get('web', {})
        config['web']['port'] = int(os.environ.get('FALCON_WEB_PORT', 
                                                 config['web'].get('port', 5000)))
        
        # Ollama settings
        config['ollama'] = config.get('ollama', {})
        config['ollama']['enabled'] = os.environ.get('FALCON_OLLAMA_ENABLED', 
                                                    config['ollama'].get('enabled', 'True')).lower() == 'true'
        config['ollama']['model'] = os.environ.get('FALCON_OLLAMA_MODEL', 
                                                  config['ollama'].get('model', 'qwen3:8b'))
        config['ollama']['server_url'] = os.environ.get('FALCON_OLLAMA_SERVER_URL', 
                                                       config['ollama'].get('server_url', 'http://localhost:11434'))
        
        # MCP settings
        config['mcp'] = config.get('mcp', {})
        config['mcp']['enabled'] = os.environ.get('FALCON_MCP_ENABLED', 
                                                 config['mcp'].get('enabled', 'True')).lower() == 'true'
        
        # Brave Search MCP settings
        config['mcp']['brave_search'] = config['mcp'].get('brave_search', {})
        config['mcp']['brave_search']['enabled'] = os.environ.get('FALCON_MCP_BRAVE_SEARCH_ENABLED', 
                                                                config['mcp']['brave_search'].get('enabled', 'True')).lower() == 'true'
        config['mcp']['brave_search']['api_key'] = os.environ.get('FALCON_MCP_BRAVE_SEARCH_API_KEY', 
                                                                 config['mcp']['brave_search'].get('api_key', ''))
        
        # Sequential Thinking MCP settings
        config['mcp']['sequential_thinking'] = config['mcp'].get('sequential_thinking', {})
        config['mcp']['sequential_thinking']['enabled'] = os.environ.get('FALCON_MCP_SEQUENTIAL_THINKING_ENABLED', 
                                                                        config['mcp']['sequential_thinking'].get('enabled', 'True')).lower() == 'true'
        
        # Context7 MCP settings
        config['mcp']['context7'] = config['mcp'].get('context7', {})
        config['mcp']['context7']['enabled'] = os.environ.get('FALCON_MCP_CONTEXT7_ENABLED', 
                                                            config['mcp']['context7'].get('enabled', 'True')).lower() == 'true'
    
    def _set_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default values for configuration.
        
        Args:
            config: Configuration dictionary to update.
            
        Returns:
            Updated configuration dictionary.
        """
        # AI Model defaults
        config.setdefault('ai', {})
        config['ai'].setdefault('model', 'qwen3:8b')
        config['ai'].setdefault('api_key', '')
        
        # CrewAI defaults
        config.setdefault('crewai', {})
        config['crewai'].setdefault('sequential', True)
        
        # Logging defaults
        config.setdefault('logging', {})
        config['logging'].setdefault('level', 'INFO')
        config['logging'].setdefault('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File System defaults
        config.setdefault('file_system', {})
        config['file_system'].setdefault('base_dir', 'data')
        config['file_system'].setdefault('lock_timeout', 30)  # seconds
        
        # Memory defaults
        config.setdefault('memory', {})
        config['memory'].setdefault('short_term_capacity', 100)
        config['memory'].setdefault('long_term_enabled', True)
        
        # Agent defaults
        config.setdefault('agents', {})
        config['agents'].setdefault('max_concurrent_tasks', 2)
        
        # Web Interface defaults
        config.setdefault('web', {})
        config['web'].setdefault('enabled', True)
        config['web'].setdefault('port', 5000)
        config['web'].setdefault('host', '0.0.0.0')
        
        # Ollama defaults
        config.setdefault('ollama', {})
        config['ollama'].setdefault('enabled', True)
        config['ollama'].setdefault('model', 'qwen3:8b')
        config['ollama'].setdefault('server_url', 'http://localhost:11434')
        
        # MCP defaults
        config.setdefault('mcp', {})
        config['mcp'].setdefault('enabled', True)
        
        # Brave Search MCP defaults
        config['mcp'].setdefault('brave_search', {})
        config['mcp']['brave_search'].setdefault('enabled', True)
        config['mcp']['brave_search'].setdefault('api_key', '')
        
        # Sequential Thinking MCP defaults
        config['mcp'].setdefault('sequential_thinking', {})
        config['mcp']['sequential_thinking'].setdefault('enabled', True)
        
        # Context7 MCP defaults
        config['mcp'].setdefault('context7', {})
        config['mcp']['context7'].setdefault('enabled', True)
        
        return config
    
    def _ensure_directories(self) -> None:
        """Ensure that required directories exist."""
        base_dir = self.config['file_system']['base_dir']
        
        # Create base directory if it doesn't exist
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            logger.info(f"Created base directory: {base_dir}")
        
        # Create subdirectories for different data types
        subdirs = [
            'prd',         # For Product Requirement Documents
            'logs',        # For log files
            'memory',      # For persistent memory storage
            'tasks',       # For task storage and tracking
            'artifacts',   # For generated artifacts
            'models',      # For model data and checkpoints
        ]
        
        for subdir in subdirs:
            dir_path = os.path.join(base_dir, subdir)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key, can be nested using dot notation (e.g., 'ai.model').
            default: Default value to return if key is not found.
            
        Returns:
            The configuration value or default.
        """
        parts = key.split('.')
        value = self.config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")


# Create a global instance of Config
config = Config() 