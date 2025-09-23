# fra_extractor_app.py
import os
import sqlite3
import json
from typing import Dict, Optional

import streamlit as st
import pytesseract
import pandas as pd
from PIL import Image
from pdf2image import convert_from_bytes
import google.generativeai as genai

# ----------------- CONFIG -----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

DB_FILE = "fra_claims.db"
POPPLER_PATH = None

# ----------------- Gemini API -----------------
genai.configure(api_key="AIzaSyC7EjsWlNLMVJfLyaBkAkYkud6bo9ElQ9U")
GEMINI_MODEL = "gemini-2.0-flash"

def human_like_extract_with_gemini(raw_text: str) -> Dict[str, Optional[str]]:
    """
    Gemini reads the OCR text and produces structured fields
    like a human would, based only on the content present.
    """
    prompt = f"""
You are an expert in interpreting FRA Claim Forms (Form A). 

Task:
- Analyze the OCR text below.
- Extract all the following fields: 
  claimant_name, spouse_name, father_or_mother_name, address, village, gram_panchayat,
  tehsil_taluka, district, state, is_scheduled_tribe, is_otfd.

- Only use the information present in the document.
- If a field is missing or unclear, leave it blank ("").
- Avoid inventing any values.
- Return a **JSON dictionary** only, keys as above, values as strings or empty.

OCR Text:
---
{raw_text}
"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        st.subheader("🔹 Gemini Raw Response")
        st.text(response.text[:4000])  # preview first 4000 chars

        # Clean up Gemini response
        cleaned = response.text.strip()
        if cleaned.startswith("```"):
            # Drop the ```json ... ``` fences
            parts = cleaned.split("```")
            if len(parts) >= 2:
                cleaned = parts[1]
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip("` \n")

        # Parse safely
        extracted = json.loads(cleaned)
        return extracted
    except Exception as e:
        st.warning(f"Gemini extraction failed: {e}")
        return {}

# ----------------- Address Builder -----------------
def build_full_address(extracted: dict) -> str:
    parts = [
        extracted.get("address", ""),
        extracted.get("village", ""),
        extracted.get("gram_panchayat", ""),
        extracted.get("tehsil_taluka", ""),
        extracted.get("district", ""),
        extracted.get("state", "")
    ]
    # Strip dots/extra spaces and join
    full_address = ", ".join([p.strip().strip(".") for p in parts if p and p.strip()])
    return full_address

# ----------------- DB Utilities -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Stable schema: we keep using "address" for full combined address
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fra_claim_individual (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_filename TEXT,
            claimant_name TEXT,
            spouse_name TEXT,
            father_or_mother_name TEXT,
            address TEXT,
            is_scheduled_tribe TEXT,
            is_otfd TEXT,
            raw_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def query_db(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# ----------------- OCR -----------------
def ocr_image(image: Image.Image) -> str:
    try:
        text = pytesseract.image_to_string(image, lang="eng")
    except pytesseract.pytesseract.TesseractError as e:
        st.error("Tesseract OCR failed. Check installation.")
        raise e
    return text

def ocr_pdf_bytes(pdf_bytes: bytes) -> str:
    images = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=POPPLER_PATH)
    texts = []
    for idx, img in enumerate(images):
        st.subheader(f"🖼 OCR Page {idx+1} Preview")
        st.image(img, use_column_width=True)
        texts.append(ocr_image(img))
    return "\n".join(texts)

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title="FRA Claim Extractor", layout="wide")
init_db()

st.title("🌳 FRA Claim Form Extractor (Form A)")
st.write("Upload scanned FRA claim forms (Form A). The app will OCR → Gemini → build full address → save in SQLite DB.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Upload a document (PDF / JPG / PNG)", type=["pdf", "jpg", "jpeg", "png"])
    if uploaded_file:
        st.info(f"Processing: {uploaded_file.name}")
        raw_text = ""
        try:
            if uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
                pdf_bytes = uploaded_file.read()
                raw_text = ocr_pdf_bytes(pdf_bytes)
            else:
                image = Image.open(uploaded_file).convert("RGB")
                st.subheader("🖼 Uploaded Image Preview")
                st.image(image, use_column_width=True)
                raw_text = ocr_image(image)
        except Exception as e:
            st.error("OCR failed: " + str(e))
            raw_text = ""

        if raw_text:
            st.subheader("📝 Raw OCR Text (Preview first 4000 chars)")
            st.text_area("Raw OCR Text", raw_text[:4000], height=250)

            extracted = human_like_extract_with_gemini(raw_text)
            st.subheader("✨ Gemini Extracted Fields")
            st.json(extracted)

            full_address = build_full_address(extracted)
            st.subheader("📌 Full Combined Address")
            st.write(full_address)

            record = {
                "source_filename": uploaded_file.name,
                "claimant_name": extracted.get("claimant_name", ""),
                "spouse_name": extracted.get("spouse_name", ""),
                "father_or_mother_name": extracted.get("father_or_mother_name", ""),
                "address": full_address,  # full address stored in "address"
                "is_scheduled_tribe": extracted.get("is_scheduled_tribe", ""),
                "is_otfd": extracted.get("is_otfd", ""),
                "raw_text": raw_text
            }

            st.subheader("💾 Final Record to Save in DB")
            st.json(record)

            if st.button("Save Record to Database"):
                save_to_db(record)
                st.success("Saved to database successfully!")

with col2:
    st.subheader("🔎 Browse Saved Records")
    df_all = query_db("SELECT id, source_filename, claimant_name, address, is_scheduled_tribe, is_otfd, created_at FROM fra_claim_individual ORDER BY created_at DESC")
    st.write(f"Total saved records: {len(df_all)}")
    st.dataframe(df_all, use_container_width=True)

    sel_id = st.number_input("Enter Record ID to view full record (or 0 to skip)", min_value=0, value=0, step=1)
    if sel_id:
        rec_df = query_db("SELECT * FROM fra_claim_individual WHERE id = ?", (sel_id,))
        if not rec_df.empty:
            rec = rec_df.iloc[0].to_dict()
            st.subheader("Full record")
            st.json(rec)
        else:
            st.warning("Record not found.")

    if not df_all.empty:
        csv_bytes = df_all.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export all records as CSV", csv_bytes, file_name="fra_records.csv", mime="text/csv")

st.markdown("---")
st.write("Notes:")
st.write("- Gemini extracts fields, and app builds a full combined address stored in the `address` column.")
st.write("- Database schema is stable, no mismatch errors.")
st.write("- For better accuracy, ensure scans are high-quality (300dpi).")
