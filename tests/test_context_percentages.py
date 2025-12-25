#!/usr/bin/env python3
"""Test context framework percentages."""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_builder import extract_policy_context

# Load USGHA
usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(usgha_path)

# Extract with context
result = extract_policy_context(text, "USGHA")

print("=" * 80)
print("CONTEXT FRAMEWORK EXTRACTION")
print("=" * 80)

print(f"\nPolicy Type: {result.get('policy_type', 'unknown')}")
print(f"Confidence: {result.get('confidence', result.get('confidence_score', 0)):.2%}")

print(f"\nPercentages found:")
for i, pct in enumerate(result['quantities']['percentages'], 1):
    print(f"  {i}. {pct['value']}%")

print(f"\nConcepts found:")
for key, occurrences in result['concepts'].items():
    if occurrences:
        print(f"  {key}: {len(occurrences)} occurrences")
        for occ in occurrences[:2]:  # First 2
            # Handle both dict and string occurrences
            if isinstance(occ, dict):
                text = occ.get('text', str(occ))
            else:
                text = str(occ)
            print(f"    - {text[:80]}...")
