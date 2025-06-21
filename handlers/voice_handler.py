#!/usr/bin/env python3
"""
Voice Handler for Fixer AI

Manages speech recognition and text-to-speech capabilities.
Enables voice interaction with the Fixer AI agent.
Supports both traditional speech recognition and Gemini 2.0 Flash Live API for real-time audio processing.
"""

import os
import time
import tempfile
import asyncio
import base64
import io
import traceback
from typing import Optional, Tuple, List, Dict, Any, Union

# Traditional speech recognition
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import threading

# Gemini Live API requirements
import cv2
import pyaudio
import PIL.Image
import mss
import google.generativeai as genai
from google.genai import types

try:
    from google.genai.types import LiveConnectConfig, SpeechConfig, VoiceConfig, PrebuiltVoiceConfig
except ImportError:
    log.warning("Live API types not found in library. Live audio features may not work.")
    LiveConnectConfig = None
    SpeechConfig = None
    VoiceConfig = None
    PrebuiltVoiceConfig = None

from utils import logger, config
from handlers import gemini_handler, vision_handler

# Initialize logger
log = logger.get_logger(__name__)

# Create temp directory for audio files if it doesn't exist
TEMP_DIR = config.get_config("TEMP_DIR", os.path.join(tempfile.gettempdir(), "fixer_ai"))
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize speech recognizer for traditional mode
recognizer = sr.Recognizer()

# Initialize TTS engine for traditional mode
tts_engine = pyttsx3.init()

# Configure TTS properties
voice_rate = int(config.get_config("VOICE_RATE", "175"))  # Speed of speech
voice_volume = float(config.get_config("VOICE_VOLUME", "0.9"))  # Volume (0.0 to 1.0)
tts_engine.setProperty('rate', voice_rate)
tts_engine.setProperty('volume', voice_volume)

# Try to set a more natural voice if available
voices = tts_engine.getProperty('voices')
for voice in voices:
    # Prefer female voice if available
    if "female" in voice.name.lower() or "zira" in voice.name.lower():
        tts_engine.setProperty('voice', voice.id)
        break

# Gemini Live API configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
MODEL = "gemini-2.5-flash"

def listen_for_command(timeout: int = 15) -> Optional[str]:
    """Listen for a voice command using the microphone.

    Args:
        timeout (int, optional): Timeout for listening in seconds. Defaults to 15.

    Returns:
        Optional[str]: The recognized command, or None if no command was recognized.
    """
    try:
        with sr.Microphone() as source:
            log.info("Listening for command...")
            log.info("Adjusting for ambient noise... please wait")
            recognizer.adjust_for_ambient_noise(source, duration=3)
            log.info("Ambient noise adjustment complete")
            log.info(f"Listening with timeout of {timeout} seconds")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            log.info("Processing speech...")
            command = recognizer.recognize_google(audio)
            log.info(f"Recognized command: {command}")
            return command
    except sr.WaitTimeoutError:
        log.info("No speech detected within timeout")
        return None
    except sr.UnknownValueError:
        log.info("Could not understand audio - audio was received but not recognized")
        return None
    except sr.RequestError as e:
        log.error(f"Speech recognition request failed: {e}")
        return None
    except Exception as e:
        log.error(f"Error during speech recognition: {e}")
        return None

