"""Locations of the app's files, from source and in the packaged (PyInstaller) app."""

import os
import sys

if getattr(sys, "frozen", False):
    # Packaged app: bundled files (data.bin, the icon) are in the bundle folder.
    APP_ROOT = sys._MEIPASS
else:
    # From source: the project folder, which holds main.py and src/.
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Script that starts the app; also run as a helper for the embedded login window.
MAIN_SCRIPT = os.path.join(APP_ROOT, "main.py")
ICON_FILE = os.path.join(APP_ROOT, "assets", "icon", "icon.ico")


def app_file(name):
    """Path of a file kept next to the app, such as the settings file."""
    return os.path.join(APP_ROOT, name)
