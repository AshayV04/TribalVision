#!/usr/bin/env python3
"""
Debug script to test OCR extraction
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

def fallback_extract_with_regex(raw_text: str) -> Dict[str, Optional[str]]:
    """Fallback extraction using regex patterns for common FRA form fields"""
    extracted = {
        "claimant_name": "", "spouse_name": "", "father_or_mother_name": "", 
        "address": "", "village": "", "gram_panchayat": "", "tehsil_taluka": "", 
        "district": "", "state": "", "is_scheduled_tribe": "", "is_otfd": "", "land_area": ""
    }
    
    try:
        print(f"Processing text: {raw_text[:200]}...")
        
        # Extract claimant name - look for patterns like "Name of the claimant" or "Claimant:"
        claimant_patterns = [
            r'Name of the claimant[:\s]*([A-Za-z\s]+)',
            r'Claimant[:\s]*([A-Za-z\s]+)',
            r'Name[:\s]*([A-Za-z\s]{3,})',
        ]
        
        for pattern in claimant_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                print(f"Found claimant match: '{name}'")
                if len(name) > 2 and not any(word in name.lower() for word in ['form', 'claim', 'rights', 'forest']):
                    extracted["claimant_name"] = name
                    break
        
        # Extract spouse name
        spouse_patterns = [
            r'Name of the spouse[:\s]*([A-Za-z\s]+)',
            r'Spouse[:\s]*([A-Za-z\s]+)',
        ]
        
        for pattern in spouse_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                print(f"Found spouse match: '{name}'")
                if len(name) > 2:
                    extracted["spouse_name"] = name
                    break
        
        # Extract father/mother name
        parent_patterns = [
            r'Name of father[:\s]*([A-Za-z\s]+)',
            r'Name of mother[:\s]*([A-Za-z\s]+)',
            r'Father[:\s]*([A-Za-z\s]+)',
            r'Mother[:\s]*([A-Za-z\s]+)',
        ]
        
        for pattern in parent_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                print(f"Found parent match: '{name}'")
                if len(name) > 2:
                    extracted["father_or_mother_name"] = name
                    break
        
        # Extract village
        village_patterns = [
            r'Village[:\s]*([A-Za-z\s,]+)',
            r'Village[:\s]*([A-Za-z\s]+)',
        ]
        
        for pattern in village_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                village = match.group(1).strip().rstrip(',').strip()
                print(f"Found village match: '{village}'")
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
                print(f"Found district match: '{district}'")
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
                print(f"Found address match: '{address}'")
                if len(address) > 5:
                    extracted["address"] = address
                    break
        
        print(f"Final extraction result: {extracted}")
        return extracted
        
    except Exception as e:
        print(f"Fallback extraction failed: {e}")
        return extracted

# Test with sample text
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

if __name__ == "__main__":
    result = fallback_extract_with_regex(sample_text)
    print("\n" + "="*50)
    print("EXTRACTION RESULT:")
    print("="*50)
    for key, value in result.items():
        print(f"{key}: '{value}'")





