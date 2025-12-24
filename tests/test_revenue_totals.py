#!/usr/bin/env python3
"""Test standard extraction with full GDP details."""

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
print("STANDARD EXTRACTION - FULL MECHANISM DETAILS")
print("=" * 80)

print(f"\nTotal mechanisms: {len(mechs.funding_mechanisms)}")

# Calculate total revenue as % GDP
total_gdp_pct = 0.0

print(f"\n{'#':<3} {'Type':<25} {'Rate':<8} {'GDP%':<8} {'Description'}")
print("-" * 100)

for i, m in enumerate(mechs.funding_mechanisms, 1):
    rate_str = f"{m.percentage_rate}%" if m.percentage_rate else "N/A"
    gdp_str = f"{m.percentage_gdp:.2f}%" if m.percentage_gdp else "N/A"
    
    if m.percentage_gdp:
        total_gdp_pct += m.percentage_gdp
    
    print(f"{i:<3} {m.source_type:<25} {rate_str:<8} {gdp_str:<8} {m.description[:50]}")

print("-" * 100)
print(f"\nTOTAL REVENUE: ~{total_gdp_pct:.2f}% of GDP")
print(f"\nFor $29T GDP in 2025:")
print(f"  Total Revenue: ${total_gdp_pct * 0.29:.2f}T")
print(f"  Baseline Healthcare: ~$5.4T (18.5% GDP)")
print(f"  Surplus/Deficit: ${(total_gdp_pct * 0.29) - 5.4:.2f}T")
