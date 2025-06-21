#!/usr/bin/env python3
"""
Vision Handler for Fixer AI

Captures images from webcam or screenshots for multimodal processing.
Prepares images for use with the Gemini Vision API.
Supports real-time video streaming with Gemini 2.0 Flash Live API.
"""

import os
import time
import tempfile
import asyncio
import base64
import io
import traceback
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union

import cv2
import numpy as np
import PIL.Image
import mss
import mss.tools
import pyaudio

import google.generativeai as genai
from google.generativeai import types

from utils import logger, config

# Initialize logger
log = logger.get_logger(__name__)

# Create temp directory for images if it doesn't exist
TEMP_DIR = os.path.join(tempfile.gettempdir(), "fixer_ai")
os.makedirs(TEMP_DIR, exist_ok=True)

# Audio constants for Gemini Live API
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

# Gemini model name for Live API
MODEL = "gemini-2.5-flash"

# Default video mode
DEFAULT_VIDEO_MODE = "camera"

# Initialize PyAudio
pya = pyaudio.PyAudio()

# Initialize Gemini client
api_key = config.get_config("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in configuration")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(MODEL)

# Chat configuration
CHAT_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "automatic_function_calling": {"disable": True},
    "max_output_tokens": 8192,
    "response_modalities": ["text", "audio"],
    "safety_settings": [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
}

def capture_screenshot() -> Optional[str]:
    """Capture a screenshot of the primary monitor.
    
    Returns:
        Path to the saved screenshot or None if failed
    """
    try:
        timestamp = int(time.time())
        output_path = os.path.join(TEMP_DIR, f"screenshot_{timestamp}.png")
        
        with mss.mss() as sct:
            # Capture the primary monitor
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            
            # Save the screenshot
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)
            
            log.info(f"Screenshot captured and saved to {output_path}")
            return output_path
    
    except Exception as e:
        log.error(f"Error capturing screenshot: {e}")
        return None

def capture_webcam(camera_id: int = 0) -> Optional[str]:
    """Capture an image from the webcam.
    
    Args:
        camera_id: ID of the camera to use (default: 0 for primary camera)
        
    Returns:
        Path to the saved webcam image or None if failed
    """
    try:
        # Initialize webcam
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            log.error(f"Could not open camera {camera_id}")
            return None
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Allow camera to initialize
        time.sleep(0.5)
        
        # Capture frame
        ret, frame = cap.read()
        
        if not ret:
            log.error("Failed to capture image from webcam")
            cap.release()
            return None
        
        # Save the image
        timestamp = int(time.time())
        output_path = os.path.join(TEMP_DIR, f"webcam_{timestamp}.jpg")
        cv2.imwrite(output_path, frame)
        
        # Release the camera
        cap.release()
        
        log.info(f"Webcam image captured and saved to {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Error capturing webcam image: {e}")
        return None

def process_image(image_path: str, max_size: int = 1024) -> Optional[str]:
    """Process an image for use with Gemini Vision API.
    
    Args:
        image_path: Path to the image file
        max_size: Maximum dimension (width or height) for the processed image
        
    Returns:
        Path to the processed image or None if failed
    """
    try:
        # Open the image
        image = PIL.Image.open(image_path)
        
        # Resize if needed while maintaining aspect ratio
        width, height = image.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.resize((new_width, new_height), PIL.Image.LANCZOS)
        
        # Create output path
        filename = os.path.basename(image_path)
        processed_path = os.path.join(TEMP_DIR, f"processed_{filename}")
        
        # Save the processed image
        image.save(processed_path, quality=85, optimize=True)
        
        log.info(f"Image processed and saved to {processed_path}")
        return processed_path
    
    except Exception as e:
        log.error(f"Error processing image: {e}")
        return None

def cleanup_old_images(max_age_hours: int = 24) -> None:
    """Clean up old images from the temp directory.
    
    Args:
        max_age_hours: Maximum age of images to keep in hours
    """
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in Path(TEMP_DIR).glob("*.*"):
            if file_path.is_file():
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    log.info(f"Removed old image: {file_path}")
    
    except Exception as e:
        log.error(f"Error cleaning up old images: {e}")

# Example usage function
def capture_device_image(use_webcam: bool = False) -> Optional[str]:
    """Capture an image from either webcam or screenshot based on preference.
    
    Args:
        use_webcam: If True, capture from webcam; otherwise capture screenshot
        
    Returns:
        Path to the processed image or None if failed
    """
    try:
        # Capture image
        if use_webcam:
            raw_image_path = capture_webcam()
        else:
            raw_image_path = capture_screenshot()
        
        if not raw_image_path:
            return None
        
        # Process the image
        processed_image_path = process_image(raw_image_path)
        
        # Clean up old images
        cleanup_old_images()
        
        return processed_image_path
    
    except Exception as e:
        log.error(f"Error capturing device image: {e}")
        return None


class ChatLoop:
    """Handles chat functionality with Gemini API.
    
    This class manages the chat interaction with the Gemini API.
    """
    
    def __init__(self, prompt: str = None, client=None):
        """Initialize the ChatLoop.
        
        Args:
            prompt: Optional initial prompt to send to the model
            client: The Gemini API client instance
        """
        self.prompt = prompt
        self.session = None
        self.client = client or genai
        
        log.info(f"Initialized ChatLoop")
    
    async def send_text(self):
        """Send text input to the model."""
        # Send initial prompt if provided
        if self.prompt:
            log.info(f"Sending initial prompt: {self.prompt}")
            response = await asyncio.to_thread(self.session.send_message, self.prompt)
            print(f"\nFixer AI: {response.text}", end="")
            log.info(f"Model response: {response.text}")
        
        while True:
            try:
                text = await asyncio.to_thread(input, "Fixer AI > ")
                if text.lower() in ["q", "quit", "exit"]:
                    log.info("User requested to exit")
                    break
                
                log.info(f"Sending user input: {text}")
                response = await asyncio.to_thread(self.session.send_message, text or ".")
                print(f"\nFixer AI: {response.text}", end="")
                log.info(f"Model response: {response.text}")
            except Exception as e:
                log.error(f"Error sending text: {e}")
                break
    
    async def receive_text(self):
        """Receive text responses from the model."""
        # Since send_text handles both sending and receiving responses,
        # this method can be a no-op or used for additional logic if needed
        while True:
            await asyncio.sleep(1)  # Keep the coroutine alive
            # In a real async API, this would handle streaming responses
            # For now, responses are handled in send_text
    
    async def run(self):
        """Run the ChatLoop."""
        log.info(f"Starting ChatLoop")
        
        try:
            # Start the chat session synchronously but wrapped in asyncio.to_thread
            self.session = await asyncio.to_thread(self.client.start_chat)
            await asyncio.gather(self.send_text(), self.receive_text())
        except Exception as e:
            log.error(f"Error in ChatLoop: {e}")
            traceback.print_exception(e)
        finally:
            log.info("ChatLoop shutdown complete")


def run_chat(prompt: str = None) -> None:
    """Run the ChatLoop with the specified prompt.
    
    Args:
        prompt: Optional initial prompt to send to the model
    """
    log.info(f"Starting chat")
    loop = ChatLoop(prompt=prompt, client=model)
    asyncio.run(loop.run())
