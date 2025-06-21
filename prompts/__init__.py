#!/usr/bin/env python3
"""
Prompt Templates Module for Fixer AI

Provides functions to load prompt templates from the prompts directory.
Templates are organized by category (diagnose, scripts) and use case.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from utils import logger

# Initialize logger
log = logger.get_logger(__name__)

# Base directory for prompt templates
PROMPTS_DIR = Path(__file__).parent

# Categories
DIAGNOSE_DIR = PROMPTS_DIR / "diagnose"
SCRIPTS_DIR = PROMPTS_DIR / "scripts"

def load_prompt(template_path: str) -> Optional[str]:
    """Load a prompt template from the specified path.
    
    Args:
        template_path: Path to the prompt template file
        
    Returns:
        The prompt template as a string, or None if the file doesn't exist
    """
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        log.error(f"Prompt template not found: {template_path}")
        return None
    except Exception as e:
        log.error(f"Error loading prompt template {template_path}: {e}")
        return None

def get_diagnostic_prompt(mode: str = "general") -> Optional[str]:
    """Get a diagnostic prompt template.
    
    Args:
        mode: The type of diagnostic prompt ('general' or 'technical')
        
    Returns:
        The prompt template as a string, or None if not found
    """
    valid_modes = ["general", "technical"]
    if mode not in valid_modes:
        log.warning(f"Invalid diagnostic mode: {mode}. Using 'general' instead.")
        mode = "general"
    
    template_path = DIAGNOSE_DIR / f"{mode}.txt"
    return load_prompt(str(template_path))

def get_script_prompt(os_type: str) -> Optional[str]:
    """Get a script generation prompt template for the specified OS.
    
    Args:
        os_type: The operating system type ('windows', 'linux', or 'macos')
        
    Returns:
        The prompt template as a string, or None if not found
    """
    valid_os_types = ["windows", "linux", "macos"]
    if os_type.lower() not in valid_os_types:
        log.warning(f"Invalid OS type: {os_type}. Using 'windows' instead.")
        os_type = "windows"
    
    template_path = SCRIPTS_DIR / f"{os_type.lower()}.txt"
    return load_prompt(str(template_path))

# Ensure all prompt directories exist
os.makedirs(DIAGNOSE_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
