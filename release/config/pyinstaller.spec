# -*- mode: python ; coding: utf-8 -*-
import os

# This file is release/config/pyinstaller.spec.
ROOT = os.path.abspath(os.path.join(SPECPATH, '..', '..'))


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
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # pywebview's hook would also pull in any other installed Qt library;
    # the app uses PySide6 and pywebview's Edge (WebView2) backend only.
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(ROOT, 'assets', 'icon', 'icon.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CourseraDownloader',
)
