@echo off
echo ================================================
echo NTU Travel Management System - Startup Script
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r app\requirements.txt >nul 2>&1
echo [OK] Dependencies installed

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env >nul
    echo [OK] .env file created
)

echo.
echo ================================================
echo Starting NTU Travel Management System...
echo ================================================
echo.
echo API Documentation will be available at:
echo   -^> http://localhost:8000/docs
echo   -^> http://localhost:8000/redoc
echo.
echo Health Check:
echo   -^> http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the application
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
