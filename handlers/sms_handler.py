#!/usr/bin/env python3
"""
SMS Handler for Fixer AI

Provides SMS interaction capabilities via Twilio.
Implements a FastAPI webhook for receiving and responding to SMS messages.
"""

import os
import time
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from utils import logger, config
from handlers import gemini_handler

# Initialize logger
log = logger.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Fixer AI SMS Handler")

# Initialize Twilio client
def get_twilio_client() -> Optional[Client]:
    """Initialize Twilio client with credentials from config."""
    try:
        account_sid = config.get_config("TWILIO_ACCOUNT_SID")
        auth_token = config.get_config("TWILIO_AUTH_TOKEN")
        
        if not account_sid or not auth_token:
            log.error("Twilio credentials not found in configuration")
            return None
        
        return Client(account_sid, auth_token)
    
    except Exception as e:
        log.error(f"Error initializing Twilio client: {e}")
        return None

# Store conversation history for each phone number
conversation_history = {}

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "Fixer AI SMS Handler is running"}

@app.post("/sms")
async def sms_webhook(request: Request, From: str = Form(...), Body: str = Form(...)):
    """Webhook for receiving SMS messages from Twilio.
    
    Args:
        request: The FastAPI request object
        From: The phone number that sent the message (provided by Twilio)
        Body: The content of the SMS message (provided by Twilio)
    
    Returns:
        TwiML response with the AI's reply
    """
    try:
        log.info(f"Received SMS from {From}: {Body}")
        
        # Initialize response
        resp = MessagingResponse()
        
        # Process commands
        if Body.lower() in ["help", "commands"]:
            resp.message(
                "Fixer AI Commands:\n" +
                "- Ask any technical question\n" +
                "- Send 'reset' to clear conversation history\n" +
                "- Send 'help' to see this message"
            )
        elif Body.lower() == "reset":
            # Clear conversation history for this user
            if From in conversation_history:
                del conversation_history[From]
            resp.message("Conversation history has been reset.")
        else:
            # Process the message with Gemini
            result = process_sms(From, Body)
            
            # Format the response
            response_text = format_sms_response(result)
            
            # Send the response
            resp.message(response_text)
        
        return Response(content=str(resp), media_type="application/xml")
    
    except Exception as e:
        log.error(f"Error processing SMS webhook: {e}")
        resp = MessagingResponse()
        resp.message("Sorry, an error occurred while processing your request.")
        return Response(content=str(resp), media_type="application/xml")

def process_sms(phone_number: str, message: str) -> Dict[str, Any]:
    """Process an SMS message and generate a response.
    
    Args:
        phone_number: The sender's phone number
        message: The SMS message content
        
    Returns:
        Dict containing the structured response
    """
    try:
        # Get conversation history for this user or initialize it
        if phone_number not in conversation_history:
            conversation_history[phone_number] = []
        
        # Add user message to history
        conversation_history[phone_number].append({"role": "user", "message": message})
        
        # Keep only the last 5 messages to maintain context without overloading
        if len(conversation_history[phone_number]) > 10:
            conversation_history[phone_number] = conversation_history[phone_number][-10:]
        
        # Create context from history
        context = "\n".join([f"{item['role']}: {item['message']}" for item in conversation_history[phone_number][-5:]])
        
        # Process with Gemini
        full_message = f"Context:\n{context}\n\nCurrent question: {message}"
        result = gemini_handler.process_text(full_message)
        
        # Add assistant response to history
        response_summary = result.get("cause", "") + " " + ". ".join(result.get("steps", []))
        conversation_history[phone_number].append({"role": "assistant", "message": response_summary})
        
        return result
    
    except Exception as e:
        log.error(f"Error processing SMS: {e}")
        return {"cause": "Error processing your request", "steps": ["Please try again later"], "script": ""}

def format_sms_response(result: Dict[str, Any]) -> str:
    """Format the response for SMS delivery.
    
    Args:
        result: The result dictionary from Gemini
        
    Returns:
        Formatted text for SMS
    """
    try:
        response_parts = []
        
        # Add diagnosis
        if result.get("cause"):
            response_parts.append(f"DIAGNOSIS: {result['cause']}")
        
        # Add steps
        if result.get("steps") and len(result["steps"]) > 0:
            steps_text = "STEPS:\n"
            for i, step in enumerate(result["steps"]):
                steps_text += f"{i+1}. {step}\n"
            response_parts.append(steps_text)
        
        # Add script summary if available
        if result.get("script") and result["script"].strip():
            script_summary = "A repair script is available but too long for SMS. Please use the CLI or voice interface to access it."
            response_parts.append(script_summary)
        
        # Join all parts
        return "\n\n".join(response_parts)
    
    except Exception as e:
        log.error(f"Error formatting SMS response: {e}")
        return "Error formatting response. Please try again."

def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the SMS webhook server.
    
    Args:
        host: Host to bind the server to
        port: Port to bind the server to
    """
    try:
        # Check if Twilio is configured
        twilio_client = get_twilio_client()
        if not twilio_client:
            log.warning("Twilio not configured properly. SMS functionality will be limited.")
        
        # Get port from environment variable if available (for cloud deployment)
        port_env = os.environ.get("PORT")
        if port_env:
            port = int(port_env)
        
        # Start the FastAPI server
        log.info(f"Starting SMS webhook server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
    
    except Exception as e:
        log.error(f"Error starting SMS webhook server: {e}")
        raise

if __name__ == "__main__":
    # For testing the module directly
    run()
