@echo off
title AI Video Automation Agent - Installer
echo.

:: Enable ANSI color support
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
    set "ESC=%%b"
)

echo %ESC%[36m============================================%ESC%[0m
echo %ESC%[36m   AI Video Automation Agent - Installer%ESC%[0m
echo %ESC%[36m============================================%ESC%[0m
echo.

:: Check Python version (require 3.9+)
echo %ESC%[33m[1/5]%ESC%[0m Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo %ESC%[31m[ERROR]%ESC%[0m Python is not installed or not in PATH.
    echo         Please install Python 3.9+ from https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Verify Python version is 3.9+
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)
if %PYMAJOR% LSS 3 (
    echo %ESC%[31m[ERROR]%ESC%[0m Python 3.9+ required. Found: %PYVER%
    pause
    exit /b 1
)
if %PYMAJOR%==3 if %PYMINOR% LSS 9 (
    echo %ESC%[31m[ERROR]%ESC%[0m Python 3.9+ required. Found: %PYVER%
    echo         Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo %ESC%[32m[OK]%ESC%[0m Python %PYVER% found.
echo.

:: Check pip
echo %ESC%[33m[2/5]%ESC%[0m Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo %ESC%[31m[ERROR]%ESC%[0m pip is not found. Please reinstall Python with pip enabled.
    pause
    exit /b 1
)
echo %ESC%[32m[OK]%ESC%[0m pip found.
echo.

:: Install dependencies
echo %ESC%[33m[3/5]%ESC%[0m Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo %ESC%[31m[ERROR]%ESC%[0m Failed to install dependencies.
    echo         Try running: pip install -r requirements.txt --user
    pause
    exit /b 1
)
echo %ESC%[32m[OK]%ESC%[0m Dependencies installed.
echo.

:: Check FFmpeg
echo %ESC%[33m[4/5]%ESC%[0m Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo %ESC%[33m[WARNING]%ESC%[0m FFmpeg is not installed or not in PATH.
    echo          FFmpeg is required for video processing.
    echo.
    echo          Download FFmpeg:
    echo            https://www.gyan.dev/ffmpeg/builds/
    echo            (Get "ffmpeg-release-essentials.zip")
    echo.
    echo          After downloading:
    echo            1. Extract the zip file
    echo            2. Add the "bin" folder to your system PATH
    echo            3. Restart this installer to verify
    echo.
    echo          The app will start but video editing features won't work.
) else (
    echo %ESC%[32m[OK]%ESC%[0m FFmpeg found.
)
echo.

:: Setup project files
echo %ESC%[33m[5/5]%ESC%[0m Setting up project files...

:: Create .env if not exists
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo      Created .env file from template.
        echo      %ESC%[33mPlease edit .env and add your Gemini API key.%ESC%[0m
    ) else (
        echo GEMINI_API_KEY=your_key_here> .env
        echo      Created .env file. Please add your Gemini API key.
    )
) else (
    echo      .env file already exists.
)

:: Create outputs directory
if not exist outputs (
    mkdir outputs
    echo      Created outputs/ directory.
) else (
    echo      outputs/ directory already exists.
)

echo %ESC%[32m[OK]%ESC%[0m Project setup complete.
echo.

echo %ESC%[32m============================================%ESC%[0m
echo %ESC%[32m   Installation Complete!%ESC%[0m
echo %ESC%[32m============================================%ESC%[0m
echo.
echo   Next steps:
echo     1. Edit .env and add your GEMINI_API_KEY
echo     2. Run start.bat to launch the application
echo.
pause
