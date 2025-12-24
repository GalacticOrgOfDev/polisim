"""
Test the integrated context-aware extraction on M4A PDF.
"""

import sys
sys.path.insert(0, '/e:/AI Projects/polisim')

from pathlib import Path
from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_extractor import extract_policy_mechanics, extract_with_context_awareness

# Path to M4A PDF
pdf_path = Path('project guidelines/policies and legislation/BILLS-118s1655is.pdf')

if not pdf_path.exists():
    print(f"❌ PDF not found at {pdf_path}")
    sys.exit(1)

print(f"\n{'='*70}")
print(f"Testing Context-Aware Extraction on M4A (S.1655)")
print(f"{'='*70}\n")

# Extract text from PDF
processor = PolicyPDFProcessor()
print("📄 Extracting text from PDF...")
text = processor.extract_text_from_pdf(pdf_path)

if "[PDF extraction requires" in text or "[Error extracting" in text:
    print(f"❌ {text}")
    sys.exit(1)

print(f"✓ Extracted {len(text)} characters from PDF")
print(f"✓ First 200 chars: {text[:200]}...\n")

# Test new context-aware extraction
print("🔍 Running context-aware extraction...")
try:
    mechanics = extract_with_context_awareness(text, "S.1655 Medicare for All")
    
    print(f"\n✅ Extraction Results (Context-Aware):")
    print(f"   Policy Type: {mechanics.policy_type}")
    print(f"   Confidence Score: {mechanics.confidence_score:.1%}")
    print(f"   Universal Coverage: {mechanics.universal_coverage}")
    print(f"   Zero Out-of-Pocket: {mechanics.zero_out_of_pocket}")
    print(f"   Funding Mechanisms: {len(mechanics.funding_mechanisms)}")
    for i, mech in enumerate(mechanics.funding_mechanisms, 1):
        print(f"     {i}. {mech.source_type}: {mech.percentage_rate}% rate" if mech.percentage_rate else f"     {i}. {mech.source_type}")
    print(f"   Timeline Milestones: {len(mechanics.timeline_milestones)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Compare with standard extraction
print("\n" + "="*70)
print("Comparing with standard extraction...")
try:
    standard = extract_policy_mechanics(text, policy_type="healthcare")
    print(f"\n📊 Standard Extraction Results:")
    print(f"   Policy Type: {standard.policy_type}")
    print(f"   Confidence Score: {standard.confidence_score:.1%}")
    print(f"   Universal Coverage: {standard.universal_coverage}")
    print(f"   Zero Out-of-Pocket: {standard.zero_out_of_pocket}")
    print(f"   Funding Mechanisms: {len(standard.funding_mechanisms)}")
    
    # Show improvement
    print(f"\n📈 Improvement:")
    if mechanics.confidence_score > standard.confidence_score:
        improvement = ((mechanics.confidence_score - standard.confidence_score) / standard.confidence_score * 100) if standard.confidence_score > 0 else 100
        print(f"   Confidence improved by: {improvement:.0f}%")
    if mechanics.universal_coverage and not standard.universal_coverage:
        print(f"   Universal coverage now: ✓ Detected")
    if mechanics.zero_out_of_pocket and not standard.zero_out_of_pocket:
        print(f"   Zero cost-sharing now: ✓ Detected")
    if len(mechanics.funding_mechanisms) > len(standard.funding_mechanisms):
        print(f"   Funding mechanisms found: +{len(mechanics.funding_mechanisms) - len(standard.funding_mechanisms)}")
    
except Exception as e:
    print(f"⚠️  Standard extraction error: {e}")

print(f"\n{'='*70}")
print("✅ Integration test complete!")
print(f"{'='*70}\n")
