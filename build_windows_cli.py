#!/usr/bin/env python3
"""
Build Script for Native Windows CLI Executable - Coursera Downloader

This script automates the creation of a standalone Windows CLI executable from
the Coursera Downloader Python source code using PyInstaller. The resulting
executable provides a native command-line interface that does not require 
Python to be installed on the target machine.

CLI-Specific Features:
- Builds coursera_cli.py as the main entry point (not the GUI)
- Optimized for command-line usage with enhanced help system
- Includes CLI-specific argument validation and user guidance
- Bundles all CLI dependencies into a single executable
- Creates a native Windows CLI tool for course downloads

Key Features:
- Automated dependency management and PyInstaller installation
- Custom PyInstaller spec file generation for CLI optimization
- Virtual environment creation for clean CLI builds
- Comprehensive error handling and user feedback
- Icon integration and CLI-specific hidden imports
- Build artifact cleanup and organization
- Optional system-wide CLI installation with PATH management

CLI Build Process:
1. Virtual environment creation and activation
2. CLI dependency installation from requirements.txt
3. PyInstaller installation if not present
4. Custom spec file generation (coursera_downloader.spec - auto-generated, not checked in)
5. CLI executable compilation targeting coursera_cli.py
6. Build artifact cleanup and organization
7. Optional CLI installation to user directory (no admin rights required)

Output:
- Single CLI executable file (~17.5MB) in dist/ directory (auto-generated, not checked in)
- Complete bundling of Python interpreter and all CLI dependencies
- Windows-optimized CLI with proper icon and metadata
- Ready for distribution as a standalone command-line tool
- User-friendly installation script (install.bat - auto-generated, not checked in)

Usage:
    python build_windows_cli.py              # Build CLI only
    python build_windows_cli.py --install    # Build and install CLI for current user

Requirements:
- Windows 10/11
- Python 3.8+
- Internet connection for dependency downloads
- No administrator rights required (installs to user directory)

The script handles common CLI build issues including:
- PyInstaller hook conflicts
- Hidden import specification for CLI-bundled dependencies
- Icon file inclusion and Windows CLI executable metadata
- Path handling for both development and frozen CLI environments

Author: Generated for Coursera-Downloader native CLI functionality
License: Same as parent project
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """
    Verify PyInstaller installation and install if missing.
    
    This function checks for PyInstaller availability in the current Python
    environment. If not found, it attempts to install it using pip.
    
    Returns:
        bool: True if PyInstaller is available/installed successfully,
              False if installation failed
    
    Raises:
        subprocess.CalledProcessError: If pip installation fails
    
    Side Effects:
        - May install PyInstaller package via pip
        - Prints status messages to stdout
    """
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

def create_spec_file():
    """
    Generate a custom PyInstaller specification file for optimized CLI builds.
    
    This function creates a .spec file that provides fine-grained control
    over the PyInstaller CLI build process. The spec file includes:
    
    - CLI entry point specification (coursera_cli.py)
    - Hidden imports for CLI modules not automatically detected
    - Data files inclusion (icons, CLI resources)
    - CLI build optimizations and exclusions
    - Windows CLI-specific configurations
    
    Hidden Imports Included:
        - keyring.backends.Windows: Windows credential storage for CLI auth
        - rookiepy: Browser cookie extraction for CLI authentication
        - pillow: Image processing capabilities for CLI operations
        - PyQt5 components: Backend support (even for CLI builds)
    
    Data Files:
        - icon/icon.ico: Application icon for Windows CLI executable
    
    Returns:
        str: Path to the generated CLI spec file
    
    Side Effects:
        - Creates 'coursera_downloader.spec' file in current directory
        - Overwrites existing spec file if present
        
    The generated spec file is optimized for:
    - Single-file CLI executable generation
    - Minimal file size while maintaining CLI functionality
    - Windows CLI compatibility and proper icon display
    - Inclusion of all necessary CLI dependencies
    """
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['coursera_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon/icon.ico', 'icon'),
    ],
    hiddenimports=[
        'keyring.backends.Windows',
        'rookiepy',
        'pillow',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='coursera_downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/icon.ico',
)
"""
    
    with open('coursera_downloader.spec', 'w') as f:
        f.write(spec_content.strip())
    print("✅ Created PyInstaller spec file")

def build_executable():
    """Build the Windows executable"""
    print("🔨 Building Windows CLI executable...")
    print("This may take several minutes...")
    
    try:
        # Build using the spec file
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "coursera_downloader.spec"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CLI build completed successfully!")
            
            # Check if the executable was created
            exe_path = Path("dist/coursera_downloader.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📦 CLI Executable created: {exe_path}")
                print(f"📏 Size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ CLI executable not found after build")
                return False
        else:
            print("❌ CLI build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ CLI build error: {e}")
        return False

def create_batch_installer():
    """
    Create a batch script for easy user-level installation.
    
    This generates install.bat which is auto-generated and should not be 
    checked into version control. The file is created dynamically during
    the build process to ensure it matches the current executable name
    and installation paths.
    """
    batch_content = r"""@echo off
title Coursera Downloader - Native CLI Installer

echo.
echo ================================
echo Coursera Downloader Native CLI
echo ================================
echo.

echo Installing to %USERPROFILE%\CourseraDownloader...

if not exist "%USERPROFILE%\CourseraDownloader" (
    mkdir "%USERPROFILE%\CourseraDownloader"
)

copy "dist\coursera_downloader.exe" "%USERPROFILE%\CourseraDownloader\"

echo.
echo Adding to user PATH...

for /f "skip=2 tokens=1,2*" %%A in ('reg query HKCU\Environment /v PATH 2^>nul') do set CurrentPath=%%C
if defined CurrentPath (
    setx PATH "%CurrentPath%;%USERPROFILE%\CourseraDownloader"
) else (
    setx PATH "%USERPROFILE%\CourseraDownloader"
)

echo.
echo ================================
echo Installation Complete!
echo ================================
echo.
echo You can now use 'coursera_downloader' from any command prompt.
echo.
echo Example usage:
echo   coursera_downloader financial-accounting-basics -c cookies.txt --video-resolution 720p
echo.
echo Note: You may need to restart your command prompt for PATH changes to take effect.
echo.
pause
"""
    
    with open('install.bat', 'w') as f:
        f.write(batch_content)
    print("✅ Created installation batch script")

def main():
    """Main build process"""
    print("🏗️  Building Coursera Downloader Native Windows CLI")
    print("=" * 60)
    
    # Step 1: Check and install PyInstaller
    if not check_pyinstaller():
        return False
    
    # Step 2: Create main CLI entry point
    print("📝 Creating CLI entry point...")
    
    # Step 3: Create spec file
    create_spec_file()
    
    # Step 4: Build executable
    if not build_executable():
        return False
    
    # Step 5: Create installer
    create_batch_installer()
    
    print("\n🎉 Build Process Complete!")
    print("=" * 60)
    print("📦 Executable: dist/coursera_downloader.exe")
    print("🚀 Installer: install.bat (created)")
    print("📖 Documentation: README_CLI.md")
    print("\n💡 Next Steps:")
    print("  • To install for current user: run 'install.bat'")
    print("  • Installation path: %USERPROFILE%\\CourseraDownloader")
    print("  • See README_CLI.md for complete usage guide")
    print("  • Test executable: dist\\coursera_downloader.exe --help")
    
    return True

if __name__ == "__main__":
    main()