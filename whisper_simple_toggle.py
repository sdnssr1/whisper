#!/usr/bin/env python3
"""
Simple Whisper Toggle App
Double-click to start/stop transcription
"""

import subprocess
import os
import signal
from pathlib import Path
import sys

# Configuration
WHISPER_DIR = "/Users/saeed/Documents/GitHub/whisper"
PID_FILE = "/tmp/whisper_live.pid"
VENV_PYTHON = f"{WHISPER_DIR}/.venv/bin/python"

def show_notification(title, message):
    """Show macOS notification"""
    cmd = f'osascript -e \'display notification "{message}" with title "{title}"\''
    os.system(cmd)

def is_running():
    """Check if whisper transcription is running"""
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)  # Test if process exists
        return True
    except (OSError, ValueError):
        # Process doesn't exist or invalid PID
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return False

def start_transcription():
    """Start live transcription"""
    if is_running():
        show_notification("Whisper", "Already running!")
        return

    try:
        # Start the live transcription script
        cmd = [VENV_PYTHON, f"{WHISPER_DIR}/live_transcribe.py"]
        process = subprocess.Popen(
            cmd,
            cwd=WHISPER_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Save PID
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
        
        show_notification("Whisper Started", "🎙 Live transcription is now running")
        
    except Exception as e:
        show_notification("Whisper Error", f"Failed to start: {str(e)}")

def stop_transcription():
    """Stop live transcription"""
    if not is_running():
        show_notification("Whisper", "Not running!")
        return

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # Kill the process group
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        
        # Clean up PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        
        show_notification("Whisper Stopped", "🛑 Transcription stopped")
        
    except Exception as e:
        show_notification("Whisper Error", f"Failed to stop: {str(e)}")
        # Force cleanup
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

def main():
    """Main toggle function"""
    os.chdir(WHISPER_DIR)
    
    if is_running():
        print("Stopping transcription...")
        stop_transcription()
    else:
        print("Starting transcription...")
        start_transcription()

if __name__ == "__main__":
    main()
