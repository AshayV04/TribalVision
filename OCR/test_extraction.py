#!/usr/bin/env python3
"""
Test extraction directly
"""

import os
import sys
import json
import re
from typing import Dict, Optional

# Fix numpy import issue
current_dir = os.getcwd()
if current_dir in sys.path:
    sys.path.remove(current_dir)

# Change to safe directory
os.chdir('/tmp')

# Add OCR directory to path
sys.path.append('/Users/ashayvairat/Public/FRA/fra_atlas_webgis version 7/OCR')

def test_extraction():
    # Import the functions
    from flask_ocr_api import human_like_extract_with_gemini, fallback_extract_with_regex
    
    sample_text = """(Becoprion of Fores Fight) Rae, 2008

ANNEXURE -I
[See rule 6()]
FORM-A
CLAIM FORM FOR RIGHTS TO FOREST LAND
[See rule 11(1)(a)]

'Name of the claimant 6): KBPCOES
'Name of the spouse KBPCOES1
'Name of father/ mother KBPCOES2
Adaress: SADAR BAZAR
Village: SATARA,
Gram Panchayat: SATARAL
'Tehsil! Taluka: SATARAD
District SATARA
@) Scheduled Tribe: Yes/No
(Attach authenticated copy of Certificate)
(© Other Traditional Forest Dweller: Yes/No"""

    print("Testing Gemini extraction...")
    try:
        gemini_result = human_like_extract_with_gemini(sample_text)
        print(f"Gemini result: {gemini_result}")
    except Exception as e:
        print(f"Gemini failed: {e}")
    
    print("\nTesting fallback extraction...")
    try:
        fallback_result = fallback_extract_with_regex(sample_text)
        print(f"Fallback result: {fallback_result}")
    except Exception as e:
        print(f"Fallback failed: {e}")

if __name__ == "__main__":
    test_extraction()





