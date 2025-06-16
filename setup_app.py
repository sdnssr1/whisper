#!/usr/bin/env python3
"""
Setup script to create a standalone macOS app for Whisper Live Transcription
"""

import os
import shutil
import subprocess
from pathlib import Path

APP_NAME = "WhisperLive"
APP_DIR = f"/Applications/{APP_NAME}.app"
CONTENTS_DIR = f"{APP_DIR}/Contents"
MACOS_DIR = f"{CONTENTS_DIR}/MacOS"
RESOURCES_DIR = f"{CONTENTS_DIR}/Resources"

def create_app_structure():
    """Create the macOS app bundle structure"""
    print("🏗️  Creating app bundle structure...")
    
    # Remove existing app if it exists
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
    
    # Create directories
    os.makedirs(MACOS_DIR, exist_ok=True)
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    
    print(f"✅ Created: {APP_DIR}")

def create_info_plist():
    """Create Info.plist file"""
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleExecutable</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.whisper.live</string>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>WhisperLive needs microphone access for speech transcription.</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>'''
    
    with open(f"{CONTENTS_DIR}/Info.plist", "w") as f:
        f.write(plist_content)
    
    print("✅ Created Info.plist")

def create_launcher_script():
    """Create the main launcher script"""
    launcher_content = f'''#!/bin/bash
# WhisperLive Launcher Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" &> /dev/null && pwd )"
APP_DIR="$SCRIPT_DIR/../Resources"

# Change to the app directory
cd "$APP_DIR"

# Activate virtual environment
source .venv/bin/activate

# Check if model exists, download if needed
if [ ! -f "$HOME/.cache/whisper/small.en.pt" ]; then
    echo "📥 Downloading Whisper model..."
    python -c "import whisper; whisper.load_model('small.en')"
fi

# Launch the transcription app
echo "🎤 Starting WhisperLive..."
python whisper_app.py
'''
    
    launcher_path = f"{MACOS_DIR}/{APP_NAME}"
    with open(launcher_path, "w") as f:
        f.write(launcher_content)
    
    # Make executable
    os.chmod(launcher_path, 0o755)
    print(f"✅ Created launcher: {launcher_path}")

def create_main_app():
    """Create the main application file"""
    app_content = '''#!/usr/bin/env python3
"""
WhisperLive - Standalone Transcription App
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
import os
import signal
from pathlib import Path
import time

class WhisperLiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WhisperLive - Speech Transcription")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # State variables
        self.transcription_process = None
        self.is_running = False
        self.transcript_file = Path.home() / "Documents" / "whisper_transcripts.txt"
        
        self.setup_ui()
        self.start_file_monitor()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎤 WhisperLive", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Control buttons
        self.start_button = ttk.Button(main_frame, text="Start Transcription", command=self.start_transcription)
        self.start_button.grid(row=1, column=0, padx=(0, 10), sticky=tk.W)
        
        self.stop_button = ttk.Button(main_frame, text="Stop Transcription", command=self.stop_transcription, state="disabled")
        self.stop_button.grid(row=1, column=1, padx=10, sticky=tk.W)
        
        self.clear_button = ttk.Button(main_frame, text="Clear Text", command=self.clear_text)
        self.clear_button.grid(row=1, column=2, padx=(10, 0), sticky=tk.W)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to transcribe", foreground="green")
        self.status_label.grid(row=1, column=3, padx=(20, 0), sticky=tk.E)
        
        # Text display area
        self.text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=80, height=30)
        self.text_area.grid(row=2, column=0, columnspan=4, pady=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Instructions
        instructions = """Instructions:
