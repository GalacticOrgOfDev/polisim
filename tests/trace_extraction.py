"""
Trace the full extraction pipeline for M4A.
"""

import sys
sys.path.insert(0, '/e:/AI Projects/polisim')

from pathlib import Path
from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_extractor import extract_policy_mechanics, extract_with_context_awareness

# Extract text
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(Path('project guidelines/policies and legislation/BILLS-118s1655is.pdf'))

print(f"\n{'='*70}")
print("TRACING EXTRACTION PIPELINE")
print(f"{'='*70}\n")

print(f"Text length: {len(text)} characters\n")

# Trace context-aware extraction
print("1️⃣ Context-Aware Extraction:")
try:
    from core.policy_mechanics_builder import extract_policy_context
    print("   ✓ Framework imported")
    
    context_result = extract_policy_context(text, "M4A Test")
    print(f"   ✓ Context extraction ran")
    print(f"     - Policy type: {context_result['policy_type']}")
    print(f"     - Concepts found: {sum(len(v) for v in context_result['concepts'].values())}")
    print(f"     - Assessment confidence: {context_result['assessment']['overall_confidence']:.0%}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Trace context-aware mechanics
print("2️⃣ extract_with_context_awareness():")
try:
    mech = extract_with_context_awareness(text, "M4A")
    print(f"   ✓ Function completed")
    print(f"     - Confidence: {mech.confidence_score:.0%}")
    print(f"     - Universal coverage: {mech.universal_coverage}")
    print(f"     - Zero OOP: {mech.zero_out_of_pocket}")
    print(f"     - Funding mechanisms: {len(mech.funding_mechanisms)}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    import traceback
    traceback.print_exc()

# Trace standard extraction path
print("3️⃣ extract_policy_mechanics() main entry point:")
try:
    mech = extract_policy_mechanics(text, "healthcare")
    print(f"   ✓ Function completed")
    print(f"     - Confidence: {mech.confidence_score:.0%}")
    print(f"     - Funding mechanisms: {len(mech.funding_mechanisms)}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print(f"{'='*70}\n")
