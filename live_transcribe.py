import queue, sys, time

import numpy as np
import sounddevice as sd
import whisper

SAMPLE_RATE = 16000        # Whisper expects 16 kHz mono
CHUNK_SEC   = 4            # latency window (seconds)

print("Loading Whisper model … (first run downloads it)")
model = whisper.load_model("small")           # or "base", "medium", …

audio_q = queue.Queue()

def audio_callback(indata, frames, t, status):
    if status:
        print(status, file=sys.stderr)
    # Convert int16 -> float32 in [-1,1]
    audio_q.put(indata.copy().flatten().astype(np.float32) / 32768.0)

with sd.InputStream(channels=1,
                    samplerate=SAMPLE_RATE,
                    dtype="int16",
                    blocksize=int(SAMPLE_RATE*0.5),   # 0.5-s blocks
                    callback=audio_callback):

    print("🎙  Start speaking. Ctrl-C to stop.")
    buf = np.empty((0,), dtype=np.float32)

    try:
        while True:
            buf = np.concatenate([buf, audio_q.get()])
            if len(buf) >= SAMPLE_RATE * CHUNK_SEC:
                chunk, buf = np.split(buf, [SAMPLE_RATE * CHUNK_SEC])
                result = model.transcribe(chunk,
                                          language="en",
                                          fp16=False,
                                          temperature=0)["text"]
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] {result.strip()}")
    except KeyboardInterrupt:
        pass
