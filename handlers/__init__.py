#!/usr/bin/env python3
"""
Fixer AI Handlers Package

Provides various interface handlers for the Fixer AI repair agent:
- CLI Handler: Terminal-based interaction
- Voice Handler: Speech recognition and synthesis
- Vision Handler: Image capture and analysis
- SMS Handler: Text message interaction
- Gemini Handler: Google Gemini AI integration
"""

from . import cli_handler
from . import voice_handler
from . import vision_handler
from . import sms_handler
from . import gemini_handler

__all__ = [
    'cli_handler',
    'voice_handler',
    'vision_handler',
    'sms_handler',
    'gemini_handler',
]