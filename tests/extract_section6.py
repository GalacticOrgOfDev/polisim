#!/usr/bin/env python3
"""Extract Section 6 from USGHA."""

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

# Find Section 6
section6_match = re.search(r'SEC\.\s*6\..*?(?=SEC\.\s*7\.|\Z)', text, re.DOTALL | re.IGNORECASE)

if section6_match:
    section6_text = section6_match.group(0)
    print("=" * 80)
    print("SECTION 6: FUNDING MECHANISMS AND TRANSITION")
    print("=" * 80)
    print(section6_text[:5000])  # First 5000 chars
    print("\n" + "=" * 80)
    print(f"Total Section 6 length: {len(section6_text):,} characters")
    print("=" * 80)
    
    # Look for subsections
    subsections = re.findall(r'\(([a-z])\)[^\(]{0,200}', section6_text[:5000])
    print(f"\nSubsections found: {subsections[:20]}")
else:
    print("Section 6 not found")
