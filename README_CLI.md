# Coursera Downloader - Native Windows CLI

A standalone Windows executable for downloading Coursera courses with high quality videos, subtitles, and course materials.

## 🏗️ CLI Architecture

This project provides **two ways** to use the Coursera downloader:

1. **Native Executable** (`coursera_downloader.exe`) - Standalone, no Python required
2. **Direct Module Access** (`coursera_dl.py`) - Core module, developer-focused

## 🤔 Which File Should You Use?

| Use Case | Recommended File | Why? |
|----------|------------------|------|
| **End User (No Python)** | `coursera_downloader.exe` | Standalone executable, no dependencies |
| **Developer/Integration** | `coursera_dl.py` | Direct access, programmatic usage |
| **Building Executable** | `coursera_cli.py` | Optimized for PyInstaller builds |

### Quick Decision:
- 🎯 **Want simple download?** → Use the executable
- 🔧 **Building automation?** → Use `coursera_dl.py` directly
- 📦 **Building for distribution?** → Use `coursera_cli.py` with build script

Both interfaces provide identical functionality with the same command-line options. Run the build script:

```bash
   python build_windows_cli.py
```   

## 📦 Quick Setup

### Option 1: Build from Source (Recommended)
1. Run the build script:
   ```bash
   python build_windows_cli.py
   ```
2. This creates:
   - `dist/coursera_downloader.exe` - The standalone executable (auto-generated)
   - `install.bat` - User-friendly installer script (auto-generated)
   - `coursera_downloader.spec` - PyInstaller configuration (auto-generated)

### Option 2: Python Script Usage
1. Use the Python module directly:
   ```bash
   python coursera_dl.py <course-name> [options]
   ```

## 🔐 Permissions Required

**Good News: No elevated permissions needed for normal usage!**

### Regular User Permissions ✅
- **Running the CLI**: No administrator rights required
- **Downloading courses**: Works with standard user account
- **Installation**: Installs to user directory (no admin needed)
- **Most download locations**: User folders, Desktop, Documents, etc.

### No Administrator Rights Required ✅
- **User-level installation**: Installs to %USERPROFILE%\CourseraDownloader
- **User PATH modification**: Updates user environment only
- **Portable usage**: Can run directly from any folder without installation

### Recommended Setup
```cmd
# Create folder in your user directory (no admin needed)
mkdir "%USERPROFILE%\Coursera"

# Download courses there
coursera_downloader.exe course-name -c cookies.txt --path "%USERPROFILE%\Coursera"
```

## 🔑 Coursera Authentication Setup

1. **Login to Coursera** in your browser (Chrome, Edge, Firefox)
2. **Export cookies** using a browser extension (cookies.txt format)
3. **Save the file** as `cookies.txt` in your download directory
4. **Use the `-c` option** to specify the cookies file

## 📚 Finding the Course Name

To download a course, you need the **course name** from the Coursera URL:

### URL Structure
```
https://www.coursera.org/learn/[COURSE-NAME]/home/module/1
                              ^^^^^^^^^^^
                              This is what you need
```

### Examples
| Coursera URL | Course Name |
|--------------|-------------|
| `https://www.coursera.org/learn/financial-accounting-basics/home/module/1` | `financial-accounting-basics` |
| `https://www.coursera.org/learn/machine-learning/home/week/1` | `machine-learning` |
| `https://www.coursera.org/learn/data-science-fundamentals/lecture/abc123` | `data-science-fundamentals` |
| `https://www.coursera.org/learn/algorithms-part1/programming/xyz789` | `algorithms-part1` |

### How to Find It
1. **Go to the course page** on Coursera
2. **Look at the URL** in your browser's address bar
3. **Find the part after `/learn/`** and before the next `/`
4. **That's your course name** - use it in the download command

### Common Course Names
- `financial-accounting-basics`
- `machine-learning`
- `data-science`
- `algorithms-part1`
- `algorithms-part2`
- `deep-learning`
- `python-for-everybody`
- `digital-marketing`

