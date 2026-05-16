<!--
*********************************************
CWGAME Ver.1.0 by JA1XPM 2026.05.17
*********************************************
-->

# CWGAME Ver.1.0

CWGAME Ver.1.0 is a Tkinter-based Morse code typing game.

Characters and their Morse code fall from the top of the window. Use the left mouse button to enter Morse code:

- Short click: dot
- Long click: dash

When the entered Morse code matches a falling character before it crosses the red line, the score increases.

## Version

Ver.1.0 is based on `cwgame.py` renamed from `7cwgame.py`. This version is treated as the first formal release because it is the first version confirmed to work properly.

## Requirements

- Python 3.10 or later
- Tkinter
- pynput

Install the Python dependency with:

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python cwgame.py
```

## Build

A PyInstaller spec file is included for Ver.1.0:

```powershell
pyinstaller cwgame.spec
```

Build outputs are intentionally excluded from Git by `.gitignore`.

## Archive

Older development files are kept in `archive/` for reference. They are not treated as the formal Ver.1.0 source.