#!/usr/bin/env python3
"""
Configuration Handler for Fixer AI

Loads and manages configuration settings from environment variables and .env files.
Provides a centralized way to access configuration values across the application.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union

from dotenv import load_dotenv

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration values
DEFAULT_CONFIG = {
    # API Keys
    "GEMINI_API_KEY": "",
    "TWILIO_ACCOUNT_SID": "",
    "TWILIO_AUTH_TOKEN": "",
    "TWILIO_PHONE_NUMBER": "",
    
    # Server settings
    "SMS_SERVER_HOST": "0.0.0.0",
    "SMS_SERVER_PORT": "8000",
    
    # Voice settings
    "VOICE_RATE": "175",  # Speech rate
    "VOICE_VOLUME": "0.9",  # Volume (0.0 to 1.0)
    
    # Logging settings
    "LOG_LEVEL": "INFO",
    "LOG_FILE": str(Path(PROJECT_ROOT, "logs", "fixer.log")),
    
    # Temp directory for files
    "TEMP_DIR": os.path.join(os.path.expanduser("~"), "fixer_ai_temp"),
    
    # Script execution settings
    "SCRIPT_TIMEOUT": "30",  # Seconds
}

# Global config cache
_config_cache: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    """Load configuration from .env file and environment variables.
    
    Returns:
        Dict containing all configuration values
    """
    global _config_cache
    
    # If config is already loaded, return the cached version
    if _config_cache:
        return _config_cache
    
    # Load .env file if it exists
    env_path = Path(PROJECT_ROOT, ".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    for key in config.keys():
        env_value = os.environ.get(key)
        if env_value is not None:
            config[key] = env_value
    
    # Cache the config
    _config_cache = config
    
    return config

def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value by key.
    
    Args:
        key: The configuration key to look up
        default: Default value if key is not found
        
    Returns:
        The configuration value or default if not found
    """
    config = load_config()
    return config.get(key, default)

def set_config(key: str, value: Any) -> None:
    """Set a configuration value (in memory only, not persisted).
    
    Args:
        key: The configuration key to set
        value: The value to set
    """
    global _config_cache
    
    # Load config if not already loaded
    if not _config_cache:
        load_config()
    
    # Update the value
    _config_cache[key] = value

def create_env_example() -> None:
    """Create a .env.example file with all required configuration keys."""
    env_example_path = Path(PROJECT_ROOT, ".env.example")
    
    with open(env_example_path, "w") as f:
        f.write("# Fixer AI Configuration\n\n")
        
        # Write each config key with a description
        f.write("# API Keys\n")
        f.write("GEMINI_API_KEY=your_gemini_api_key_here  # Required for AI functionality\n")
        f.write("TWILIO_ACCOUNT_SID=your_twilio_sid_here  # Required for SMS functionality\n")
        f.write("TWILIO_AUTH_TOKEN=your_twilio_token_here  # Required for SMS functionality\n")
        f.write("TWILIO_PHONE_NUMBER=your_twilio_phone_number  # Required for SMS functionality\n\n")
        
        f.write("# Server settings\n")
        f.write("SMS_SERVER_HOST=0.0.0.0  # Host to bind the SMS server to\n")
        f.write("SMS_SERVER_PORT=8000  # Port to bind the SMS server to\n\n")
        
        f.write("# Voice settings\n")
        f.write("VOICE_RATE=175  # Speech rate\n")
        f.write("VOICE_VOLUME=0.9  # Volume (0.0 to 1.0)\n\n")
        
        f.write("# Logging settings\n")
        f.write("LOG_LEVEL=INFO  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)\n")
        f.write(f"LOG_FILE={DEFAULT_CONFIG['LOG_FILE']}  # Path to log file\n\n")
        
        f.write("# Temp directory for files\n")
        f.write(f"TEMP_DIR={DEFAULT_CONFIG['TEMP_DIR']}  # Directory for temporary files\n\n")
        
        f.write("# Script execution settings\n")
        f.write("SCRIPT_TIMEOUT=30  # Maximum execution time for scripts in seconds\n")

if __name__ == "__main__":
    # Create .env.example file when run directly
    create_env_example()
    print("Created .env.example file")
