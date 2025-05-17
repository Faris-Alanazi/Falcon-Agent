import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.config.config import LOG_LEVEL, LOG_FILE

def setup_logger(name, log_level=None, log_file=None):
    """
    Set up a logger with console and file handlers.
    
    Args:
        name (str): Name of the logger
        log_level (str, optional): Logging level. Defaults to value in config.
        log_file (str, optional): Path to log file. Defaults to value in config.
        
    Returns:
        logging.Logger: Configured logger
    """
    # Use default config values if not specified
    if log_level is None:
        log_level = LOG_LEVEL
    if log_file is None:
        log_file = LOG_FILE
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    
    # Create file handler
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB with 5 backups
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.addHandler(console_handler)
        logger.error(f"Failed to create file handler: {e}")
    
    return logger 