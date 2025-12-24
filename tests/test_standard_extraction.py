#!/usr/bin/env python3
"""Test standard extraction (non-context-aware)."""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_extractor import PolicyMechanicsExtractor

# Load USGHA
usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(usgha_path)

# Standard extraction
mechs = PolicyMechanicsExtractor.extract_generic_healthcare_mechanics(text, "USGHA")

print("=" * 80)
print("STANDARD EXTRACTION (Non-Context-Aware)")
print("=" * 80)

print(f"\nTotal mechanisms: {len(mechs.funding_mechanisms)}")

# Find payroll
payroll = [m for m in mechs.funding_mechanisms if "payroll" in m.source_type.lower()]
print(f"\nPayroll mechanisms: {len(payroll)}")
for m in payroll:
    print(f"  - {m.source_type}: {m.percentage_rate}%")
    print(f"    Description: {m.description[:80]}")

# Show all mechanisms
print(f"\nAll mechanisms:")
for i, m in enumerate(mechs.funding_mechanisms, 1):
    print(f"  {i}. {m.source_type}: {m.percentage_rate}% - {m.description[:60]}")
