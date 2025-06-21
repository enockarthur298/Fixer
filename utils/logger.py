#!/usr/bin/env python3
"""
Logger for Fixer AI

Provides centralized logging functionality for the entire application.
Configures loggers with appropriate handlers and formatters.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

from loguru import logger

from utils import config

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Default log file path
DEFAULT_LOG_FILE = str(logs_dir / "fixer.log")

# Configure Loguru logger
def setup_logger(log_file: Optional[str] = None, log_level: str = "INFO") -> logger:
    """Set up and configure the logger.
    
    Args:
        log_file: Path to the log file (default: from config or DEFAULT_LOG_FILE)
        log_level: Logging level (default: from config or INFO)
        
    Returns:
        Configured logger instance
    """
    # Remove default handlers
    logger.remove()
    
    # Get configuration
    if log_file is None:
        log_file = config.get_config("LOG_FILE", DEFAULT_LOG_FILE)
    
    if log_level is None:
        log_level = config.get_config("LOG_LEVEL", "INFO")
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Add file handler
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",  # Rotate when file reaches 10 MB
        retention="1 week",  # Keep logs for 1 week
        compression="zip"  # Compress rotated logs
    )
    
    logger.info(f"Logger initialized with level {log_level}, logging to {log_file}")
    
    return logger

def get_logger(name: str) -> logger:
    """Get a logger for a specific module.
    
    Args:
        name: Name of the module (usually __name__)
        
    Returns:
        Logger instance with the specified name
    """
    return logger.bind(name=name)

# Initialize the logger when the module is imported
_default_logger = setup_logger()

if __name__ == "__main__":
    # Test the logger
    test_logger = get_logger("logger_test")
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
