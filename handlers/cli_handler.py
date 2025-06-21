#!/usr/bin/env python3
"""
CLI Handler for Fixer AI

Provides a terminal-based interface for interacting with the Fixer AI agent.
Supports text input/output and can trigger image capture for multimodal analysis.
"""

import os
import sys
import time
import platform
from typing import Dict, Any, Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

from utils import logger
from handlers import gemini_handler, vision_handler
from core import script_runner

# Initialize logger
log = logger.get_logger(__name__)

# Initialize Rich console
console = Console()

def display_welcome() -> None:
    """Display welcome message and instructions."""
    console.print(Panel.fit(
        """[bold blue]Fixer AI - Technical Repair Assistant[/bold blue]
        
[green]Commands:[/green]
  - Type your technical issue or question
  - Use [bold]!screenshot[/bold] to capture and analyze your screen
  - Use [bold]!webcam[/bold] to capture and analyze using your webcam
  - Use [bold]!run[/bold] to execute the last suggested script
  - Use [bold]!exit[/bold] to quit
        """,
        title="Welcome to Fixer AI",
        border_style="blue"
    ))

def process_command(command: str, capture_image: bool = False, use_webcam: bool = False) -> Dict[str, Any]:
    """Process a CLI command and generate a response.
    
    Args:
        command: The command to process
        capture_image: Whether to capture an image
        use_webcam: Whether to use webcam (if capturing image)
        
    Returns:
        Dict containing the structured response
    """
    try:
        # Capture image if requested
        image_path = None
        if capture_image:
            with console.status("[bold green]Capturing image..."):
                image_path = vision_handler.capture_device_image(use_webcam=use_webcam)
                if not image_path:
                    console.print("[bold red]Failed to capture image[/bold red]")
        
        # Process with Gemini
        with console.status("[bold green]Processing with AI..."):
            if image_path:
                result = gemini_handler.process_multimodal(command, image_path)
            else:
                result = gemini_handler.process_text(command)
        
        return result
    
    except Exception as e:
        log.error(f"Error processing CLI command: {e}")
        return {"cause": "Error processing command", "steps": [f"Error: {str(e)}"], "script": ""}

def display_result(result: Dict[str, Any]) -> None:
    """Display the result in a formatted way.
    
    Args:
        result: The result dictionary from Gemini
    """
    try:
        # Display diagnosis
        if result.get("cause"):
            console.print(Panel(
                f"[bold]Diagnosis:[/bold]\n{result['cause']}",
                title="Problem Analysis",
                border_style="yellow"
            ))
        
        # Display steps
        if result.get("steps") and len(result["steps"]) > 0:
            steps_md = "# Repair Steps\n\n"
            for i, step in enumerate(result["steps"]):
                steps_md += f"{i+1}. {step}\n"
            
            console.print(Markdown(steps_md))
        
        # Display script if available
        if result.get("script") and result["script"].strip():
            # Determine script type
            os_type = platform.system().lower()
            script_type = "PowerShell" if os_type == "windows" and ("function" in result["script"] or "param(" in result["script"] or "$" in result["script"] or "Write-Host" in result["script"] or "Get-Process" in result["script"]) else "Batch" if os_type == "windows" else "Bash"
                
            console.print(Panel(
                result["script"],
                title=f"{script_type} Repair Script",
                border_style="green"
            ))
            console.print("[bold blue]Type [bold]!run[/bold] to execute this script[/bold blue]")
            console.print("[bold yellow]The script will be displayed again for review before execution[/bold yellow]")
    
    except Exception as e:
        log.error(f"Error displaying result: {e}")
        console.print(f"[bold red]Error displaying result: {e}[/bold red]")

def run() -> None:
    """Run the CLI interface in a loop."""
    try:
        # Display welcome message
        display_welcome()
        
        # Store the last script for potential execution
        last_script = ""
        
        # Main interaction loop
        while True:
            # Get user input
            user_input = Prompt.ask("\n[bold green]How can I help you?[/bold green]")
            
            # Process special commands
            if user_input.lower() in ["!exit", "exit", "quit", "q"]:
                console.print("[bold blue]Thank you for using Fixer AI. Goodbye![/bold blue]")
                break
            
            elif user_input.lower() == "!screenshot":
                # Capture and analyze screenshot
                console.print("[bold blue]Please describe what I should look for in the screenshot:[/bold blue]")
                description = Prompt.ask("[bold green]Description[/bold green]")
                result = process_command(description, capture_image=True, use_webcam=False)
                display_result(result)
                if result.get("script"):
                    last_script = result["script"]
            
            elif user_input.lower() == "!webcam":
                # Capture and analyze webcam image
                console.print("[bold blue]Please describe what I should look for in the webcam image:[/bold blue]")
                description = Prompt.ask("[bold green]Description[/bold green]")
                result = process_command(description, capture_image=True, use_webcam=True)
                display_result(result)
                if result.get("script"):
                    last_script = result["script"]
            
            elif user_input.lower() == "!run":
                # Execute the last script
                if not last_script:
                    console.print("[bold red]No script available to run[/bold red]")
                    continue
                
                # Display the script again for user review
                console.print(Panel(
                    last_script,
                    title="Script to Execute",
                    border_style="yellow"
                ))
                
                # Determine if it's a PowerShell or Bash script
                os_type = platform.system().lower()
                script_type = "PowerShell" if os_type == "windows" and ("function" in last_script or "param(" in last_script or "$" in last_script or "Write-Host" in last_script or "Get-Process" in last_script) else "Batch" if os_type == "windows" else "Bash"
                
                # Confirm before running with script type information
                if Confirm.ask(f"[bold red]Are you sure you want to run this {script_type} script?[/bold red]"):
                    with console.status("[bold green]Running script..."):
                        output = script_runner.run_script(last_script)
                    
                    console.print(Panel(
                        output,
                        title="Script Execution Result",
                        border_style="blue"
                    ))
            
            else:
                # For normal text input, check if it's a technical issue and offer image capture
                if len(user_input) > 10 and not user_input.endswith("?"):
                    # Likely a technical issue description rather than a question
                    capture_image = Confirm.ask("\n[bold blue]Would you like to capture a screenshot or webcam image to help diagnose this issue?[/bold blue]")
                    
                    if capture_image:
                        # Ask for capture type
                        use_webcam = Confirm.ask("[bold blue]Use webcam? (No for screenshot)[/bold blue]")
                        
                        # Capture the image
                        with console.status("[bold green]Capturing image..."):
                            result = process_command(user_input, capture_image=True, use_webcam=use_webcam)
                    else:
                        # Process without image
                        result = process_command(user_input)
                else:
                    # Process normal text input without image prompt
                    result = process_command(user_input)
                
                # Display result and store script
                display_result(result)
                if result.get("script"):
                    last_script = result["script"]
    
    except KeyboardInterrupt:
        console.print("\n[bold blue]CLI interface terminated.[/bold blue]")
    except Exception as e:
        log.error(f"Error in CLI interface: {e}")
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]")

if __name__ == "__main__":
    # For testing the module directly
    run()
