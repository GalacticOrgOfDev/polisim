"""
Debug: Check what the context framework finds in M4A PDF text.
"""

import sys
sys.path.insert(0, '/e:/AI Projects/polisim')

from pathlib import Path
from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_context_framework import create_context_aware_extractor
from core.policy_mechanics_builder import extract_policy_context

# Extract text
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(Path('project guidelines/policies and legislation/BILLS-118s1655is.pdf'))

print(f"\n{'='*70}")
print(f"DEBUG: Context Framework on M4A PDF")
print(f"{'='*70}\n")

# Test framework directly
print("1️⃣ Framework Assessment:")
extractor = create_context_aware_extractor()
policy_type, confidence = extractor.assess_policy_type(text)
print(f"   Policy Type: {policy_type}")
print(f"   Confidence: {confidence:.0%}\n")

print("2️⃣ Framework Extraction:")
result = extract_policy_context(text, "S.1655 Medicare for All")

print(f"   Detected Type: {result['policy_type']}")
print(f"   Type Confidence: {result['type_confidence']:.0%}")
print(f"   Overall Assessment: {result['assessment']['overall_confidence']:.0%}\n")

print("3️⃣ Concepts Found:")
concept_count = 0
for key, concepts in result['concepts'].items():
    if concepts:
        concept_count += len(concepts)
        print(f"   {key}: {len(concepts)} occurrence(s)")

print(f"   Total: {concept_count} concepts\n")

if concept_count == 0:
    print("   ⚠️  No concepts found. Checking if patterns match...\n")
    
    print("4️⃣ Manual Pattern Check:")
    import re
    
    # Check for funding patterns
    payroll_pattern = r"payroll\s+(?:tax|contribution|assessment)"
    income_pattern = r"(?:income\s+)?tax(?:es)?"
    employer_pattern = r"employer.*contribution"
    employee_pattern = r"employee.*contribution"
    
    patterns = [
        ("Payroll", payroll_pattern),
        ("Income tax", income_pattern),
        ("Employer contribution", employer_pattern),
        ("Employee contribution", employee_pattern),
    ]
    
    for name, pattern in patterns:
        matches = len(re.findall(pattern, text, re.IGNORECASE))
        print(f"   {name}: {matches} matches")
    
    # Show relevant excerpts
    print("\n5️⃣ Text Excerpts (searching for 'payroll'):")
    for match in re.finditer(r'.{0,80}payroll.{0,80}', text, re.IGNORECASE)[:3]:
        excerpt = match.group(0).replace('\n', ' ')
        print(f"   ...{excerpt}...\n")

print(f"\n{'='*70}\n")
