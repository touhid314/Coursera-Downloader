@echo off
setlocal
cd /d "%~dp0.."

set "APP_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "APP_PYTHON=.venv\Scripts\python.exe"

echo Building Coursera Downloader...
"%APP_PYTHON%" -m PyInstaller release\config\pyinstaller.spec --noconfirm --clean ^
    --distpath release\artifacts\app --workpath release\work
if errorlevel 1 (
    echo.
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo App build complete:
echo release\artifacts\app\CourseraDownloader
echo.
echo Next, run release\build_installer.bat.
pause
