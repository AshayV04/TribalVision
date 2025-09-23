#!/usr/bin/env python3
"""
Startup script for FRA OCR API
This script initializes the database and starts the Flask server
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        # Check for numpy source directory issue
        import os
        import sys
        
        # Remove current directory from path to avoid numpy source directory issues
        current_dir = os.getcwd()
        if current_dir in sys.path:
            sys.path.remove(current_dir)
        
        import flask
        import pytesseract
        import PIL
        import pdf2image
        import google.generativeai
        import pandas
        import numpy
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR is available")
        return True
    except Exception as e:
        print(f"❌ Tesseract OCR not found: {e}")
        print("Please install Tesseract OCR:")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")
        return False

def initialize_database():
    """Initialize the SQLite database"""
    try:
        conn = sqlite3.connect('fra_claims.db')
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fra_claim_individual (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_filename TEXT,
                claimant_name TEXT,
                spouse_name TEXT,
                father_or_mother_name TEXT,
                address TEXT,
                village TEXT,
                gram_panchayat TEXT,
                tehsil_taluka TEXT,
                district TEXT,
                state TEXT,
                is_scheduled_tribe TEXT,
                is_otfd TEXT,
                land_area TEXT,
                raw_text TEXT,
                ocr_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending_review'
            )
        """)
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting FRA OCR API...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('flask_ocr_api.py'):
        print("❌ Please run this script from the OCR directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Tesseract
    if not check_tesseract():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 All checks passed! Starting Flask server...")
    print("📡 API will be available at: http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000/api/health")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start Flask server
    try:
        from flask_ocr_api import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