1. Click 'Start Transcription' to begin
2. Speak clearly into your microphone
3. Your words will appear here in real-time
4. Click 'Stop Transcription' when finished
5. All transcriptions are saved to ~/Documents/whisper_transcripts.txt"""
        
        self.text_area.insert(tk.END, instructions)
    
    def start_transcription(self):
        """Start the transcription process"""
        try:
            # Change to the app directory
            app_dir = Path(__file__).parent
            
            # Start transcription process
            cmd = ["python", "whisper_clear.py"]
            self.transcription_process = subprocess.Popen(
                cmd,
                cwd=app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.is_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="🎤 Listening...", foreground="red")
            
            # Clear previous content and show live transcription
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "🎤 Listening for speech...\\n\\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start transcription: {str(e)}")
    
    def stop_transcription(self):
        """Stop the transcription process"""
        if self.transcription_process and self.is_running:
            try:
                # Send SIGINT to gracefully stop
                self.transcription_process.send_signal(signal.SIGINT)
                self.transcription_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                self.transcription_process.kill()
            except Exception:
                pass
            
            self.transcription_process = None
            self.is_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="Transcription stopped", foreground="orange")
    
    def clear_text(self):
        """Clear the text area"""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Text cleared.\\n\\n")
    
    def start_file_monitor(self):
        """Monitor the transcript file for updates"""
        def monitor():
            last_size = 0
            while True:
                try:
                    if self.transcript_file.exists():
                        current_size = self.transcript_file.stat().st_size
                        if current_size > last_size:
                            # File has new content
                            with open(self.transcript_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Update text area with new content
                            self.root.after(0, self.update_text_area, content)
                            last_size = current_size
                    
                    time.sleep(1)  # Check every second
                except Exception:
                    pass
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def update_text_area(self, content):
        """Update the text area with new content"""
        if self.is_running:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, content)
            self.text_area.see(tk.END)  # Scroll to bottom
    
    def on_closing(self):
        """Handle app closing"""
        if self.is_running:
            self.stop_transcription()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = WhisperLiveApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
'''
    
    app_path = f"{RESOURCES_DIR}/whisper_app.py"
    with open(app_path, "w") as f:
        f.write(app_content)
    
    print(f"✅ Created main app: {app_path}")

def copy_dependencies():
    """Copy all necessary files to the app bundle"""
    print("📦 Copying dependencies...")
    
    source_dir = Path("/Users/saeed/Documents/GitHub/whisper")
    
    # Files to copy
    files_to_copy = [
        "whisper_clear.py",
        "live_transcribe_streaming.py",
        "transcribe_with_voice_profile.py"
    ]
    
    for file_name in files_to_copy:
        source_file = source_dir / file_name
        if source_file.exists():
            shutil.copy2(source_file, RESOURCES_DIR)
            print(f"   ✅ Copied: {file_name}")
        else:
            print(f"   ⚠️  Missing: {file_name}")
    
    # Copy virtual environment
    venv_source = source_dir / ".venv"
    venv_dest = Path(RESOURCES_DIR) / ".venv"
    
    if venv_source.exists():
        print("📦 Copying virtual environment...")
        shutil.copytree(venv_source, venv_dest)
        print("   ✅ Virtual environment copied")
    else:
        print("   ⚠️  Virtual environment not found")

def set_permissions():
    """Set proper permissions for the app"""
    print("🔐 Setting permissions...")
    
    # Make the main executable
    os.chmod(f"{MACOS_DIR}/{APP_NAME}", 0o755)
    
    # Make Python files executable
    for py_file in Path(RESOURCES_DIR).glob("*.py"):
        os.chmod(py_file, 0o755)
    
    print("✅ Permissions set")

def main():
    """Main setup function"""
    print("🚀 Creating WhisperLive Standalone App")
    print("=" * 50)
    
    try:
        create_app_structure()
        create_info_plist()
        create_launcher_script()
        create_main_app()
        copy_dependencies()
        set_permissions()
        
        print("\\n" + "=" * 50)
        print("🎉 SUCCESS! WhisperLive app created!")
        print(f"📱 Location: {APP_DIR}")
        print("\\n📋 To use:")
        print("1. Open Finder and navigate to Applications")
        print("2. Double-click WhisperLive.app")
        print("3. Grant microphone permissions when prompted")
        print("4. Click 'Start Transcription' and speak!")
        print("\\n💾 Transcripts saved to: ~/Documents/whisper_transcripts.txt")
        
    except Exception as e:
        print(f"❌ Error creating app: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()
