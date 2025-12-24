#!/usr/bin/env python3
"""Test payroll extraction with new regex."""

import sys
from pathlib import Path
import re

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pdf_policy_parser import PolicyPDFProcessor

# Load USGHA
usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(usgha_path)

print("=" * 80)
print("TESTING PAYROLL TAX EXTRACTION")
print("=" * 80)

# Test the cap keyword pattern
print("\n1. Testing CAP keyword pattern:")
pattern = r'(?:cap(?:ped)?|maximum|limit(?:ed)?)[^.]*?(?:payroll|combined)[^.]*?(\d+(?:\.\d+)?)\s*percent'
matches = list(re.finditer(pattern, text, re.IGNORECASE))
print(f"   Found {len(matches)} matches:")
for i, match in enumerate(matches, 1):
    rate = float(match.group(1))
    context = text[max(0, match.start()-50):match.end()+50]
    print(f"\n   Match {i}: {rate}%")
    print(f"   Context: ...{context}...")
    print(f"   Valid (5-25 range): {5 <= rate <= 25}")

# Test generic payroll pattern
print("\n2. Testing GENERIC payroll pattern:")
pattern = r'payroll\s+(?:tax|contribution)[^.]*?(\d+(?:\.\d+)?)\s*percent'
matches = list(re.finditer(pattern, text, re.IGNORECASE))
print(f"   Found {len(matches)} matches:")
for i, match in enumerate(matches, 1):
    rate = float(match.group(1))
    context = text[max(0, match.start()-50):match.end()+50]
    print(f"\n   Match {i}: {rate}%")
    print(f"   Context: ...{context}...")
    print(f"   Valid (5-25 range): {5 <= rate <= 25}")

# Show the actual text around "capped at 15"
print("\n3. Looking for 'capped at 15':")
match = re.search(r'capped at 15', text, re.IGNORECASE)
if match:
    context = text[max(0, match.start()-100):match.end()+100]
    print(f"   Found at position {match.start()}")
    print(f"   Context: ...{context}...")
