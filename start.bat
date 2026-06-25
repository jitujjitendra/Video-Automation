@echo off
title AI Video Automation Agent
echo.

:: Enable ANSI color support
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
    set "ESC=%%b"
)

echo %ESC%[36m
echo     _    ___  __     ___     _
echo    / \  |_ _| \ \   / (_) __| | ___  ___
echo   / _ \  | |   \ \ / /| |/ _` |/ _ \/ _ \
echo  / ___ \ | |    \ V / | | (_| |  __/ (_) |
echo /_/   \_\___|    \_/  |_|\__,_|\___|\___/
echo.
echo       A U T O M A T I O N   A G E N T
echo %ESC%[0m
echo %ESC%[36m============================================%ESC%[0m
echo %ESC%[36m         Starting Server v1.0.0%ESC%[0m
echo %ESC%[36m============================================%ESC%[0m
echo.

:: Show system info
echo %ESC%[33m[System Info]%ESC%[0m
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo   Python: %%v
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   FFmpeg: %ESC%[31mNot found%ESC%[0m (video assembly disabled)
) else (
    echo   FFmpeg: %ESC%[32mInstalled%ESC%[0m
)
echo.

:: Check if .env exists
if not exist .env (
    echo %ESC%[33m[WARNING]%ESC%[0m No .env file found.
    echo.
    set /p "API_KEY=Enter your Gemini API Key (or press Enter to skip): "
    if defined API_KEY (
        echo GEMINI_API_KEY=%API_KEY%> .env
        echo %ESC%[32m[OK]%ESC%[0m .env file created with your API key.
    ) else (
        if exist .env.example (
            copy .env.example .env >nul
        ) else (
            echo GEMINI_API_KEY=your_gemini_api_key_here> .env
        )
        echo %ESC%[33m[INFO]%ESC%[0m Created .env with placeholder. Edit it to add your key.
    )
    echo.
)

:: Check if dependencies are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo %ESC%[33m[WARNING]%ESC%[0m Dependencies not installed. Running install...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo %ESC%[31m[ERROR]%ESC%[0m Failed to install dependencies. Run install.bat first.
        pause
        exit /b 1
    )
    echo.
)

:: Display server info
echo %ESC%[32m   Server starting...%ESC%[0m
echo.
echo   Application URL: %ESC%[36mhttp://localhost:8000%ESC%[0m
echo   API Docs:        %ESC%[36mhttp://localhost:8000/docs%ESC%[0m
echo   Online Demo:     %ESC%[36mhttps://jitujjitendra.github.io/Video-Automation/%ESC%[0m
echo.
echo   Press Ctrl+C to stop the server.
echo %ESC%[36m============================================%ESC%[0m
echo.

:: Open browser after a short delay
start "" cmd /c "timeout /t 2 >nul && start http://localhost:8000"

:: Run the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
