#!/usr/bin/env python3
"""
See exactly what concepts the context framework finds in M4A and USGHA
"""

from pathlib import Path
from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_builder import PolicyMechanicsBuilder

print("=" * 80)
print("CONTEXT FRAMEWORK ANALYSIS")
print("=" * 80)

# M4A
print("\nM4A (S.1655):")
print("-" * 80)

m4a_path = Path("project guidelines/policies and legislation/BILLS-118s1655is.pdf")
if m4a_path.exists():
    processor = PolicyPDFProcessor()
    text = processor.extract_text_from_pdf(m4a_path)
    
    builder = PolicyMechanicsBuilder()
    context = builder.build_from_text(text, "M4A")
    
    print(f"Policy Type: {context['policy_type']}")
    print(f"Type Confidence: {context['type_confidence']}")
    print(f"\nConcepts Found:")
    for concept_key, concept_list in context['concepts'].items():
        if concept_list:
            print(f"  {concept_key}: {len(concept_list)} occurrences")
    
    print(f"\nQuantities Found:")
    print(f"  Percentages: {len(context['quantities']['percentages'])}")
    for pct in context['quantities']['percentages'][:5]:
        print(f"    - {pct['value']}% ({pct['context'][:60]}...)")
    print(f"  Currencies: {len(context['quantities']['currencies'])}")
    for curr in context['quantities']['currencies'][:3]:
        print(f"    - ${curr['value']} {curr['unit']} ({curr['context'][:60]}...)")
else:
    print("M4A PDF not found")

# USGHA
print("\n\nUSGHA (V1.22):")
print("-" * 80)

usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")
if usgha_path.exists():
    processor = PolicyPDFProcessor()
    text = processor.extract_text_from_pdf(usgha_path)
    
    builder = PolicyMechanicsBuilder()
    context = builder.build_from_text(text, "USGHA")
    
    print(f"Policy Type: {context['policy_type']}")
    print(f"Type Confidence: {context['type_confidence']}")
    print(f"\nConcepts Found:")
    for concept_key, concept_list in context['concepts'].items():
        if concept_list:
            print(f"  {concept_key}: {len(concept_list)} occurrences")
    
    print(f"\nQuantities Found:")
    print(f"  Percentages: {len(context['quantities']['percentages'])}")
    for pct in context['quantities']['percentages'][:10]:
        print(f"    - {pct['value']}% ({pct['context'][:60]}...)")
    print(f"  Currencies: {len(context['quantities']['currencies'])}")
    for curr in context['quantities']['currencies'][:3]:
        print(f"    - ${curr['value']} {curr['unit']} ({curr['context'][:60]}...)")
else:
    print("USGHA PDF not found")

print("\n" + "=" * 80)
