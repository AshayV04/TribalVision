# flask_ocr_api.py
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Optional
import base64
import io
import sys
import re


# Fix numpy import issue by removing current directory from path
current_dir = os.getcwd()
if current_dir in sys.path:
    sys.path.remove(current_dir)

# Additional numpy fix - ensure we're not in a numpy source directory
os.chdir('/tmp')  # Change to a safe directory temporarily

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pytesseract
import pandas as pd
from PIL import Image
from pdf2image import convert_from_bytes
import google.generativeai as genai

# ----------------- CONFIG -----------------
# Configure Tesseract path for different OS
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
else:  # Linux/Mac
    # Default paths for Linux/Mac
    pass

import os

DB_FILE = os.path.join(os.path.dirname(__file__), "fra_claims.db")
print("Using database:", DB_FILE)



POPPLER_PATH = None

# ----------------- Gemini API -----------------
genai.configure(api_key="AIzaSyC7EjsWlNLMVJfLyaBkAkYkud6bo9ElQ9U")
GEMINI_MODEL = "gemini-2.0-flash"

app = Flask(__name__)
CORS(app)

# ----------------- Database Functions -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
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

def save_to_db(record):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fra_claim_individual (
            source_filename, claimant_name, spouse_name, father_or_mother_name,
            address, village, gram_panchayat, tehsil_taluka, district, state,
            is_scheduled_tribe, is_otfd, land_area, raw_text, ocr_confidence, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["source_filename"], record["claimant_name"], record["spouse_name"],
        record["father_or_mother_name"], record["address"], record["village"],
        record["gram_panchayat"], record["tehsil_taluka"], record["district"], record["state"],
        record["is_scheduled_tribe"], record["is_otfd"], record["land_area"],
        record["raw_text"], record["ocr_confidence"], record["status"]
    ))
    conn.commit()
    conn.close()