## 🎯 Basic Usage

### Quick Reference
1. **Find course name**: Look at URL `https://www.coursera.org/learn/[COURSE-NAME]/...`
2. **Export cookies**: Save as `cookies.txt` 
3. **Run download**: Use course name in command

### Using the Built Executable
```cmd
# Download a course
coursera_downloader.exe financial-accounting-basics -c cookies.txt

# High quality download
coursera_downloader.exe machine-learning -c cookies.txt --video-resolution 720p

# Full download with extras
coursera_downloader.exe data-science -c cookies.txt --download-quizzes --download-notebooks --video-resolution 720p --path "D:\Coursera"
```

### Using Python Script
```cmd
# Download a course
python coursera_dl.py financial-accounting-basics -c cookies.txt

# High quality download  
python coursera_dl.py machine-learning -c cookies.txt --video-resolution 720p

# Full download with extras
python coursera_dl.py data-science -c cookies.txt --download-quizzes --download-notebooks --video-resolution 720p --path "D:\Coursera"
```

## 🛠️ Command Options

### Essential Options
| Option | Description | Example |
|--------|-------------|---------|
| `-c <file>` | Cookies file for authentication | `-c cookies.txt` |
| `--video-resolution` | Video quality (360p/540p/720p) | `--video-resolution 720p` |
| `--path <dir>` | Download directory | `--path "D:\Coursera"` |

### Content Options
| Option | Description |
|--------|-------------|
| `--download-quizzes` | Include quiz content |
| `--download-notebooks` | Include Jupyter notebooks |
| `--formats <list>` | Specific formats (mp4, pdf, etc.) |

### Retry Options
| Option | Description |
|--------|-------------|
| `--resume` | Resume incomplete downloads |
| `--overwrite` | Re-download existing files |
| `--disable-url-skipping` | Force download all URLs |

### Debug Options
| Option | Description |
|--------|-------------|
| `--debug` | Verbose output for troubleshooting |
| `--jobs <n>` | Number of parallel downloads |

## 📁 File Organization

Downloads are organized in a clear hierarchy:

```
<download-path>/
├── <course-name>/
│   ├── 01_course-orientation/
│   │   ├── 01_about-the-course/
│   │   │   ├── 01_meet-professor.mp4
│   │   │   ├── 01_meet-professor.en.srt
│   │   │   ├── 01_meet-professor.es.srt
│   │   │   └── 01_meet-professor.en.txt
│   │   └── 02_syllabus/
│   ├── 02_module-1-introduction/
│   │   ├── 01_lesson-1-overview/
│   │   └── 02_lesson-1-content/
│   └── 03_module-2-advanced/
```

## 🔄 Common Scenarios

### First Time Download
```cmd
# Using executable
coursera_downloader.exe financial-accounting-basics -c cookies.txt --video-resolution 720p --path "D:\Coursera" --download-quizzes --download-notebooks

# Using Python script
python coursera_dl.py financial-accounting-basics -c cookies.txt --video-resolution 720p --path "D:\Coursera" --download-quizzes --download-notebooks
```

### Resume Failed Download
```cmd
# Using executable
coursera_downloader.exe financial-accounting-basics -c cookies.txt --resume --disable-url-skipping

# Using Python script
python coursera_dl.py financial-accounting-basics -c cookies.txt --resume --disable-url-skipping
```

### Re-download Everything
```cmd
# Using executable
coursera_downloader.exe financial-accounting-basics -c cookies.txt --overwrite --video-resolution 720p

# Using Python script
python coursera_dl.py financial-accounting-basics -c cookies.txt --overwrite --video-resolution 720p
```

### Debug Connection Issues
```cmd
# Using executable
coursera_downloader.exe financial-accounting-basics -c cookies.txt --debug

# Using Python script
python coursera_dl.py financial-accounting-basics -c cookies.txt --debug
```

## 🆘 Troubleshooting

