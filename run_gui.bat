@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "APP_PYTHON=.venv\Scripts\python.exe"
    set "APP_PYTHONW=.venv\Scripts\pythonw.exe"
    goto launch
)

where python >nul 2>nul || (
    echo Python was not found.
    pause
    exit /b 1
)
set "APP_PYTHON=python"
where pythonw >nul 2>nul && (set "APP_PYTHONW=pythonw") || (set "APP_PYTHONW=python")

:launch
"%APP_PYTHON%" -c "import PySide6, webview" >nul 2>nul
if errorlevel 1 (
    echo Installing the required GUI components...
    "%APP_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Installation failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

start "" "%APP_PYTHONW%" main.py
exit /b 0
