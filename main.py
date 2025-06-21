#!/usr/bin/env python3
"""
Fixer: AI Repair Agent

A headless AI repair agent capable of troubleshooting technical issues
through voice commands, SMS, or CLI interfaces.

Usage:
    python main.py --cli                # Run in CLI mode
    python main.py --voice              # Run in voice mode with traditional speech recognition
    python main.py --voice-live         # Run in voice mode with Gemini Live API (real-time)
    python main.py --voice-live-screen  # Run in voice mode with Gemini Live API and screen sharing
    python main.py --vision-live        # Run in vision mode with Gemini Live API and webcam
    python main.py --vision-live-screen # Run in vision mode with Gemini Live API and screen sharing
    python main.py --sms-daemon         # Run as SMS daemon
"""

import argparse
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import handlers
from handlers import cli_handler, voice_handler, sms_handler, vision_handler
from utils import config, logger

def main():
    """Main entry point for the Fixer AI repair agent."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Fixer: AI Repair Agent")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--cli", action="store_true", help="Run in CLI mode")
    mode_group.add_argument("--voice", action="store_true", help="Run in voice mode with traditional speech recognition")
    mode_group.add_argument("--voice-live", action="store_true", help="Run in voice mode with Gemini Live API and webcam")
    mode_group.add_argument("--voice-live-screen", action="store_true", help="Run in voice mode with Gemini Live API and screen sharing")
    mode_group.add_argument("--voice-live-none", action="store_true", help="Run in voice mode with Gemini Live API without visuals")
    mode_group.add_argument("--vision-live", action="store_true", help="Run in vision mode with Gemini Live API and webcam")
    mode_group.add_argument("--vision-live-screen", action="store_true", help="Run in vision mode with Gemini Live API and screen sharing")
    mode_group.add_argument("--vision-live-none", action="store_true", help="Run in vision mode with Gemini Live API without visuals")
    mode_group.add_argument("--sms-daemon", action="store_true", help="Run as SMS daemon")
    
    # Additional arguments
    parser.add_argument("--prompt", type=str, help="Initial prompt to send to the model in Live API modes")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize logger
    log = logger.setup_logger()
    log.info("Starting Fixer AI Repair Agent")
    
    # Load configuration
    cfg = config.load_config()
    
    # Run in the appropriate mode
    try:
        if args.cli:
            log.info("Starting in CLI mode")
            cli_handler.run()
        elif args.voice:
            log.info("Starting in traditional voice mode")
            voice_handler.run(use_live_api=False)
        elif args.voice_live:
            log.info("Starting in voice mode with Gemini Live API and webcam")
            voice_handler.run(use_live_api=True, video_mode="camera")
        elif args.voice_live_screen:
            log.info("Starting in voice mode with Gemini Live API and screen sharing")
            voice_handler.run(use_live_api=True, video_mode="screen")
        elif args.voice_live_none:
            log.info("Starting in voice mode with Gemini Live API without visuals")
            voice_handler.run(use_live_api=True, video_mode="none")
        elif args.vision_live:
            log.info("Starting in vision mode with Gemini Live API and webcam")
            vision_handler.run_chat(prompt=args.prompt)
        elif args.vision_live_screen:
            log.info("Starting in vision mode with Gemini Live API and screen sharing")
            vision_handler.run_chat(prompt=args.prompt)
        elif args.vision_live_none:
            log.info("Starting in vision mode with Gemini Live API without visuals")
            vision_handler.run_chat(prompt=args.prompt)
        elif args.sms_daemon:
            log.info("Starting SMS daemon")
            sms_handler.run()
    except KeyboardInterrupt:
        log.info("Shutting down Fixer AI Repair Agent")
        sys.exit(0)
    except Exception as e:
        log.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()