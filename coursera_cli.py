#!/usr/bin/env python3
"""
Native Windows CLI for Coursera Downloader
Optimized entry point for PyInstaller builds

=======================================================================
WHEN TO USE THIS FILE vs coursera_dl.py DIRECTLY
=======================================================================

USE coursera_cli.py WHEN:
🎯 Building a standalone Windows executable with PyInstaller
🎯 You want a user-friendly CLI with enhanced help and validation
🎯 Creating a distributable version that doesn't require Python
🎯 You need argument validation and helpful error messages
🎯 Building for end-users who may not be familiar with Python

USE coursera_dl.py DIRECTLY WHEN:
🔧 You're a developer working with the source code
🔧 Integrating with other Python scripts or automation
🔧 You need direct access to the main_f() function
🔧 Building custom workflows or batch processing
🔧 You prefer minimal overhead and direct module access

=======================================================================
KEY DIFFERENCES
=======================================================================

coursera_cli.py Features:
✅ User-friendly banner and help system
✅ Argument validation with helpful error messages
✅ PyInstaller path resolution for frozen executables
✅ Progress feedback and status messages
✅ Graceful error handling with user-friendly messages
✅ Optimized for distribution as a standalone executable

coursera_dl.py Direct Usage:
✅ Direct function access without CLI wrapper
✅ Minimal overhead for programmatic usage
✅ Full access to internal functions and classes
✅ Better for automation and scripting
✅ Standard argparse help without custom formatting

=======================================================================
USAGE EXAMPLES
=======================================================================

# Using coursera_cli.py (this file):
python coursera_cli.py financial-accounting-basics -c cookies.txt
# OR as compiled executable:
coursera_downloader.exe financial-accounting-basics -c cookies.txt

# Using coursera_dl.py directly:
python coursera_dl.py financial-accounting-basics -c cookies.txt
# OR importing in your script:
from coursera_dl import main_f
main_f(['financial-accounting-basics', '-c', 'cookies.txt'])

=======================================================================
BUILD INTEGRATION
=======================================================================

PyInstaller Build Process:
1. build_windows_cli.py targets coursera_cli.py as entry point
2. This file handles frozen executable path resolution  
3. Creates optimized single-file Windows executable (coursera_downloader.exe)
4. Provides user-friendly CLI experience for end-users

For Development:
- Use coursera_dl.py directly for testing and development
- Use coursera_cli.py when building distributable executables

=======================================================================
 USAGE DECISION GUIDE
=======================================================================
 🤔 STILL UNSURE WHICH FILE TO USE?

 Quick Decision Tree:
 
 ❓ Are you building an executable?
    ✅ YES → Use coursera_cli.py (this file)
    ❌ NO  → Continue to next question

 ❓ Do you want user-friendly help and validation?
    ✅ YES → Use coursera_cli.py (this file)
    ❌ NO  → Continue to next question

 ❓ Are you integrating with other Python code?
    ✅ YES → Use coursera_dl.py directly
    ❌ NO  → Use coursera_cli.py (this file)

 📋 SUMMARY:
 - coursera_cli.py:  For executables and end-user CLI experience
 - coursera_dl.py:   For direct integration and development
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure the script can find modules when running as executable
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

def print_banner():
    """Print application banner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                 COURSERA DOWNLOADER CLI                   ║
╚═══════════════════════════════════════════════════════════╝
""")

def print_help():
    """Enhanced help information"""
    print_banner()
    print("""
🚀 QUICK START:
   coursera_downloader.exe <course-name> -c cookies.txt --video-resolution 720p

📝 EXAMPLES:
   coursera_downloader.exe financial-accounting-basics -c cookies.txt
   coursera_downloader.exe machine-learning -c cookies.txt --path "D:\\coursera" --video-resolution 720p
   coursera_downloader.exe data-science -c cookies.txt --download-quizzes --download-notebooks

🔑 AUTHENTICATION:
   Export cookies from your browser and save as cookies.txt
   Use -c or --cookies to specify the cookies file

📊 QUALITY OPTIONS:
   --video-resolution 360p   (Low quality, smaller files)
   --video-resolution 540p   (Medium quality, default)
   --video-resolution 720p   (High quality, recommended)

📁 DOWNLOAD OPTIONS:
   --path <directory>        Save location (default: current directory)
   --download-quizzes        Include quiz content
   --download-notebooks      Include Jupyter notebooks

🔄 RETRY OPTIONS:
   --resume                  Resume incomplete downloads
   --overwrite              Re-download existing files
   --disable-url-skipping   Force download all URLs

