"""Locations of the app's files, from source and in the packaged (PyInstaller) app."""

import os
import shutil
import sys

IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
APP_DATA_FOLDER = "CourseraDownloader"

if getattr(sys, "frozen", False):
    # Packaged app: bundled files (data.bin, the icon) are in the bundle folder.
    APP_ROOT = sys._MEIPASS
else:
    # From source: the project folder, which holds main.py and src/.
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Script that starts the app; also run as a helper for the embedded login window.
MAIN_SCRIPT = os.path.join(APP_ROOT, "main.py")
# Only Windows gets the .ico file; macOS and Linux use the PNG.
ICON_FILE = os.path.join(
    APP_ROOT, "assets", "icon", "icon.ico" if IS_WINDOWS else "icon.png"
)


def user_data_dir():
    """Folder for the user's own app data (settings, the login window's storage)."""
    if IS_MACOS:
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "share"
        )
    return os.path.join(base, APP_DATA_FOLDER)


def app_file(name):
    """
    Path of a file the app reads and writes, such as the settings file.

    On Windows it is kept next to the app. A macOS app bundle must not be
    changed (that breaks its signature, and it may be read-only), and a Linux
    install may not be writable, so the packaged Mac and Linux apps keep it in
    the user's data folder, starting from the bundled copy.
    """
    if IS_WINDOWS or not getattr(sys, "frozen", False):
        return os.path.join(APP_ROOT, name)

    folder = user_data_dir()
    os.makedirs(folder, exist_ok=True)
    user_copy = os.path.join(folder, name)
    bundled_copy = os.path.join(APP_ROOT, name)
    if not os.path.exists(user_copy) and os.path.isfile(bundled_copy):
        shutil.copyfile(bundled_copy, user_copy)
    return user_copy
