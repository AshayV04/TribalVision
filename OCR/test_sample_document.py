#!/usr/bin/env python3
"""
Test script to debug OCR processing of the sample document
"""

import requests
import json
from PIL import Image
import io
import subprocess
import os

def test_tesseract_directly():
    """Test Tesseract directly on the sample document"""
    print("🔍 Testing Tesseract directly on Sample_claim.png...")
    
    sample_path = "../Sample_claim.png"
    if not os.path.exists(sample_path):
        print(f"❌ Sample document not found at {sample_path}")
        return False
    
    try:
        # Test tesseract directly
        result = subprocess.run([
            'tesseract', sample_path, 'stdout', '-l', 'eng'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            text = result.stdout.strip()
            print(f"✅ Tesseract extracted {len(text)} characters")
            print("📄 First 500 characters:")
            print("-" * 50)
            print(text[:500])
            print("-" * 50)
            return True
        else:
            print(f"❌ Tesseract failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_image_processing():
    """Test image processing with PIL"""
    print("\n🖼️ Testing image processing...")
    
    sample_path = "../Sample_claim.png"
    try:
        # Open and process image
        image = Image.open(sample_path)
        print(f"✅ Image loaded: {image.size}, mode: {image.mode}")
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            print("✅ Converted to RGB")
        
        # Save as temporary file for tesseract
        temp_path = "/tmp/sample_claim_temp.png"
        image.save(temp_path)
        print(f"✅ Saved temp image to {temp_path}")
        
        # Test tesseract on temp file
        result = subprocess.run([
            'tesseract', temp_path, 'stdout', '-l', 'eng'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            text = result.stdout.strip()
            print(f"✅ OCR on processed image: {len(text)} characters")
            print("📄 First 300 characters:")
            print("-" * 50)
            print(text[:300])
            print("-" * 50)
            
            # Clean up
            os.remove(temp_path)
            return True
        else:
            print(f"❌ OCR failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Image processing error: {e}")
        return False

def test_api_upload():
    """Test uploading to the API"""
    print("\n🌐 Testing API upload...")
    
    sample_path = "../Sample_claim.png"
    try:
        with open(sample_path, 'rb') as f:
            files = {'file': ('Sample_claim.png', f, 'image/png')}
            response = requests.post('http://localhost:5001/api/upload-document', files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API upload successful")
            print(f"   Confidence: {data.get('confidence', 0):.1f}%")
            print(f"   Text length: {len(data.get('raw_text', ''))}")
            
            # Show extracted data
            extracted = data.get('extracted_data', {})
            if extracted:
                print("\n📊 Extracted Data:")
                for key, value in extracted.items():
                    if value:
                        print(f"   {key}: {value}")
            else:
                print("❌ No extracted data")
            
            return True
        else:
            print(f"❌ API upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API upload error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Sample Document OCR Test")
    print("=" * 50)
    
    # Test 1: Direct Tesseract
    tesseract_ok = test_tesseract_directly()
    
    # Test 2: Image processing
    image_ok = test_image_processing()
    
    # Test 3: API upload
    api_ok = test_api_upload()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Tesseract Direct: {'✅' if tesseract_ok else '❌'}")
    print(f"   Image Processing: {'✅' if image_ok else '❌'}")
    print(f"   API Upload: {'✅' if api_ok else '❌'}")
    
    if not tesseract_ok:
        print("\n💡 Suggestions:")
        print("   - Check if Tesseract is installed: brew install tesseract")
        print("   - Try different image formats (JPG, PNG)")
        print("   - Ensure image has good contrast and resolution")
        print("   - Try preprocessing the image (increase contrast, resize)")

if __name__ == "__main__":
    main()
