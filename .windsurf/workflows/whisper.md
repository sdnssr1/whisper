---
description: Drop-in workspace rule for your Whisper project
---

<environment activation="always">
1. This repo targets macOS 14 on Apple Silicon.
2. External deps:
   - `ffmpeg` with `--enable-libopus --enable-libfdk-aac`
   - Python wheels should build against `llvm` not Apple Clang.
3. Virtual env lives in `.venv`; never touch system Python.
</environment>

<whisper-specific activation="model">
1. We use `openai-whisper` forked at commit abc123.
2. Prefer `ffmpeg-python` over spawning `subprocess` directly.
3. Streaming script is `live_transcribe.py`; optimise *that* first.
</whisper-specific>

<error_patterns activation="glob:\*.log">

1. If build fails on `_TYPE_CHLAYOUT` or similar ffmpeg/av errors,
   suggest:
   ```bash
   brew reinstall ffmpeg --HEAD
   CFLAGS="-Wno-deprecated-declarations" pip install --no-binary=av av
   ```
