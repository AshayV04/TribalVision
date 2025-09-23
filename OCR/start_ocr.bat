@echo off
echo Starting FRA OCR API Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "flask_ocr_api.py" (
    echo Error: Please run this script from the OCR directory
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    echo.
)

REM Run the startup script
echo Starting OCR API server...
python start_ocr_api.py

pause