def get_claims():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT id, source_filename, claimant_name, village, district, 
               land_area, status, created_at 
        FROM fra_claim_individual 
        ORDER BY created_at DESC
    """, conn)
    conn.close()
    return df.to_dict('records')

# ----------------- OCR Functions -----------------
def ocr_image(image: Image.Image) -> tuple[str, float]:
    """Extract text from image and return text with confidence score"""
    try:
        # Get OCR data with confidence scores
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(image, lang="eng")
        
        # Calculate average confidence
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return text, avg_confidence
    except Exception as e:
        print(f"OCR failed: {e}")
        return "", 0.0

def ocr_pdf_bytes(pdf_bytes: bytes) -> tuple[str, float]:
    """Extract text from PDF and return text with confidence score"""
    try:
        images = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=POPPLER_PATH)
        all_texts = []
        all_confidences = []
        
        for img in images:
            text, confidence = ocr_image(img)
            all_texts.append(text)
            all_confidences.append(confidence)
        
        combined_text = "\n".join(all_texts)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return combined_text, avg_confidence
    except Exception as e:
        print(f"PDF OCR failed: {e}")
        return "", 0.0

def human_like_extract_with_gemini(raw_text: str) -> Dict[str, Optional[str]]:
    """Use Gemini to extract structured fields from OCR text"""
    prompt = f"""
    You are an expert in interpreting FRA (Forest Rights Act) Claim Forms (Form A). 
    
    Task:
    - Analyze the OCR text below from a FRA claim form.
    - Extract the following fields with high accuracy:
      - claimant_name: Name of the person making the claim
      - spouse_name: Name of the spouse (if mentioned)
      - father_or_mother_name: Father's or mother's name
      - address: Complete address
      - village: Village name
      - gram_panchayat: Gram Panchayat name
      - tehsil_taluka: Tehsil or Taluka name
      - district: District name
      - state: State name
      - is_scheduled_tribe: "Yes" or "No" for Scheduled Tribe status
      - is_otfd: "Yes" or "No" for Other Traditional Forest Dweller status
      - land_area: Area of land claimed (in hectares, acres, etc.)
    
    Instructions:
    - Only extract information that is clearly present in the document
    - If a field is missing, unclear, or not mentioned, use empty string ""
    - For Yes/No fields, use exactly "Yes" or "No" or empty string if not specified
    - Clean up any OCR errors in names and addresses
    - Return ONLY a valid JSON dictionary with the exact keys listed above
    
    OCR Text:
    ---
    {raw_text}
    ---
    
    Return only the JSON response:
    """
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Clean up Gemini response
        cleaned = response.text.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
        # Remove any leading/trailing whitespace and newlines
        cleaned = cleaned.strip()
        
        # Try to find JSON in the response
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            cleaned = cleaned[start:end]
        
        # Parse JSON
        extracted = json.loads(cleaned)
        
        # Ensure all required keys exist with empty strings as defaults
        required_keys = [
            "claimant_name", "spouse_name", "father_or_mother_name", "address", 
            "village", "gram_panchayat", "tehsil_taluka", "district", "state", 
            "is_scheduled_tribe", "is_otfd", "land_area"
        ]
        
        for key in required_keys:
            if key not in extracted:
                extracted[key] = ""
            elif extracted[key] is None:
                extracted[key] = ""
            else:
                # Clean up the extracted value
                extracted[key] = str(extracted[key]).strip()
        
        print(f"Successfully extracted data: {extracted}")
        return extracted
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        # Return empty structure if JSON parsing fails
        return {
            "claimant_name": "", "spouse_name": "", "father_or_mother_name": "", 
            "address": "", "village": "", "gram_panchayat": "", "tehsil_taluka": "", 
            "district": "", "state": "", "is_scheduled_tribe": "", "is_otfd": "", "land_area": ""
        }
    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        return {
            "claimant_name": "", "spouse_name": "", "father_or_mother_name": "", 
            "address": "", "village": "", "gram_panchayat": "", "tehsil_taluka": "", 
            "district": "", "state": "", "is_scheduled_tribe": "", "is_otfd": "", "land_area": ""
        }

def fallback_extract_with_regex(raw_text: str) -> Dict[str, Optional[str]]:
    """Fallback extraction using regex patterns for common FRA form fields"""
    extracted = {
        "claimant_name": "", "spouse_name": "", "father_or_mother_name": "", 
        "address": "", "village": "", "gram_panchayat": "", "tehsil_taluka": "", 
        "district": "", "state": "", "is_scheduled_tribe": "", "is_otfd": "", "land_area": ""
    }
    
    try:
        print(f"Fallback extraction starting with text: {raw_text[:200]}...")
        
        # Extract claimant name - look for patterns like "Name of the claimant" or "Claimant:"
        claimant_patterns = [
            r'Name of the claimant[^:]*:\s*([A-Za-z0-9\s]+?)(?=\n|Name of the spouse)',
            r'Name of the claimant[^:]*:\s*([A-Za-z0-9\s]+)',
            r'Claimant[:\s]*([A-Za-z\s]+)',
        ]
        
        for pattern in claimant_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and not any(word in name.lower() for word in ['form', 'claim', 'rights', 'forest']):
                    extracted["claimant_name"] = name
                    break
        
        # Extract spouse name
        spouse_patterns = [
            r'Name of the spouse[:\s]*([A-Za-z0-9\s]+?)(?=\n|Name of father|Name of mother|$)',
            r'Name of the spouse[:\s]*([A-Za-z0-9\s]+)',
            r'Spouse[:\s]*([A-Za-z0-9\s]+)',
        ]
        
        for pattern in spouse_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:
                    extracted["spouse_name"] = name
                    break
        
        # Extract father/mother name
        parent_patterns = [
            r'Name of father[:\s]*([A-Za-z\s]+?)(?=\n|Address|$)',
            r'Name of mother[:\s]*([A-Za-z\s]+?)(?=\n|Address|$)',
            r'Name of father[:\s]*([A-Za-z\s]+)',
            r'Name of mother[:\s]*([A-Za-z\s]+)',
            r'Father[:\s]*([A-Za-z\s]+)',
            r'Mother[:\s]*([A-Za-z\s]+)',
        ]
        
        for pattern in parent_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:
                    extracted["father_or_mother_name"] = name
                    break
        
        # Extract village
        village_patterns = [
            r'Village[:\s]*([A-Za-z0-9\s,]+?)(?=\n|Gram Panchayat|Tehsil|District|$)',
            r'Village[:\s]*([A-Za-z0-9\s,]+)',
        ]
        
        for pattern in village_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                village = match.group(1).strip().rstrip(',').strip()
                if len(village) > 2:
                    extracted["village"] = village
                    break
        
        # Extract district
        district_patterns = [
            r'District[:\s]*([A-Za-z\s]+)',
            r'District[:\s]*([A-Za-z\s,]+)',
        ]
        
        for pattern in district_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                district = match.group(1).strip().rstrip(',').strip()
                if len(district) > 2:
                    extracted["district"] = district
                    break
        
        # Extract address
        address_patterns = [
            r'Address[:\s]*([A-Za-z0-9\s,.-]+?)(?=Village|District|$)',
            r'Address[:\s]*([A-Za-z0-9\s,.-]+)',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(1).strip()
                if len(address) > 5:
                    extracted["address"] = address
                    break
        
        # Extract land area
        area_patterns = [
            r'(\d+\.?\d*)\s*(hectares?|acres?|ha|ac)',
            r'Area[:\s]*(\d+\.?\d*)\s*(hectares?|acres?|ha|ac)',
            r'(\d+\.?\d*)\s*(hectares?|acres?)',
        ]
        
        for pattern in area_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                area = f"{match.group(1)} {match.group(2)}"
                extracted["land_area"] = area
                break
        
        # Extract Scheduled Tribe status
        st_patterns = [
            r'Scheduled Tribe[:\s]*(Yes|No)',
            r'ST[:\s]*(Yes|No)',
        ]
        
        for pattern in st_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                extracted["is_scheduled_tribe"] = match.group(1).strip()
                break
        
        # Extract OTFD status
        otfd_patterns = [
            r'Other Traditional Forest Dweller[:\s]*(Yes|No)',
            r'OTFD[:\s]*(Yes|No)',
        ]
        
        for pattern in otfd_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                extracted["is_otfd"] = match.group(1).strip()
                break
        
        print(f"Fallback extraction completed: {extracted}")
        return extracted
        
    except Exception as e:
        print(f"Fallback extraction failed: {e}")
        return extracted

def build_full_address(extracted: dict) -> str:
    """Build full address from extracted components"""
    parts = [
        extracted.get("address", ""),
        extracted.get("village", ""),
        extracted.get("gram_panchayat", ""),
        extracted.get("tehsil_taluka", ""),
        extracted.get("district", ""),
        extracted.get("state", "")
    ]
    full_address = ", ".join([p.strip().strip(".") for p in parts if p and p.strip()])
    return full_address

# ----------------- API Routes -----------------
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "FRA OCR API is running"})

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read file content
        file_content = file.read()
        filename = file.filename
        
        # Process based on file type
        if filename.lower().endswith('.pdf'):
            raw_text, confidence = ocr_pdf_bytes(file_content)
        else:
            # Handle image files
            image = Image.open(io.BytesIO(file_content)).convert("RGB")
            raw_text, confidence = ocr_image(image)
        
        if not raw_text.strip():
            return jsonify({"error": "No text could be extracted from the document"}), 400
        
        # Extract structured data using Gemini with fallback
        print(f"Starting extraction for text: {raw_text[:200]}...")
        extracted_data = human_like_extract_with_gemini(raw_text)
        print(f"Gemini extraction result: {extracted_data}")
        
        # If Gemini extraction failed or returned mostly empty data, use fallback
        if not extracted_data or all(not v or v.strip() == "" for v in extracted_data.values()):
            print("Gemini extraction failed or returned empty data, using fallback extraction")
            extracted_data = fallback_extract_with_regex(raw_text)
            print(f"Fallback extraction result: {extracted_data}")
        
        # Build full address
        full_address = build_full_address(extracted_data)
        
        # Prepare response
        response_data = {
            "filename": filename,
            "raw_text": raw_text,
            "confidence": confidence,
            "extracted_data": extracted_data,
            "full_address": full_address,
            "processing_time": datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route('/api/save-claim', methods=['POST'])
def save_claim():
    try:
        data = request.get_json()
        print("Incoming JSON:", data)   # <-- moved after parsing JSON
        
        # Build dict, not set
        record = {
            "source_filename": data.get("filename", ""),
            "claimant_name": data.get("claimant_name", ""),
            "spouse_name": data.get("spouse_name", ""),
            "father_or_mother_name": data.get("father_or_mother_name", ""),
            "address": data.get("full_address", ""),
            "village": data.get("village", ""),
            "gram_panchayat": data.get("gram_panchayat", ""),
            "tehsil_taluka": data.get("tehsil_taluka", ""),
            "district": data.get("district", ""),
            "state": data.get("state", ""),
            "is_scheduled_tribe": data.get("is_scheduled_tribe", ""),
            "is_otfd": data.get("is_otfd", ""),
            "land_area": data.get("land_area", ""),
            "raw_text": data.get("raw_text", ""),
            "ocr_confidence": data.get("confidence", 0.0),
            "status": "pending_review"
        }

        save_to_db(record)
        return jsonify({"message": "Claim saved successfully", "status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to save claim: {str(e)}"}), 500



@app.route('/api/claims', methods=['GET'])
def get_claims_api():
    try:
        claims = get_claims()
        return jsonify({"claims": claims, "count": len(claims)})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch claims: {str(e)}"}), 500

@app.route('/api/claim/<int:claim_id>', methods=['GET'])
def get_claim_details(claim_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT * FROM fra_claim_individual WHERE id = ?", (claim_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"error": "Claim not found"}), 404
        
        # Convert to dict
        columns = [description[0] for description in cur.description]
        claim_data = dict(zip(columns, row))
        
        return jsonify(claim_data)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch claim: {str(e)}"}), 500

@app.route('/api/claim/<int:claim_id>/status', methods=['PUT'])
def update_claim_status(claim_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
        
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE fra_claim_individual SET status = ? WHERE id = ?", (new_status, claim_id))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Status updated successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to update status: {str(e)}"}), 500

@app.route('/api/claims/<int:claim_id>', methods=['DELETE'])
def delete_claim(claim_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("DELETE FROM fra_claim_individual WHERE id = ?", (claim_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Claim deleted successfully", "status": "success"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete claim: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)

