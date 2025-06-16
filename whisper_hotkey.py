#!/usr/bin/env python3
import subprocess
import sys
import os
import signal
import time
from pathlib import Path

WHISPER_DIR = "/Users/saeed/Documents/GitHub/whisper"
PID_FILE = "/tmp/whisper_live.pid"

def show_notification(title, message):
    """Show macOS notification"""
    cmd = f'osascript -e \'display notification "{message}" with title "{title}"\''
    os.system(cmd)

def is_running():
    """Check if whisper is already running"""
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
        show_notification("Whisper Live", "Already running!")
        return
    
    show_notification("Whisper Live", "🎙 Starting transcription...")
    
    # Start the process in background
    cmd = f"""
    cd {WHISPER_DIR} && 
    source .venv/bin/activate && 
    python live_transcribe.py
    """
    
    process = subprocess.Popen(
        ["bash", "-c", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Save PID
    with open(PID_FILE, 'w') as f:
        f.write(str(process.pid))
    
    # Wait a moment to see if it starts successfully
    time.sleep(2)
    if process.poll() is None:
        show_notification("Whisper Live", "✅ Transcription active!")
    else:
        show_notification("Whisper Live", "❌ Failed to start")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

def stop_transcription():
    """Stop live transcription"""
    if not is_running():
        show_notification("Whisper Live", "Not running")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # Kill the process group
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        os.remove(PID_FILE)
        show_notification("Whisper Live", "🛑 Transcription stopped")
        
    except Exception as e:
        show_notification("Whisper Live", f"Error stopping: {e}")

def toggle_transcription():
    """Toggle transcription on/off"""
    if is_running():
        stop_transcription()
    else:
        start_transcription()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "start":
            start_transcription()
        elif action == "stop":
            stop_transcription()
        elif action == "toggle":
            toggle_transcription()
        elif action == "status":
            status = "running" if is_running() else "stopped"
            print(f"Whisper Live is {status}")
        else:
            print("Usage: whisper_hotkey.py [start|stop|toggle|status]")
    else:
        toggle_transcription()