🐛 DEBUGGING:
   --debug                  Verbose output for troubleshooting

For full options, use: coursera_downloader.exe --help-full

📚 ALTERNATIVE USAGE OPTIONS:
   • coursera_cli.py       - This file (best for executables & end-users)
   • coursera_dl.py       - Direct module access (best for developers)
""")

def print_full_help():
    """Print full command line help"""
    try:
        from coursera_dl import get_parser
        parser = get_parser()
        parser.print_help()
    except:
        print("Full help not available. Use basic options above.")

def validate_args(args):
    """Validate common argument issues"""
    issues = []
    
    # Check for course name
    if not args or len(args) == 0:
        issues.append("❌ No course name provided")
    
    # Check for cookies file if specified
    cookies_specified = False
    for i, arg in enumerate(args):
        if arg in ['-c', '--cookies'] and i + 1 < len(args):
            cookies_file = args[i + 1]
            cookies_specified = True
            if not os.path.exists(cookies_file):
                issues.append(f"❌ Cookies file not found: {cookies_file}")
            elif os.path.getsize(cookies_file) == 0:
                issues.append(f"❌ Cookies file is empty: {cookies_file}")
        elif arg in ['-u', '--username', '-p', '--password']:
            issues.append("⚠️  Username/password authentication may not work. Consider using cookies file instead.")
    
    if not cookies_specified:
        for arg in args:
            if not arg.startswith('-'):
                issues.append("⚠️  No cookies file specified. Add -c cookies.txt for authentication.")
                break
    
    # Check video resolution
    for i, arg in enumerate(args):
        if arg == '--video-resolution' and i + 1 < len(args):
            resolution = args[i + 1]
            if resolution not in ['360p', '540p', '720p']:
                issues.append(f"❌ Invalid video resolution: {resolution}. Use 360p, 540p, or 720p")
    
    # Check path
    for i, arg in enumerate(args):
        if arg == '--path' and i + 1 < len(args):
            path = args[i + 1]
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"❌ Cannot create download path: {path} ({e})")
    
    return issues

def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    # Handle special help cases
    if not args or '--help' in args or '-h' in args:
        print_help()
        return 0
    
    if '--help-full' in args:
        print_full_help()
        return 0
    
    if '--version' in args:
        print("Coursera Downloader CLI - Native Windows Build")
        print("Based on coursera-dl project by multiple contributors")
        return 0
    
    # Validate arguments
    print_banner()
    issues = validate_args(args)
    
    if issues:
        print("🔍 ARGUMENT VALIDATION:")
        for issue in issues:
            print(f"   {issue}")
        
        if any("❌" in issue for issue in issues):
            print("\n💡 Use 'coursera_downloader.exe' (no arguments) for help")
            return 1
        else:
            print()  # Just warnings, continue
    
    # Show what we're about to do
    course_name = next((arg for arg in args if not arg.startswith('-') and args.index(arg) == 0), "unknown")
    print(f"📚 Course: {course_name}")
    
    # Find resolution
    resolution = "540p"  # default
    for i, arg in enumerate(args):
        if arg == '--video-resolution' and i + 1 < len(args):
            resolution = args[i + 1]
            break
    print(f"🎥 Video Quality: {resolution}")
    
    # Find download path
    download_path = "current directory"
    for i, arg in enumerate(args):
        if arg == '--path' and i + 1 < len(args):
            download_path = args[i + 1]
            break
    print(f"📁 Download to: {download_path}")
    
    # Check for additional content
    extras = []
    if '--download-quizzes' in args:
        extras.append("quizzes")
    if '--download-notebooks' in args:
        extras.append("notebooks")
    if extras:
        print(f"📋 Including: {', '.join(extras)}")
    
    print("🚀 Starting download...\n")
    
    try:
        # Import and run the main downloader
        from coursera_dl import main_f
        exit_code = main_f(args)
        
        if exit_code == 0:
            print("\n✅ Download completed successfully!")
        else:
            print(f"\n❌ Download failed with exit code: {exit_code}")
        
        return exit_code or 0
        
    except ImportError as e:
        print(f"❌ Error: Missing required dependencies: {e}")
        print("\nThis may be a packaging issue. Try reinstalling the application.")
        return 1
        
    except KeyboardInterrupt:
        print("\n🛑 Download interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\n💡 Try running with --debug for more information")
        return 1


if __name__ == "__main__":
    sys.exit(main())