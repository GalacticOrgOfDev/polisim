#!/usr/bin/env python3
"""
Debug USGHA extraction to see what funding mechanisms are being detected
and what percentages are being assigned.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_extractor import extract_policy_mechanics

# Load USGHA PDF
usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")

if not usgha_path.exists():
    print(f"ERROR: USGHA not found at {usgha_path}")
    exit(1)

print("=" * 80)
print("USGHA EXTRACTION DEBUG")
print("=" * 80)

# Extract text
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(usgha_path)
print(f"\n1. PDF TEXT EXTRACTED")
print(f"   Size: {len(text):,} characters")

# Look for percentage patterns
print(f"\n2. PERCENTAGE PATTERNS IN TEXT")
import re
percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
print(f"   Found {len(percentages)} percentage values:")
for pct in percentages[:20]:  # First 20
    print(f"      - {pct}%")
if len(percentages) > 20:
    print(f"      ... and {len(percentages) - 20} more")

# Look for tax patterns
print(f"\n3. TAX-RELATED PATTERNS")
tax_patterns = [
    ('payroll', r'payroll\s+(?:tax|rate|contribution)', 0),
    ('income tax', r'income\s+tax', 0),
    ('payroll rate', r'(\d+(?:\.\d+)?)\s*%\s+(?:payroll|wage)', 0),
    ('employer contrib', r'employer\s+(?:contribut|taxed)', 0),
]

for name, pattern, count in tax_patterns:
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    print(f"   {name}: {len(matches)} matches")

# Extract mechanics
print(f"\n4. EXTRACTION RESULTS")
mechanics = extract_policy_mechanics(text, policy_type="healthcare")

print(f"   Policy Type: {mechanics.policy_type}")
print(f"   Confidence: {mechanics.confidence_score * 100:.1f}%")
print(f"   Universal Coverage: {mechanics.universal_coverage}")
print(f"   Zero OOP: {mechanics.zero_out_of_pocket}")
print(f"\n   Funding Mechanisms: {len(mechanics.funding_mechanisms)}")

for i, mech in enumerate(mechanics.funding_mechanisms, 1):
    print(f"\n   Mechanism {i}: {mech.source_type}")
    print(f"      Description: {mech.description}")
    print(f"      Rate: {mech.percentage_rate}%")
    print(f"      % GDP: {mech.percentage_gdp}")
    if mech.conditions:
        print(f"      Conditions: {mech.conditions}")



print("\n" + "=" * 80)
