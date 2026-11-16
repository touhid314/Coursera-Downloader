# -*- mode: python ; coding: utf-8 -*-
import os
import re
import sys

# This file is release/config/pyinstaller.spec. It builds the Windows and Linux
# app folders and, on macOS, the CourseraDownloader.app bundle.
ROOT = os.path.abspath(os.path.join(SPECPATH, '..', '..'))
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# On Linux the login window uses pywebview's Qt backend, loaded at run time.
LINUX_HIDDEN_IMPORTS = [
    'webview.platforms.qt',
    'qtpy',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebChannel',
    'PySide6.QtNetwork',
]

with open(os.path.join(ROOT, 'src', '__init__.py'), encoding='utf-8') as f:
    VERSION = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)

# PyInstaller turns the PNG into the .icns file a Mac app needs (with Pillow).
# Linux programs have no embedded icon; the installer's menu entry uses the PNG.
ICON = os.path.join(ROOT, 'assets', 'icon', 'icon.png' if IS_MACOS else 'icon.ico')


a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, 'default_data', 'data.bin'), '.'),
        (
            os.path.join(ROOT, 'assets', 'icon', 'icon.ico'),
            os.path.join('assets', 'icon'),
        ),
        (
            os.path.join(ROOT, 'assets', 'icon', 'icon.png'),
            os.path.join('assets', 'icon'),
        ),
    ],
    hiddenimports=LINUX_HIDDEN_IMPORTS if IS_LINUX else [],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # pywebview's hook would also pull in any other installed Qt library;
    # the app uses PySide6, and pywebview's Edge (WebView2) backend on Windows
    # or its Cocoa (WebKit) backend on macOS.
    excludes=['PyQt5', 'PyQt6', 'PySide2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CourseraDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX breaks the code signature of macOS binaries.
    upx=not IS_MACOS,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[ICON],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=not IS_MACOS,
    upx_exclude=[],
    name='CourseraDownloader',
)

if IS_MACOS:
    app = BUNDLE(
        coll,
        name='CourseraDownloader.app',
        icon=ICON,
        bundle_identifier='io.github.touhid314.courseradownloader',
        version=VERSION,
        info_plist={
            'CFBundleDisplayName': 'Coursera Full Course Downloader',
            'CFBundleName': 'Coursera Downloader',
            'CFBundleShortVersionString': VERSION,
            'CFBundleVersion': VERSION,
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,  # follow dark mode
            'LSMinimumSystemVersion': '13.0',
            'NSHumanReadableCopyright': 'Copyright (c) Touhidul Islam',
        },
    )
