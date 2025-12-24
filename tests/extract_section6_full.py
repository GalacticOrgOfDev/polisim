#!/usr/bin/env python3
"""Extract full Section 6 from USGHA."""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pdf_policy_parser import PolicyPDFProcessor

# Load USGHA
usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(usgha_path)

# Extract from position 12378 (where Section 6 starts)
section6_start = 12378
# Section 7 should be nearby - let's extract a large chunk
section6_text = text[section6_start:section6_start + 10000]

print("=" * 80)
print("SECTION 6: FUNDING MECHANISMS AND TRANSITION (Full Text)")
print("=" * 80)
print(section6_text)
print("=" * 80)