def speak_text(text: str, use_gtts: bool = False) -> None:
    """Convert text to speech and play it.
    
    Args:
        text: Text to speak
        use_gtts: If True, use Google TTS (online) instead of pyttsx3 (offline)
    """
    try:
        if use_gtts:
            # Use Google TTS (requires internet)
            timestamp = int(time.time())
            audio_path = os.path.join(TEMP_DIR, f"speech_{timestamp}.mp3")
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(audio_path)
            
            # Play the audio file
            os.system(f"start {audio_path}")
        else:
            # Use pyttsx3 (offline TTS)
            tts_engine.say(text)
            tts_engine.runAndWait()
        
        log.info(f"Spoke: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    except Exception as e:
        log.error(f"Error in text-to-speech: {e}")

def process_voice_command(command: str, capture_image: bool = False) -> Dict[str, Any]:
    """Process a voice command and generate a response.
    
    Args:
        command: The voice command to process
        capture_image: Whether to capture an image for multimodal processing
        
    Returns:
        Dict containing the structured response
    """
    try:
        if not command:
            return {"cause": "No command detected", "steps": ["Please try again"], "script": ""}
        
        # Capture image if requested
        image_path = None
        if capture_image:
            log.info("Capturing image for multimodal processing")
            image_path = vision_handler.capture_device_image(use_webcam=False)  # Default to screenshot
        
        # Process with Gemini
        if image_path:
            result = gemini_handler.process_multimodal(command, image_path)
        else:
            result = gemini_handler.process_text(command)
        
        return result
    
    except Exception as e:
        log.error(f"Error processing voice command: {e}")
        return {"cause": "Error processing command", "steps": [f"Error: {str(e)}"], "script": ""}

# Initialize Gemini client for Live API
def initialize_gemini_client():
    """Initialize the Gemini client for Live API."""
    try:
        api_key = config.get_config("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        if not api_key:
            log.error("Gemini API key not found. Live API will not be available.")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL)
        log.info("Gemini Live API client initialized successfully")
        return model
    except Exception as e:
        log.error(f"Failed to initialize Gemini client: {e}")
        return None

# Live API configuration
def get_live_config():
    """Get the configuration for Gemini Live API."""
    if LiveConnectConfig is None:
        log.error("Live API not supported in this library version")
        return None
    return LiveConnectConfig(
        response_modalities=["AUDIO"],
        media_resolution="MEDIA_RESOLUTION_MEDIUM",
        speech_config=SpeechConfig(
            language_code="en-US",
            voice_config=VoiceConfig(
                prebuilt_voice_config=PrebuiltVoiceConfig(voice_name="Puck")
            )
        ),
    )

class LiveAudioLoop:
    """Handles real-time audio and visual interaction using Gemini Live API."""
    
    def __init__(self, video_mode="camera"):
        """Initialize the Live Audio Loop.
        
        Args:
            video_mode: Mode for video capture ("camera", "screen", or "none")
        """
        self.video_mode = video_mode
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.audio_stream = None
        self.pya = pyaudio.PyAudio()
        self.client = initialize_gemini_client()
        self.running = False
        
        # System prompt for repair agent context
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self):
        """Load the system prompt for the Fixer AI agent."""
        try:
            prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "prompts", "diagnose", "general.txt")
            with open(prompt_path, "r") as f:
                return f.read()
        except Exception as e:
            log.error(f"Failed to load system prompt: {e}")
            return "You are Fixer, an AI repair agent specialized in diagnosing and troubleshooting technical issues."

    async def send_text(self):
        """Send text input to the Gemini Live API."""
        # First send the system prompt
        await self.session.send(input=self.system_prompt)
        
        # Initial greeting
        print("Fixer AI voice interface activated. How can I help you?")
        print("Type your message or 'q' to quit, 'screenshot' to capture screen, 'webcam' to capture from camera")
        
        while self.running:
            text = await asyncio.to_thread(input, "message > ")
            
            if text.lower() == "q":
                self.running = False
                break
            elif text.lower() == "screenshot":
                print("Capturing screenshot...")
                await self._capture_and_send_screen()
                continue
            elif text.lower() == "webcam":
                print("Capturing from webcam...")
                await self._capture_and_send_webcam()
                continue
                
            await self.session.send(input=text or ".", end_of_turn=True)
    
    async def _capture_and_send_screen(self):
        """Capture and send a screenshot."""
        frame = await asyncio.to_thread(self._get_screen)
        if frame:
            await self.session.send(input=frame, end_of_turn=True)
    
    async def _capture_and_send_webcam(self):
        """Capture and send a webcam image."""
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        frame = await asyncio.to_thread(self._get_frame, cap)
        cap.release()
        if frame:
            await self.session.send(input=frame, end_of_turn=True)

    def _get_frame(self, cap):
        """Get a frame from the webcam."""
        # Read the frame
        ret, frame = cap.read()
        # Check if the frame was read successfully
        if not ret:
            return None
        # Convert BGR to RGB color space
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    def _get_screen(self):
        """Get a screenshot."""
        try:
            sct = mss.mss()
            monitor = sct.monitors[0]

            i = sct.grab(monitor)

            mime_type = "image/jpeg"
            image_bytes = mss.tools.to_png(i.rgb, i.size)
            img = PIL.Image.open(io.BytesIO(image_bytes))

            image_io = io.BytesIO()
            img.save(image_io, format="jpeg")
            image_io.seek(0)

            image_bytes = image_io.read()
            return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}
        except Exception as e:
            log.error(f"Error capturing screenshot: {e}")
            return None

    async def get_frames(self):
        """Continuously get frames from the webcam."""
        try:
            cap = await asyncio.to_thread(cv2.VideoCapture, 0)

            while self.running:
                frame = await asyncio.to_thread(self._get_frame, cap)
                if frame is None:
                    break

                await asyncio.sleep(1.0)  # Send frame every second
                await self.out_queue.put(frame)

            # Release the VideoCapture object
            cap.release()
        except Exception as e:
            log.error(f"Error in get_frames: {e}")

    async def get_screen(self):
        """Continuously get screenshots."""
        try:
            while self.running:
                frame = await asyncio.to_thread(self._get_screen)
                if frame is None:
                    break

                await asyncio.sleep(1.0)  # Send screen every second
                await self.out_queue.put(frame)
        except Exception as e:
            log.error(f"Error in get_screen: {e}")

    async def send_realtime(self):
        """Send realtime data to the Gemini Live API."""
        try:
            while self.running:
                msg = await self.out_queue.get()
                await self.session.send(input=msg)
        except Exception as e:
            log.error(f"Error in send_realtime: {e}")

    async def listen_audio(self):
        """Listen for audio input from the microphone."""
        try:
            mic_info = self.pya.get_default_input_device_info()
            self.audio_stream = await asyncio.to_thread(
                self.pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
            
            kwargs = {"exception_on_overflow": False}
            
            while self.running:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            log.error(f"Error in listen_audio: {e}")

    async def receive_audio(self):
        """Receive audio from the Gemini Live API."""
        try:
            while self.running:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        continue
                    if text := response.text:
                        print(text, end="")

                # If you interrupt the model, it sends a turn_complete.
                # For interruptions to work, we need to stop playback.
                # So empty out the audio queue because it may have loaded
                # much more audio than has played yet.
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()
        except Exception as e:
            log.error(f"Error in receive_audio: {e}")

    async def play_audio(self):
        """Play audio received from the Gemini Live API."""
        try:
            stream = await asyncio.to_thread(
                self.pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            while self.running:
                bytestream = await self.audio_in_queue.get()
                await asyncio.to_thread(stream.write, bytestream)
        except Exception as e:
            log.error(f"Error in play_audio: {e}")

    async def run(self):
        """Run the Live Audio Loop."""
        if not self.client:
            log.error("Gemini client not initialized. Cannot run Live Audio Loop.")
            return False
            
        try:
            self.running = True
            config = get_live_config()
            
            async with (
                self.client.aio.live.connect(model=MODEL, config=config) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                
                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            log.info("Live Audio Loop cancelled")
            return True
        except Exception as e:
            log.error(f"Error in Live Audio Loop: {e}")
            if self.audio_stream:
                self.audio_stream.close()
            traceback.print_exception(e)
            return False
        finally:
            self.running = False
            if self.audio_stream:
                self.audio_stream.close()
            return True

def run_live_mode(video_mode="camera"):
    """Run the voice interface using Gemini Live API.
    
    Args:
        video_mode: Mode for video capture ("camera", "screen", or "none")
        
    Returns:
        True if completed successfully, False otherwise
    """
    try:
        loop = LiveAudioLoop(video_mode=video_mode)
        return asyncio.run(loop.run())
    except Exception as e:
        log.error(f"Error in run_live_mode: {e}")
        return False

def run_traditional_voice():
    """Run the traditional voice interaction loop using speech recognition."""
    log.info("Starting traditional voice interaction...")
    log.info("Initializing Gemini client for traditional voice mode")
    gemini_client = initialize_gemini_client()
    if gemini_client is None:
        log.error("Gemini client initialization failed. Voice mode will not work.")
        return

    while True:
        try:
            command = listen_for_command()
            if command:
                log.info(f"Processing command: {command}")
                # Use Gemini API to process the transcribed text
                response = gemini_handler.process_text(command)
                if response.get("success", False):
                    content = response.get("content", "")
                    log.info(f"Gemini response: {content}")
                    # Optionally convert response to speech if configured
                    if config.get_config("VOICE_RESPONSE_ENABLED", False):
                        log.info("Converting response to speech")
                        speak_text(content)
                else:
                    error = response.get("error", "Unknown error processing command")
                    log.error(f"Error processing command: {error}")
                    speak_text("Sorry, I encountered an error processing your command.")
            else:
                log.info("No command detected")
        except KeyboardInterrupt:
            log.info("Traditional voice interaction stopped by user")
            break
        except Exception as e:
            log.error(f"Error in traditional voice interaction: {e}")
            speak_text("Sorry, I encountered an error. Please try again.")

def run(use_live_api=False, video_mode="camera") -> None:
    """Run the voice interface in a continuous loop.
    
    Args:
        use_live_api: Whether to use Gemini Live API for real-time interaction
        video_mode: Mode for video capture when using Live API
    """
    if use_live_api:
        log.info("Starting voice interface with Gemini Live API")
        return run_live_mode(video_mode)
        
    # Traditional voice interface
    run_traditional_voice()

# Function to recognize speech from an audio file
def recognize_from_file(audio_file_path: str) -> Optional[str]:
    """Recognize speech from an audio file.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Recognized text or None if recognition failed
    """
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            log.info(f"Recognized from file: {text}")
            return text
    
    except Exception as e:
        log.error(f"Error recognizing speech from file: {e}")
        return None
