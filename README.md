# Fixer AI: Technical Repair Agent

Fixer AI is an intelligent repair agent capable of troubleshooting technical issues through multiple interfaces including voice commands, SMS, and command-line interface (CLI). It leverages Google's Gemini AI to provide technical assistance and can execute diagnostic scripts to help resolve common technical problems.

## Features

- **Multiple Interaction Modes**:
  - CLI mode for text-based interaction
  - Voice mode with traditional speech recognition
  - Voice mode with Gemini Live API (real-time)
  - Vision mode with webcam support
  - Screen sharing capability for visual troubleshooting
  - SMS daemon for remote assistance

- **Technical Capabilities**:
  - Diagnoses common technical issues
  - Generates and executes repair scripts for Windows, Linux, and macOS
  - Real-time voice and visual interaction
  - Screen capture for better context awareness

## System Requirements

- Python 3.8+
- Microphone (for voice modes)
- Webcam (for vision modes)
- Internet connection (for AI API access)
- Google Gemini API key

## Quick Start Guide

1. Clone the repository:
   ```
   git clone https://github.com/enockarthur298/Fixer.git
   cd Fixer
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   # Copy the example environment file
   cp .env.example .env
   # Edit the .env file and add your Google Gemini API key
   # GEMINI_API_KEY=your_api_key_here
   ```

5. Run the application in CLI mode:
   ```
   python main.py --cli
   ```
   
   This will start Fixer AI in command-line interface mode, allowing you to interact with the repair agent through text commands.

## Usage Options

All commands should be run from the root Fixer directory:

### CLI Mode (Recommended for first-time users)
```
python main.py --cli
```
This starts the interactive text-based interface, ideal for learning how Fixer works.

### Voice Mode
```
# Traditional speech recognition
python main.py --voice

# With Gemini Live API and webcam
python main.py --voice-live

# With Gemini Live API and screen sharing
python main.py --voice-live-screen

# With Gemini Live API without visuals
python main.py --voice-live-none
```

### Vision Mode
```
# With webcam
python main.py --vision-live

# With screen sharing
python main.py --vision-live-screen

# Without visuals
python main.py --vision-live-none
```

### SMS Daemon
```
python main.py --sms-daemon
```

You can also provide an initial prompt in Live API modes:
```
python main.py --vision-live --prompt "My computer is running slowly"
```

## Project Structure

- `core/`: Core functionality and AI integration
- `handlers/`: Interface handlers (CLI, voice, SMS, vision)
- `prompts/`: AI prompt templates
  - `diagnose/`: Diagnostic prompt templates
  - `scripts/`: Script generation templates for different OS
- `utils/`: Utility functions and helpers
- `deployment/`: Deployment configuration files
- `systemd/`: SystemD service files for Linux deployment

## Configuration

The application uses environment variables for configuration. See `.env.example` for required variables.

## Building Executable

To build a standalone executable:
```
python build_exe.py
```

This will create an executable in the `dist` directory.

## Deployment

For Linux systems, a SystemD service file is provided in the `deployment` directory.