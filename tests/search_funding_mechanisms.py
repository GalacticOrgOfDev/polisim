#!/usr/bin/env python3
"""Search for all funding mechanisms in USGHA."""

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
print("SEARCHING FOR FUNDING MECHANISMS IN USGHA")
print("=" * 80)

# Search for "Section 6" or "Sec. 6" more broadly
sec6_matches = list(re.finditer(r'Sec(?:tion)?\s*\.?\s*6', text, re.IGNORECASE))
print(f"\n'Section 6' found at {len(sec6_matches)} locations:")
for match in sec6_matches:
    pos = match.start()
    context = text[pos:pos+500]
    print(f"\nPosition {pos}:")
    print(context[:300])
    print("...")

# Look for funding-related keywords
print("\n" + "=" * 80)
print("FUNDING KEYWORDS:")
print("=" * 80)

keywords = [
    'payroll tax',
    'income tax', 
    'wealth tax',
    'capital gains',
    'estate tax',
    'corporate tax',
    'financial transaction',
    'excise tax',
    'tariff',
    'premium',
    'Medicare',
    'Medicaid',
    'SNAP',
    'WIC',
    'pharmaceutical',
    'drug pricing',
    'reinsurance'
]

for keyword in keywords:
    matches = list(re.finditer(re.escape(keyword), text, re.IGNORECASE))
    if matches:
        print(f"\n'{keyword}': {len(matches)} occurrences")
        # Show first occurrence context
        first = matches[0]
        context = text[max(0, first.start()-100):first.end()+100]
        print(f"  First at position {first.start()}: ...{context}...")
