# simple_real_ocr.py
import os
import json
import sqlite3
from datetime import datetime
import subprocess
import tempfile

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

def run_ocr(image_path):
    """Run OCR on image file"""
    try:
        result = subprocess.run([
            'tesseract', image_path, 'stdout', '-l', 'eng'
        ], capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            text = result.stdout.strip()
            confidence = min(95.0, max(60.0, len(text) * 0.5 + 50))
            return text, confidence
        else:
            print(f"Tesseract error: {result.stderr}")
            return "", 0.0
    except Exception as e:
        print(f"OCR error: {e}")
        return "", 0.0

def extract_with_gemini(text):
    """Extract structured data using Gemini"""
    prompt = f"""
    Extract FRA claim information from this text:
    
    {text}
    
    Return JSON with these fields:
    claimant_name, spouse_name, father_or_mother_name, address, village, 
    gram_panchayat, tehsil_taluka, district, state, is_scheduled_tribe, 
    is_otfd, land_area
    
    Only use information present in the text. Leave fields blank if not found.
    """
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        cleaned = response.text.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            if len(parts) >= 2:
                cleaned = parts[1]
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip("` \n")
        
        return json.loads(cleaned)
    except Exception as e:
        print(f"Gemini error: {e}")
        return {}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Simple Real OCR API"})

def save_to_db(record):
    """Save claim record to database"""
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

@app.route('/api/save-claim', methods=['POST'])
def save_claim():
    """Save extracted claim data to database"""
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
        print(f"Save error: {e}")
        return jsonify({"error": f"Failed to save claim: {str(e)}"}), 500

@app.route('/api/claims', methods=['GET'])
def get_claims():
    """Get all claims from database"""
    try:
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
        
        return jsonify({"claims": claims, "count": len(claims)})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch claims: {str(e)}"}), 500

@app.route('/api/claims/<int:claim_id>', methods=['DELETE'])
def delete_claim(claim_id):
    """Delete a specific claim"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        # Check if claim exists
        cur.execute('SELECT id FROM fra_claim_individual WHERE id = ?', (claim_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({"error": "Claim not found"}), 404
        
        # Delete the claim
        cur.execute('DELETE FROM fra_claim_individual WHERE id = ?', (claim_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Claim deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete claim: {str(e)}"}), 500

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        print(f"Processing file: {file.filename}")
        
        # Read file content
        file_content = file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            # Run OCR
            print("Running OCR...")
            text, confidence = run_ocr(temp_path)
            print(f"OCR result: {len(text)} characters, confidence: {confidence}")
            
            if not text.strip():
                return jsonify({"error": "No text could be extracted"}), 400
            
            # Extract structured data
            print("Extracting with Gemini...")
            extracted = extract_with_gemini(text)
            print(f"Extracted {len(extracted)} fields")
            
            # Build address
            address_parts = [
                extracted.get("address", ""),
                extracted.get("village", ""),
                extracted.get("gram_panchayat", ""),
                extracted.get("tehsil_taluka", ""),
                extracted.get("district", ""),
                extracted.get("state", "")
            ]
            full_address = ", ".join([p.strip() for p in address_parts if p and p.strip()])
            
            response_data = {
                "filename": file.filename,
                "raw_text": text,
                "confidence": confidence,
                "extracted_data": extracted,
                "full_address": full_address,
                "processing_time": datetime.now().isoformat()
            }
            
            return jsonify(response_data)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        print(f"Processing error: {e}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    print("🚀 Starting Simple Real OCR API...")
    print("📡 API available at: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
