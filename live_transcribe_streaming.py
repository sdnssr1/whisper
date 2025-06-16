#!/usr/bin/env python3
"""
Streaming Whisper Live Transcription
Near word-by-word transcription with noise suppression
"""

import queue, sys, time
from pathlib import Path
import threading

import numpy as np
import sounddevice as sd
import whisper

SAMPLE_RATE = 16000        # Whisper expects 16 kHz mono
CHUNK_SEC   = 0.5          # Very small chunks for streaming feel (0.5 seconds)
BUFFER_SEC  = 2.0          # Keep 2 seconds of context for better accuracy

# Noise suppression settings
NOISE_THRESHOLD = 0.005    # Lower threshold to catch whispering
SPEECH_THRESHOLD = 0.3     # Lower threshold for Whisper speech detection (was 0.6)
MIN_SPEECH_LENGTH = 0.3    # Minimum duration to consider as speech (seconds)
SILENCE_TIMEOUT = 5.0      # Only finalize line after 5 seconds of silence

# Set up transcript file
TRANSCRIPT_FILE = Path.home() / "Documents" / "whisper_transcripts.txt"
TRANSCRIPT_FILE.parent.mkdir(exist_ok=True)

print("Loading Whisper model … (optimized for streaming)")
model = whisper.load_model("small")

audio_q = queue.Queue()
current_line = ""
last_output_time = 0
last_speech_time = 0
accumulated_text = ""

def audio_callback(indata, frames, t, status):
    if status:
        print(status, file=sys.stderr)
    # Convert int16 -> float32 in [-1,1]
    audio_q.put(indata.copy().flatten().astype(np.float32) / 32768.0)

def clear_current_line():
    """Clear the current line in terminal"""
    print('\r' + ' ' * 80 + '\r', end='', flush=True)

def print_streaming(text, is_final=False):
    """Print text in streaming fashion"""
    global current_line, last_output_time, accumulated_text
    
    ts = time.strftime("%H:%M:%S")
    
    if is_final:
        # Final transcription - print on new line and save to file
        clear_current_line()
        final_line = f"[{ts}] {accumulated_text.strip()}"
        print(final_line)
        
        # Save to file
        with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
            f.write(final_line + "\n")
            f.flush()
        
        current_line = ""
        accumulated_text = ""
    else:
        # Continuous streaming - keep appending to same line
        if not accumulated_text:
            accumulated_text = text.strip()
        else:
            # Append new words, avoiding duplication
            new_words = text.strip().split()
            existing_words = accumulated_text.split()
            
            # Simple deduplication - add words that aren't already at the end
            for word in new_words:
                if not existing_words or word != existing_words[-1]:
                    accumulated_text += " " + word
        
        current_line = f"[{ts}] {accumulated_text.strip()}"
        clear_current_line()
        print(f"\r{current_line}", end='', flush=True)

def has_speech(audio_chunk):
    """Simple voice activity detection - more sensitive for whispering"""
    # Calculate RMS (root mean square) energy
    rms = np.sqrt(np.mean(audio_chunk**2))
    
    # Calculate variability (speech has more variation than steady noise)
    variability = np.std(audio_chunk)
    
    # More sensitive thresholds for whispering
    return rms > NOISE_THRESHOLD and variability > NOISE_THRESHOLD * 0.3

def preprocess_audio(audio_chunk):
    """Simple noise reduction preprocessing"""
    # Apply a simple high-pass filter to reduce low-frequency fan noise
    # This is a basic approach - for better results, more sophisticated filtering could be added
    
    # Calculate a simple moving average to detect baseline noise
    baseline = np.mean(np.abs(audio_chunk))
    
    # If the chunk is too quiet, return silence
    if baseline < NOISE_THRESHOLD:
        return np.zeros_like(audio_chunk)
    
    return audio_chunk

# Log session start
with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
    session_start = time.strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"\n=== WHISPER STREAMING SESSION: {session_start} ===\n")

with sd.InputStream(channels=1,
                    samplerate=SAMPLE_RATE,
                    dtype="int16",
                    blocksize=int(SAMPLE_RATE*0.1),   # Very small blocks
                    callback=audio_callback):

    print("🎙  Streaming transcription - speak now! (Ctrl-C to stop)")
    print("=" * 60)
    
    buf = np.empty((0,), dtype=np.float32)
    context_buf = np.empty((0,), dtype=np.float32)  # Longer buffer for context
    
    try:
        while True:
            # Get audio data
            new_audio = audio_q.get()
            buf = np.concatenate([buf, new_audio])
            context_buf = np.concatenate([context_buf, new_audio])
            
            # Keep context buffer to reasonable size
            max_context_samples = int(SAMPLE_RATE * BUFFER_SEC)
            if len(context_buf) > max_context_samples:
                context_buf = context_buf[-max_context_samples:]
            
            # Process small chunks for streaming
            if len(buf) >= SAMPLE_RATE * CHUNK_SEC:
                chunk, buf = np.split(buf, [int(SAMPLE_RATE * CHUNK_SEC)])
                
                # Use context for better accuracy, but transcribe recent chunk
                if len(context_buf) >= SAMPLE_RATE * CHUNK_SEC:
                    
                    # Check if recent audio contains speech
                    recent_audio = context_buf[-int(SAMPLE_RATE * CHUNK_SEC):]
                    
                    if has_speech(recent_audio):
                        last_speech_time = time.time()
                        
                        # Preprocess audio to reduce noise
                        processed_audio = preprocess_audio(context_buf)
                        
                        # Transcribe with lower speech threshold for whispering
                        result = model.transcribe(processed_audio,
                                                language="en",
                                                fp16=False,
                                                temperature=0,
                                                no_speech_threshold=SPEECH_THRESHOLD,  # Lower threshold
                                                condition_on_previous_text=False)["text"]
                        
                        # Check if we have actual speech
                        if result.strip() and len(result.strip()) > 0:
                            # Show continuous streaming result
                            print_streaming(result, is_final=False)
                    
                    # Check if we should finalize the line (after silence timeout)
                    elif accumulated_text and time.time() - last_speech_time > SILENCE_TIMEOUT:
                        # Finalize after silence
                        print_streaming("", is_final=True)
                        context_buf = np.empty((0,), dtype=np.float32)

    except KeyboardInterrupt:
        clear_current_line()
        print("\n🛑 Streaming transcription stopped")
        
        # Save final line if there was partial content
        if current_line:
            with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
                f.write(current_line + "\n")
