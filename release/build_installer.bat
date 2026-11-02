@echo off
setlocal
cd /d "%~dp0.."

if not exist "release\artifacts\app\CourseraDownloader\CourseraDownloader.exe" (
    echo The app has not been built yet.
    echo Run release\build_app.bat first.
    pause
    exit /b 1
)

set "ISCC_EXE="
where ISCC.exe >nul 2>nul && set "ISCC_EXE=ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not defined ISCC_EXE (
    echo Inno Setup 6 was not found.
    echo Install it from https://jrsoftware.org/isinfo.php, then try again.
    pause
    exit /b 1
)

echo Building the Windows installer...
"%ISCC_EXE%" "release\config\installer.iss"
if errorlevel 1 (
    echo.
    echo Installer build failed.
    pause
    exit /b 1
)

echo.
echo Installer build complete:
echo release\artifacts\installers
pause
