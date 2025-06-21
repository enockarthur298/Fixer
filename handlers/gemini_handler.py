#!/usr/bin/env python3
"""
Gemini Handler for Fixer AI

Handles interactions with the Gemini 2.0 Flash Live model for multimodal processing.
Supports text, image, and audio inputs for comprehensive troubleshooting.
"""

import os
import json
import base64
from typing import Dict, List, Optional, Union, Any

import google.generativeai as genai
from PIL import Image

from utils import config, logger

# Initialize logger
log = logger.get_logger(__name__)

# Initialize Gemini client
def init_gemini():
    """Initialize the Gemini client with API key from config."""
    api_key = config.get_config("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in configuration")
    
    genai.configure(api_key=api_key)
    log.info("Gemini API initialized successfully")
    
    return genai

# Model configuration
MODEL_NAME = "gemini-2.5-flash"  # Using the Live model for multimodal capabilities

# Function to process text input
def process_text(text: str) -> Dict[str, Any]:
    """Process text input with Gemini model.
    
    Args:
        text: The text input from the user
        
    Returns:
        Dict containing the structured response
    """
    try:
        # Initialize Gemini
        genai_client = init_gemini()
        model = genai_client.GenerativeModel(MODEL_NAME)
        
        # Create prompt with system instructions
        system_prompt = _load_prompt_template("diagnose/general.txt")
        
        # Generate response
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [system_prompt]},
                {"role": "user", "parts": [text]}
            ],
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "response_mime_type": "application/json",
            }
        )
        
        # Parse the response
        result = _parse_response(response)
        log.info(f"Successfully processed text input")
        return result
    
    except Exception as e:
        log.error(f"Error processing text input: {e}")
        return {"error": str(e), "cause": "Unknown issue", "steps": ["Error processing your request"]}

# Function to process multimodal input (text + image)
def process_multimodal(text: str, image_path: str) -> Dict[str, Any]:
    """Process text and image input with Gemini model.
    
    Args:
        text: The text input from the user
        image_path: Path to the image file
        
    Returns:
        Dict containing the structured response
    """
    try:
        # Initialize Gemini
        genai_client = init_gemini()
        model = genai_client.GenerativeModel(MODEL_NAME)
        
        # Load image
        image = Image.open(image_path)
        
        # Create prompt with system instructions
        system_prompt = _load_prompt_template("diagnose/technical.txt")
        
        # Generate response
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [system_prompt]},
                {"role": "user", "parts": [
                    {"text": text},
                    {"inline_data": {
                        "mime_type": "image/jpeg",
                        "data": _encode_image(image_path)
                    }}
                ]}
            ],
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "response_mime_type": "application/json",
            }
        )
        
        # Parse the response
        result = _parse_response(response)
        log.info(f"Successfully processed multimodal input")
        return result
    
    except Exception as e:
        log.error(f"Error processing multimodal input: {e}")
        return {"error": str(e), "cause": "Unknown issue", "steps": ["Error processing your request"]}

# Helper function to encode image to base64
def _encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Helper function to load prompt template
def _load_prompt_template(template_path: str) -> str:
    """Load prompt template from file."""
    try:
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", template_path)
        with open(full_path, "r") as f:
            return f.read()
    except Exception as e:
        log.error(f"Error loading prompt template {template_path}: {e}")
        return """You are Fixer, an AI repair agent that helps troubleshoot technical issues.
                Please analyze the problem and provide a structured response with:
                - The likely cause of the issue
                - Step-by-step instructions to fix it
                - Any scripts that might help resolve the problem"""

# Helper function to parse Gemini response
def _parse_response(response) -> Dict[str, Any]:
    """Parse the response from Gemini into a structured format."""
    try:
        # Try to parse as JSON first
        text_response = response.text
        try:
            parsed = json.loads(text_response)
            return parsed
        except json.JSONDecodeError:
            # If not valid JSON, extract structured information from text
            lines = text_response.split("\n")
            cause = ""
            steps = []
            script = ""
            
            # Simple parsing logic
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if "cause:" in line.lower() or "diagnosis:" in line.lower():
                    current_section = "cause"
                    cause = line.split(":", 1)[1].strip() if ":" in line else ""
                elif "steps:" in line.lower() or "instructions:" in line.lower():
                    current_section = "steps"
                elif "script:" in line.lower() or "code:" in line.lower():
                    current_section = "script"
                elif current_section == "cause":
                    cause += " " + line
                elif current_section == "steps" and line.startswith(("-", "*", "1.", "2.", "3.")):
                    steps.append(line.lstrip("-*0123456789. "))
                elif current_section == "script":
                    script += line + "\n"
            
            return {
                "cause": cause.strip(),
                "steps": steps,
                "script": script.strip()
            }
    
    except Exception as e:
        log.error(f"Error parsing Gemini response: {e}")
        return {"cause": "Unknown issue", "steps": ["Error processing the response"], "script": ""}

# Function to generate repair script
def generate_script(issue_description: str, os_type: str = "windows") -> str:
    """Generate a repair script for the given issue.
    
    Args:
        issue_description: Description of the issue to fix
        os_type: Operating system type (windows, linux, macos)
        
    Returns:
        String containing the generated script
    """
    try:
        # Initialize Gemini
        genai_client = init_gemini()
        model = genai_client.GenerativeModel(MODEL_NAME)
        
        # Load script prompt template
        script_prompt = _load_prompt_template(f"scripts/{os_type}.txt")
        
        # Generate script
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [script_prompt]},
                {"role": "user", "parts": [f"Issue: {issue_description}"]}
            ],
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
            }
        )
        
        script = response.text
        log.info(f"Successfully generated script for {os_type}")
        return script
    
    except Exception as e:
        log.error(f"Error generating script: {e}")
        return f"# Error generating script: {str(e)}"
