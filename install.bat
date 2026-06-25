@echo off
title AI Video Automation Agent - Installer
color 0A

echo ============================================
echo   AI Video Automation Agent - Installer
echo ============================================
echo.

:: Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo [OK] Python found.
echo.

:: Check pip
echo [2/4] Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not found. Please reinstall Python with pip.
    pause
    exit /b 1
)
echo [OK] pip found.
echo.

:: Install dependencies
echo [3/4] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

:: Check FFmpeg
echo [4/4] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg is not installed or not in PATH.
    echo FFmpeg is required for video processing.
    echo Download from: https://ffmpeg.org/download.html
    echo Add ffmpeg.exe to your system PATH.
    echo.
    echo The app will still start but video editing features won't work.
) else (
    echo [OK] FFmpeg found.
)
echo.

:: Create .env if not exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo [OK] .env file created. Please add your Gemini API key.
) else (
    echo [OK] .env file already exists.
)
echo.

echo ============================================
echo   Installation Complete!
echo   Run start.bat to launch the application.
echo ============================================
pause
