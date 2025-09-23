#!/usr/bin/env python3
"""
Test script for the minimal OCR API
"""

import requests
import json
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image():
    """Create a test image with FRA claim text"""
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    text_lines = [
        "FOREST RIGHTS ACT CLAIM FORM",
        "",
        "Claimant Name: Ramesh Kumar Gond",
        "Spouse Name: Sunita Gond",
        "Father's Name: Late Ram Singh Gond",
        "",
        "Village: Jagdalpur",
        "District: Bastar",
        "State: Chhattisgarh",
        "",
        "Land Area: 2.5 hectares",
        "Scheduled Tribe: Yes"
    ]
    
    y_position = 30
    for line in text_lines:
        draw.text((20, y_position), line, fill='black', font=font)
        y_position += 25
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_api():
    """Test the OCR API"""
    print("🧪 Testing Minimal OCR API...")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:5001/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure it's running on port 5000")
        return False
    
    # Test document upload
    try:
        print("\n📤 Testing document upload...")
        img_bytes = create_test_image()
        
        files = {'file': ('test_fra_claim.png', img_bytes, 'image/png')}
        response = requests.post("http://localhost:5001/api/upload-document", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Document upload successful")
            print(f"   Confidence: {data.get('confidence', 0):.1f}%")
            print(f"   Extracted fields: {len(data.get('extracted_data', {}))}")
            
            # Show extracted data
            extracted = data.get('extracted_data', {})
            print("\n📊 Extracted Data:")
            for key, value in extracted.items():
                if value:
                    print(f"   {key}: {value}")
            
            return data
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_save_claim(ocr_data):
    """Test saving a claim"""
    if not ocr_data:
        print("❌ No OCR data to save")
        return False
    
    try:
        print("\n💾 Testing claim save...")
        
        claim_data = {
            "filename": ocr_data.get("filename", ""),
            "claimant_name": ocr_data.get("extracted_data", {}).get("claimant_name", ""),
            "village": ocr_data.get("extracted_data", {}).get("village", ""),
            "district": ocr_data.get("extracted_data", {}).get("district", ""),
            "land_area": ocr_data.get("extracted_data", {}).get("land_area", ""),
            "is_scheduled_tribe": ocr_data.get("extracted_data", {}).get("is_scheduled_tribe", ""),
            "full_address": ocr_data.get("full_address", ""),
            "raw_text": ocr_data.get("raw_text", ""),
            "confidence": ocr_data.get("confidence", 0)
        }
        
        response = requests.post(
            "http://localhost:5001/api/save-claim",
            headers={'Content-Type': 'application/json'},
            json=claim_data
        )
        
        if response.status_code == 200:
            print("✅ Claim saved successfully")
            return True
        else:
            print(f"❌ Save failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False

def test_get_claims():
    """Test retrieving claims"""
    try:
        print("\n📋 Testing claims retrieval...")
        
        response = requests.get("http://localhost:5001/api/claims")
        
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            print(f"✅ Retrieved {len(claims)} claims")
            
            for claim in claims:
                print(f"   - {claim.get('claimant_name', 'Unknown')} from {claim.get('village', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 FRA OCR API Test Suite")
    print("=" * 50)
    
    # Test API health
    if not test_api():
        print("\n❌ API is not running. Please start it first:")
        print("   python minimal_ocr_api.py")
        return
    
    # Test document upload
    ocr_data = test_api()
    if not ocr_data:
        return
    
    # Test saving claim
    if test_save_claim(ocr_data):
        print("\n✅ All tests passed!")
        
        # Test retrieving claims
        test_get_claims()
    else:
        print("\n❌ Some tests failed")

if __name__ == "__main__":
    main()
