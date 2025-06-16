import PyInstaller.__main__

PyInstaller.__main__.run([
    'whisper_app.py',
    '--onefile',
    '--windowed',
    '--name=WhisperLive',
    '--icon=icon.icns',
    '--add-data=whisper_app.py:.',
    '--add-data=LICENSE:.',
    '--hidden-import=whisper',
    '--hidden-import=numpy',
    '--hidden-import=numba',
    '--hidden-import=sounddevice',
    '--hidden-import=scipy',
])
