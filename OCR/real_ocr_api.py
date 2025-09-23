# real_ocr_api.py
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Optional
import base64
import io
import sys
import subprocess

# Fix numpy import issue by removing current directory from path
current_dir = os.getcwd()
if current_dir in sys.path:
    sys.path.remove(current_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import google.generativeai as genai

# ----------------- CONFIG -----------------
DB_FILE = "fra_claims.db"

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

def save_to_db(record: Dict):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    keys = list(record.keys())
    placeholders = ", ".join(["?"] * len(keys))
    cols = ", ".join(keys)
    values = [record[k] for k in keys]
    sql = f"INSERT INTO fra_claim_individual ({cols}) VALUES ({placeholders})"
    cur.execute(sql, values)
    conn.commit()
    conn.close()

def get_claims():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, source_filename, claimant_name, village, district, 
               land_area, status, created_at 
        FROM fra_claim_individual 
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    claims = []
    for row in rows:
        claims.append({
            'id': row[0],
            'source_filename': row[1],
            'claimant_name': row[2],
            'village': row[3],
            'district': row[4],
            'land_area': row[5],
            'status': row[6],
            'created_at': row[7]
        })
    return claims

# ----------------- Real OCR Functions -----------------
def run_tesseract_ocr(image_path: str) -> tuple[str, float]:
    """Run Tesseract OCR using subprocess to avoid numpy issues"""
    try:
        # Use subprocess to run tesseract directly
        result = subprocess.run([
            'tesseract', image_path, 'stdout', '-l', 'eng'
        ], capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            text = result.stdout.strip()
            # Calculate a mock confidence score based on text length and content
            confidence = min(95.0, max(60.0, len(text) * 0.5 + 50))
            return text, confidence
        else:
            print(f"Tesseract error: {result.stderr}")
            return "", 0.0
            
    except subprocess.TimeoutExpired:
        print("Tesseract timeout")
        return "", 0.0
    except FileNotFoundError:
        print("Tesseract not found in PATH")
        return "", 0.0
    except Exception as e:
        print(f"OCR error: {e}")
        return "", 0.0

def ocr_image(image: Image.Image) -> tuple[str, float]:
    """Extract text from PIL Image using Tesseract"""
    try:
        # Save image to temporary file
        temp_path = "/tmp/temp_ocr_image.png"
        image.save(temp_path)
        
        # Run OCR
        text, confidence = run_tesseract_ocr(temp_path)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return text, confidence
        
    except Exception as e:
        print(f"Image OCR failed: {e}")
        return "", 0.0

def ocr_pdf_bytes(pdf_bytes: bytes) -> tuple[str, float]:
    """Extract text from PDF using pdf2image + Tesseract"""
    try:
        # Use pdf2image to convert PDF to images
        from pdf2image import convert_from_bytes
        
        images = convert_from_bytes(pdf_bytes, dpi=300)
        all_texts = []
        all_confidences = []
        
        for i, img in enumerate(images):
            # Save each page as temp image
            temp_path = f"/tmp/temp_pdf_page_{i}.png"
            img.save(temp_path)
            
            # Run OCR on each page
            text, confidence = run_tesseract_ocr(temp_path)
            all_texts.append(text)
            all_confidences.append(confidence)
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        combined_text = "\n".join(all_texts)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return combined_text, avg_confidence
        
    except Exception as e:
        print(f"PDF OCR failed: {e}")
        return "", 0.0

def human_like_extract_with_gemini(raw_text: str) -> Dict[str, Optional[str]]:
    """Use Gemini to extract structured fields from OCR text"""
    prompt = f"""
    You are an expert in interpreting FRA Claim Forms (Form A). 
    
    Task:
    - Analyze the OCR text below carefully.
    - Extract all the following fields: 
      claimant_name, spouse_name, father_or_mother_name, address, village, gram_panchayat,
      tehsil_taluka, district, state, is_scheduled_tribe, is_otfd, land_area.
    
    - Only use the information present in the document.
    - If a field is missing or unclear, leave it blank ("").
    - Avoid inventing any values.
    - Be very careful with names and addresses - extract exactly as written.
    - Return a **JSON dictionary** only, keys as above, values as strings or empty.
    
    OCR Text:
    ---
    {raw_text}
    """
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Clean up Gemini response
        cleaned = response.text.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            if len(parts) >= 2:
                cleaned = parts[1]
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip("` \n")
        
        # Parse JSON
        extracted = json.loads(cleaned)
        return extracted
    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        return {}

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
    return jsonify({"status": "healthy", "message": "FRA OCR API is running (Real OCR Mode)"})

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
        
        print(f"Processing file: {filename}")
        
        # Process based on file type
        if filename.lower().endswith('.pdf'):
            print("Processing PDF...")
            raw_text, confidence = ocr_pdf_bytes(file_content)
        else:
            # Handle image files
            print("Processing image...")
            image = Image.open(io.BytesIO(file_content)).convert("RGB")
            raw_text, confidence = ocr_image(image)
        
        print(f"OCR completed. Text length: {len(raw_text)}, Confidence: {confidence}")
        
        if not raw_text.strip():
            return jsonify({"error": "No text could be extracted from the document"}), 400
        
        # Extract structured data using Gemini
        print("Extracting structured data with Gemini...")
        extracted_data = human_like_extract_with_gemini(raw_text)
        print(f"Extracted {len(extracted_data)} fields")
        
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
        print(f"Processing error: {e}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route('/api/save-claim', methods=['POST'])
def save_claim():
    try:
        data = request.get_json()
        
        # Prepare record for database
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
        
        # Save to database
        save_to_db(record)
        
        return jsonify({"message": "Claim saved successfully", "status": "success"})
        
    except Exception as e:
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

if __name__ == '__main__':
    init_db()
    print("🚀 Starting FRA OCR API (Real OCR Mode)...")
    print("📡 API will be available at: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print("ℹ️  Note: Using real Tesseract OCR + Gemini AI")
    app.run(debug=True, host='0.0.0.0', port=5001)
