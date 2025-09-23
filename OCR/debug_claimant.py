#!/usr/bin/env python3
"""
Debug claimant name extraction
"""

import re

sample_text = """'Name of the claimant 6): KBPCOES
'Name of the spouse KBPCOES1"""

print("Sample text:")
print(repr(sample_text))
print()

# Test different patterns
patterns = [
    r'Name of the claimant[:\s]*[0-9]*\)?\s*([A-Za-z\s]+?)(?=\n|Name of the spouse|$)',
    r'Name of the claimant[:\s]*[0-9]*\)?\s*([A-Za-z\s]+)',
    r'Name of the claimant[:\s]*([A-Za-z\s]+?)(?=\n|Name of the spouse|$)',
    r'Name of the claimant[:\s]*([A-Za-z\s]+)',
    r'Name of the claimant[:\s]*[0-9]*\)?\s*([A-Za-z0-9\s]+?)(?=\n|Name of the spouse|$)',
    r'Name of the claimant[:\s]*[0-9]*\)?\s*([A-Za-z0-9\s]+)',
]

for i, pattern in enumerate(patterns):
    print(f"Pattern {i+1}: {pattern}")
    match = re.search(pattern, sample_text, re.IGNORECASE)
    if match:
        print(f"  Match: '{match.group(1)}'")
    else:
        print("  No match")
    print()

# Test with simpler approach
print("Testing simpler approach:")
simple_patterns = [
    r'Name of the claimant[^:]*:\s*([A-Za-z\s]+)',
    r'Name of the claimant[^:]*:\s*([A-Za-z0-9\s]+)',
    r'Name of the claimant[^:]*:\s*([A-Za-z0-9\s]+?)(?=\n|Name of the spouse)',
]

for i, pattern in enumerate(simple_patterns):
    print(f"Simple pattern {i+1}: {pattern}")
    match = re.search(pattern, sample_text, re.IGNORECASE)
    if match:
        print(f"  Match: '{match.group(1)}'")
    else:
        print("  No match")
    print()





