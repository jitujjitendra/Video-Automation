@echo off
title AI Video Automation Agent
color 0B

echo ============================================
echo   AI Video Automation Agent - Starting...
echo ============================================
echo.

:: Check if .env exists
if not exist .env (
    echo [WARNING] No .env file found. Creating from template...
    copy .env.example .env >nul
    echo Please edit .env and add your Gemini API key.
    echo.
)

:: Start the backend server
echo Starting FastAPI backend server...
echo Server will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:8000/static
echo.
echo Press Ctrl+C to stop the server.
echo.

:: Open browser after a short delay
start "" cmd /c "timeout /t 3 >nul && start http://localhost:8000/static/index.html"

:: Run the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
