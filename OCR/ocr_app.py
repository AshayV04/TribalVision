import streamlit as st
import pytesseract
from PIL import Image
import os
import re

# ✅ Point pytesseract directly to the exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ✅ Force tessdata path manually (bypasses broken env variable)
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# Streamlit App
st.title("📄 OCR Name Extractor")
st.write("Upload an image and extract the **name** from it.")

# File uploader
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Open image
    image = Image.open(uploaded_file)

    # Show the image
    st.image(image, caption="Uploaded Image", use_container_width=True)

    # Extract text
    with st.spinner("Extracting text..."):
        extracted_text = pytesseract.image_to_string(image, lang="eng")

    # Try to extract "name" using regex / keywords
    name = None

    # Example 1: Look for line containing "Name:"
    match = re.search(r"(?:Name[:\-]?\s*)([A-Za-z\s]+)", extracted_text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()

    # Example 2: If no "Name:" found, take the first 2–3 words of OCR text
    if not name:
        words = extracted_text.strip().split()
        if len(words) > 1:
            name = " ".join(words[:3])  # first 3 words

    # Show results
    st.subheader("Extracted Name:")
    if name:
        st.success(name)
    else:
        st.warning("No name could be detected in the text.")

    # Debug: Show full OCR text too (optional)
    with st.expander("Full OCR Text"):
        st.text(extracted_text)