### Course Name Issues
- **Wrong course name**: Check the URL structure `/learn/[COURSE-NAME]/`
- **Course not found**: Verify you're enrolled in the course
- **Invalid characters**: Course names use dashes, not spaces (e.g., `machine-learning` not `machine learning`)

### Authentication Issues
- **Cookies expired**: Re-export cookies from your browser
- **Login required**: Make sure you're logged into Coursera when exporting cookies
- **Access denied**: Check if you're enrolled in the course

### Download Issues
- **Failed downloads**: Use `--resume --disable-url-skipping`
- **Partial files**: Use `--overwrite` to re-download
- **Slow downloads**: Adjust `--jobs <number>` (default: 1)

### File Issues
- **Permission denied**: Usually means protected folder - try user directories instead
  - ✅ Good: `%USERPROFILE%\Coursera` (no admin needed)
  - ❌ Avoid: `C:\Program Files\` (requires admin)
- **Disk space**: Check available space in download directory
- **Path errors**: Use quotes around paths with spaces

### Permission Troubleshooting
- **CLI won't run**: Check if antivirus is blocking the executable
- **Can't write files**: Ensure download path is writable by your user account
- **Access denied to folder**: Choose a folder in your user directory (Documents, Downloads, Desktop)
- **Installation issues**: CLI installs to user directory automatically - no admin rights needed

## 💡 Pro Tips

1. **Use 720p** for best quality (file sizes will be larger)
2. **Set a dedicated download folder** to keep courses organized
3. **Export fresh cookies** if you get authentication errors
4. **Use --resume** for large courses that might get interrupted
5. **Check disk space** before starting large course downloads
6. **Keep cookies.txt secure** - it contains your session information

## 🔧 Advanced Usage

### Batch Download Multiple Courses
Create a batch file:
```batch
@echo off
coursera_downloader.exe machine-learning -c cookies.txt --video-resolution 720p --path "D:\Coursera"
coursera_downloader.exe data-science -c cookies.txt --video-resolution 720p --path "D:\Coursera"
coursera_downloader.exe financial-accounting-basics -c cookies.txt --video-resolution 720p --path "D:\Coursera"
```

Or using Python scripts:
```batch
@echo off
python coursera_dl.py machine-learning -c cookies.txt --video-resolution 720p --path "D:\Coursera"
python coursera_dl.py data-science -c cookies.txt --video-resolution 720p --path "D:\Coursera"
python coursera_dl.py financial-accounting-basics -c cookies.txt --video-resolution 720p --path "D:\Coursera"
```

### Download Only Videos (No Subtitles)
```cmd
# Executable
coursera_downloader.exe course-name -c cookies.txt --formats mp4

# Python script
python coursera_dl.py course-name -c cookies.txt --formats mp4
```

### Download with Custom Parallel Jobs
```cmd
# Executable
coursera_downloader.exe course-name -c cookies.txt --jobs 3 --video-resolution 720p

# Python script
python coursera_dl.py course-name -c cookies.txt --jobs 3 --video-resolution 720p
```

## 📞 Getting Help

### Executable Help
- Run `coursera_downloader.exe` (no arguments) for quick help
- Run `coursera_downloader.exe --help-full` for complete options
- Use `--debug` flag to see detailed operation logs

### Python Script Help
- Run `python coursera_dl.py` (no arguments) for quick help
- Run `python coursera_dl.py --help` for complete options
- Use `--debug` flag to see detailed operation logs

### Build Help
- Run `python build_windows_cli.py` to create the executable
- See build documentation in the script comments

## 🛠️ Technical Implementation

### File Structure
- `coursera_cli.py` - Main CLI entry point for executable builds
- `coursera_workflow.py` - Core workflow logic
- `build_windows_cli.py` - Build script for creating Windows executable
- `README_CLI.md` - This documentation

### Build Requirements
- Windows 10/11
- Python 3.8+
- PyInstaller (automatically installed by build script)
- All dependencies from requirements.txt

### Output
- **Executable Size**: ~17.5MB standalone file
- **Dependencies**: All bundled, no Python installation required for end users
- **Compatibility**: Windows x64 systems