#!/usr/bin/env python3
"""
Whisper Live Transcription Menu Bar App
A simple menu bar app to toggle live speech transcription
"""

import rumps
import subprocess
import os
import signal
from pathlib import Path

# Configuration
WHISPER_DIR = "/Users/saeed/Documents/GitHub/whisper"
PID_FILE = "/tmp/whisper_live.pid"
VENV_PYTHON = f"{WHISPER_DIR}/.venv/bin/python"

class WhisperMenuBarApp(rumps.App):
    def __init__(self):
        super(WhisperMenuBarApp, self).__init__(
            "🎙",  # Microphone icon
            title="🎙",
            icon=None,  # We'll use the emoji as icon
            template=None,
            menu=[
                "Start Transcription",
                "Stop Transcription", 
                rumps.separator,
                "Status",
                rumps.separator,
                "Quit"
            ]
        )
        self.update_status()

    def is_running(self):
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

    def update_status(self):
        """Update menu bar icon and menu items based on transcription status"""
        is_running = self.is_running()
        
        if is_running:
            self.title = "🟢"  # Green circle when running
            self.menu["Start Transcription"].title = "✓ Transcription Running"
            self.menu["Stop Transcription"].title = "Stop Transcription"
        else:
            self.title = "🎙"  # Microphone when stopped
            self.menu["Start Transcription"].title = "Start Transcription"
            self.menu["Stop Transcription"].title = "✗ Transcription Stopped"

    @rumps.clicked("Start Transcription")
    def start_transcription(self, _):
        """Start live transcription"""
        if self.is_running():
            rumps.notification("Whisper", "Already Running", "Transcription is already active")
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
            
            rumps.notification("Whisper", "Started", "🎙 Live transcription started")
            self.update_status()
            
        except Exception as e:
            rumps.notification("Whisper", "Error", f"Failed to start: {str(e)}")

    @rumps.clicked("Stop Transcription")
    def stop_transcription(self, _):
        """Stop live transcription"""
        if not self.is_running():
            rumps.notification("Whisper", "Not Running", "No transcription to stop")
            return

        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # Kill the process group
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            
            # Clean up PID file
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            
            rumps.notification("Whisper", "Stopped", "🛑 Transcription stopped")
            self.update_status()
            
        except Exception as e:
            rumps.notification("Whisper", "Error", f"Failed to stop: {str(e)}")
            # Force cleanup
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            self.update_status()

    @rumps.clicked("Status")
    def show_status(self, _):
        """Show current transcription status"""
        status = "Running" if self.is_running() else "Stopped"
        rumps.notification("Whisper Status", f"Transcription: {status}", "")

    @rumps.timer(1)  # Update every 5 seconds
    def update_timer(self, _):
        """Periodically update the status"""
        self.update_status()

if __name__ == "__main__":
    # Ensure we're in the right directory
    os.chdir(WHISPER_DIR)
    
    # Start the menu bar app
    app = WhisperMenuBarApp()
    app.run()
