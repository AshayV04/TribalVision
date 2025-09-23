#!/usr/bin/env python3
"""
Test script for FRA OCR functionality
This script tests the OCR processing without requiring the full Flask server
"""

import os
import sys
import json
from PIL import Image
import pytesseract

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tesseract():
    """Test if Tesseract OCR is working"""
    print("🔍 Testing Tesseract OCR...")
    try:
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a white image
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add text to the image
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        draw.text((10, 30), "FRA Claim Form Test", fill='black', font=font)
        draw.text((10, 50), "Claimant: John Doe", fill='black', font=font)
        draw.text((10, 70), "Village: Test Village", fill='black', font=font)
        
        # Save test image
        test_image_path = "test_image.png"
        img.save(test_image_path)
        print(f"✅ Created test image: {test_image_path}")
        
        # Test OCR
        text = pytesseract.image_to_string(img, lang="eng")
        print(f"✅ OCR extracted text: {text.strip()}")
        
        # Clean up
        os.remove(test_image_path)
        return True
        
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")
        return False

def test_gemini_api():
    """Test if Gemini API is working"""
    print("\n🤖 Testing Gemini API...")
    try:
        import google.generativeai as genai
        
        # Configure API
        genai.configure(api_key="AIzaSyC7EjsWlNLMVJfLyaBkAkYkud6bo9ElQ9U")
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Test with sample text
        test_text = """
        FRA Claim Form
        Claimant Name: Ramesh Kumar Gond
        Village: Jagdalpur
        District: Bastar
        Land Area: 2.5 hectares
        Scheduled Tribe: Yes
        """
        
        prompt = f"""
        Extract the following fields from this FRA claim text:
        claimant_name, village, district, land_area, is_scheduled_tribe
        
        Text: {test_text}
        
        Return as JSON.
        """
        
        response = model.generate_content(prompt)
        print(f"✅ Gemini response: {response.text[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n💾 Testing database...")
    try:
        import sqlite3
        
        # Create test database
        conn = sqlite3.connect('test_fra_claims.db')
        cur = conn.cursor()
        
        # Create table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_claims (
                id INTEGER PRIMARY KEY,
                claimant_name TEXT,
                village TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        cur.execute("INSERT INTO test_claims (claimant_name, village) VALUES (?, ?)", 
                   ("Test Claimant", "Test Village"))
        
        # Query data
        cur.execute("SELECT * FROM test_claims")
        result = cur.fetchone()
        
        if result:
            print(f"✅ Database test successful: {result}")
        
        conn.commit()
        conn.close()
        
        # Clean up
        os.remove('test_fra_claims.db')
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_file_processing():
    """Test file processing capabilities"""
    print("\n📄 Testing file processing...")
    try:
        from pdf2image import convert_from_bytes
        from PIL import Image
        import io
        
        # Create a simple PDF-like test
        print("✅ PDF processing libraries available")
        
        # Test image processing
        img = Image.new('RGB', (200, 100), color='white')
        print("✅ Image processing working")
        
        return True
        
    except Exception as e:
        print(f"❌ File processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 FRA OCR System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Tesseract OCR", test_tesseract),
        ("Gemini API", test_gemini_api),
        ("Database", test_database),
        ("File Processing", test_file_processing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed! OCR system is ready to use.")
        print("\nTo start the OCR API server:")
        print("  python start_ocr_api.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon fixes:")
        print("  - Install Tesseract OCR")
        print("  - Install Python dependencies: pip install -r requirements.txt")
        print("  - Check Gemini API key")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
