#!/usr/bin/env python3
"""
Whisper Clear - Clean Speech-to-Text
A more stable version with better noise handling
"""

import numpy as np
import sounddevice as sd
import whisper
import time
from pathlib import Path
from scipy.signal import butter, filtfilt

# Configuration
SAMPLE_RATE = 16000
CHUNK_SEC = 2.5  # Slightly larger chunks for better context
SILENCE_TIMEOUT = 3.0  # Seconds of silence before finalizing
ENERGY_THRESHOLD = 0.006  # Balanced sensitivity
MIN_SPEECH_DURATION = 1.2  # Minimum seconds of speech to process

# Set up transcript file
TRANSCRIPT_FILE = Path.home() / "Documents" / "whisper_transcript.txt"
TRANSCRIPT_FILE.parent.mkdir(exist_ok=True)

# Initialize
model = whisper.load_model("small.en")  # English-specific model
print("\n🎤 Whisper Clear - Speak now (Ctrl+C to stop)")
print("=" * 50)

# Global state
current_text = ""
last_update = 0
is_recording = True

# Common phrases to reject
REJECT_PHRASES = [
    "thanks for watching",
    "please like and subscribe",
    "guitar and bass",
    "you"
]

def get_audio_energy(audio_chunk):
    """Calculate the energy level of an audio chunk"""
    return np.sqrt(np.mean(audio_chunk**2))

def transcribe_audio(audio_data):
    """Transcribe audio with optimized settings for voice accuracy"""
    try:
        result = model.transcribe(
            audio_data.astype(np.float32).flatten(),
            language="en",
            fp16=False,
            temperature=0,  # More deterministic output
            no_speech_threshold=0.85,  # More sensitive speech detection
            condition_on_previous_text=False,
            word_timestamps=True,  # Better word alignment
            suppress_tokens=[-1]  # Suppress common non-speech tokens
        )
        
        text = result["text"].strip()
        
        # Skip if text matches common rejection phrases
        if any(phrase in text.lower() for phrase in REJECT_PHRASES):
            return ""
        
        if text:
            # Capitalize the first letter
            text = text[0].upper() + text[1:]
            
            # Add a period if it ends without punctuation
            if text[-1] not in ['.', '!', '?']:
                text += '.'
                
        return text
    except Exception as e:
        return ""

def butter_highpass_filter(data, cutoff, fs, order=5):
    """Apply high-pass filter to emphasize voice frequencies"""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    y = filtfilt(b, a, data.flatten())
    return y.reshape(data.shape)

def audio_callback(indata, frames, time, status):
    """Called for each audio chunk"""
    global current_text, last_update
    
    if status:
        return
    
    # Apply a simple high-pass filter to emphasize voice frequencies
    filtered_audio = butter_highpass_filter(indata, 300, SAMPLE_RATE)
    
    energy = get_audio_energy(filtered_audio)
    
    # Only process if there's significant audio for MIN_SPEECH_DURATION
    if energy > ENERGY_THRESHOLD:
        try:
            # Convert to float32 for Whisper
            audio_data = filtered_audio.astype(np.float32).flatten()
            
            # Only transcribe if we have at least MIN_SPEECH_DURATION of audio
            if len(audio_data) >= SAMPLE_RATE * MIN_SPEECH_DURATION:
                text = transcribe_audio(audio_data)
                
                # Validate text isn't random noise
                if text and len(text.split()) >= 2:
                    current_text = text
                    print(f"\r{text}", end='', flush=True)
                    last_update = time.inputBufferAdcTime
        except Exception as e:
            pass

def main():
    global current_text, last_update, is_recording
    
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=audio_callback,
            blocksize=int(SAMPLE_RATE * CHUNK_SEC)
        ):
            print("Listening... (Press Ctrl+C to stop)")
            
            while is_recording:
                # Check for silence timeout
                if current_text and (time.time() - last_update) > SILENCE_TIMEOUT:
                    # Save the final text
                    with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
                        f.write(f"[{time.strftime('%H:%M:%S')}] {current_text}\n")
                    current_text = ""
                
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n\n🎤 Transcription stopped")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
    finally:
        # Save any remaining text
        if current_text:
            with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {current_text}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
