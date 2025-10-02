#!/bin/bash

echo "Starting FRA OCR API Server..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "flask_ocr_api.py" ]; then
    echo "Error: Please run this script from the OCR directory"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    echo
fi

# Make the startup script executable
chmod +x start_ocr_api.py

# Run the startup script
echo "Starting OCR API server..."
python3 start_ocr_api.py
