#!/usr/bin/env python3
"""
Demo script showing how to use the FRA OCR API
This script demonstrates the complete workflow from document upload to claim saving
"""

import requests
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

# API base URL
API_BASE = "http://localhost:5000"

def create_sample_document():
    """Create a sample FRA claim document for testing"""
    print("📄 Creating sample FRA claim document...")
    
    # Create a sample image with FRA claim text
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Add sample FRA claim text
    text_lines = [
        "FOREST RIGHTS ACT CLAIM FORM",
        "",
        "Claimant Name: Ramesh Kumar Gond",
        "Spouse Name: Sunita Gond",
        "Father's Name: Late Ram Singh Gond",
        "",
        "Address: Village - Jagdalpur",
        "Gram Panchayat: Jagdalpur",
        "Tehsil: Jagdalpur",
        "District: Bastar",
        "State: Chhattisgarh",
        "",
        "Land Area: 2.5 hectares",
        "Scheduled Tribe: Yes",
        "OTFD: No",
        "",
        "Land Description:",
        "Agricultural land with forest cover",
        "Located near village boundary",
        "Traditional cultivation area"
    ]
    
    y_position = 50
    for line in text_lines:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 25
    
    # Save the sample document
    sample_file = "sample_fra_claim.png"
    img.save(sample_file)
    print(f"✅ Created sample document: {sample_file}")
    return sample_file

def test_api_health():
    """Test if the API is running"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE}/api/health")
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running.")
        return False

def upload_document(file_path):
    """Upload a document for OCR processing"""
    print(f"📤 Uploading document: {file_path}")
    
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(f"{API_BASE}/api/upload-document", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Document uploaded and processed successfully")
            print(f"   Confidence: {data.get('confidence', 0):.1f}%")
            print(f"   Extracted fields: {len(data.get('extracted_data', {}))}")
            return data
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def save_claim(ocr_data):
    """Save the extracted data as a claim"""
    print("💾 Saving claim to database...")
    
    try:
        # Prepare the data for saving
        claim_data = {
            "filename": ocr_data.get("filename", ""),
            "claimant_name": ocr_data.get("extracted_data", {}).get("claimant_name", ""),
            "spouse_name": ocr_data.get("extracted_data", {}).get("spouse_name", ""),
            "father_or_mother_name": ocr_data.get("extracted_data", {}).get("father_or_mother_name", ""),
            "village": ocr_data.get("extracted_data", {}).get("village", ""),
            "district": ocr_data.get("extracted_data", {}).get("district", ""),
            "land_area": ocr_data.get("extracted_data", {}).get("land_area", ""),
            "is_scheduled_tribe": ocr_data.get("extracted_data", {}).get("is_scheduled_tribe", ""),
            "full_address": ocr_data.get("full_address", ""),
            "raw_text": ocr_data.get("raw_text", ""),
            "confidence": ocr_data.get("confidence", 0)
        }
        
        response = requests.post(
            f"{API_BASE}/api/save-claim",
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

def get_claims():
    """Retrieve all claims from the database"""
    print("📋 Retrieving claims from database...")
    
    try:
        response = requests.get(f"{API_BASE}/api/claims")
        
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            print(f"✅ Retrieved {len(claims)} claims")
            
            for claim in claims:
                print(f"   - {claim.get('claimant_name', 'Unknown')} from {claim.get('village', 'Unknown')}")
            
            return claims
        else:
            print(f"❌ Retrieval failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return []

def display_extracted_data(ocr_data):
    """Display the extracted data in a formatted way"""
    print("\n📊 Extracted Data:")
    print("=" * 50)
    
    extracted = ocr_data.get("extracted_data", {})
    
    fields = [
        ("Claimant Name", "claimant_name"),
        ("Spouse Name", "spouse_name"),
        ("Father/Mother Name", "father_or_mother_name"),
        ("Village", "village"),
        ("District", "district"),
        ("Land Area", "land_area"),
        ("Scheduled Tribe", "is_scheduled_tribe")
    ]
    
    for label, key in fields:
        value = extracted.get(key, "Not found")
        print(f"{label:20}: {value}")
    
    print(f"\nFull Address: {ocr_data.get('full_address', 'Not found')}")
    print(f"OCR Confidence: {ocr_data.get('confidence', 0):.1f}%")
    
    # Show raw OCR text (truncated)
    raw_text = ocr_data.get("raw_text", "")
    if raw_text:
        print(f"\nRaw OCR Text (first 200 chars):")
        print("-" * 50)
        print(raw_text[:200] + "..." if len(raw_text) > 200 else raw_text)

def main():
    """Main demo function"""
    print("🚀 FRA OCR API Demo")
    print("=" * 50)
    
    # Step 1: Check API health
    if not test_api_health():
        print("\n❌ Please start the OCR API server first:")
        print("   python start_ocr_api.py")
        return
    
    # Step 2: Create sample document
    sample_file = create_sample_document()
    
    try:
        # Step 3: Upload and process document
        ocr_data = upload_document(sample_file)
        if not ocr_data:
            return
        
        # Step 4: Display extracted data
        display_extracted_data(ocr_data)
        
        # Step 5: Save claim
        if save_claim(ocr_data):
            print("\n✅ Demo completed successfully!")
            
            # Step 6: Retrieve and display claims
            get_claims()
        
    finally:
        # Clean up sample file
        if os.path.exists(sample_file):
            os.remove(sample_file)
            print(f"\n🧹 Cleaned up sample file: {sample_file}")

if __name__ == "__main__":
    main()
