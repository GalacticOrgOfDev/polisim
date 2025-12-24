"""
Context-Aware Framework Validation Tests
Demonstrates the new semantic extraction on diverse policy types.
"""

import sys
sys.path.insert(0, '/e:/AI Projects/polisim')

from core.policy_context_framework import create_context_aware_extractor
from core.policy_mechanics_builder import extract_policy_context
import json


def test_single_payer_extraction():
    """Test extraction on M4A-style single-payer language."""
    m4a_sample = """
    SECTION 1. UNIVERSAL HEALTHCARE SYSTEM
    
    All residents of the United States shall be covered under a single-payer universal health program.
    
    SECTION 2. COVERAGE REQUIREMENTS
    
    The program shall provide comprehensive coverage with zero copayments, deductibles, or premiums at point of service.
    All residents, including children, shall be eligible immediately upon implementation.
    
    SECTION 3. FUNDING MECHANISMS
    
    The program shall be financed through:
    (A) A payroll tax on employers of 7.5% of payroll
    (B) A payroll tax on employees of 4% of wages
    (C) A progressive income tax on individuals with incomes above $200,000
    (D) Redirection of existing Medicare and Medicaid spending
    (E) Administrative efficiency savings from eliminating insurance overhead
    
    The combination of these sources shall generate sufficient revenue to fund the universal system.
    """
    
    print("\n" + "="*60)
    print("TEST 1: M4A-Style Single-Payer Detection")
    print("="*60)
    
    extractor = create_context_aware_extractor()
    policy_type, confidence = extractor.assess_policy_type(m4a_sample)
    
    print(f"\nDetected Policy Type: {policy_type}")
    print(f"Confidence: {confidence:.2%}")
    
    builder = extract_policy_context(m4a_sample, "M4A Sample")
    print(f"\nExtracted {builder['concepts'].__len__()} concept categories")
    print(f"Policy Type Assessment: {builder['policy_type']} ({builder['type_confidence']:.2%})")
    print(f"Gaps: {builder['assessment']['gaps']}")
    print(f"Strengths: {builder['assessment']['strengths']}")
    print(f"Overall Confidence: {builder['assessment']['overall_confidence']:.2%}")
    
    # Show extracted concepts
    print("\n--- Key Extracted Concepts ---")
    for key, concepts_list in builder['concepts'].items():
        if concepts_list:
            print(f"\n{key}:")
            for c in concepts_list[:2]:  # Show first 2 of each type
                print(f"  - {c['concept_name']}: {c['value'][:60]}... ({c['confidence']:.2%})")
    
    # Show quantities
    print("\n--- Extracted Quantities ---")
    quantities = builder['quantities']
    print(f"Percentages found: {len(quantities['percentages'])}")
    for q in quantities['percentages']:
        print(f"  {q['value']}{q['unit']} confidence: {q['confidence']:.2%}")
    
    return builder


def test_multi_payer_extraction():
    """Test extraction on multi-payer regulatory framework."""
    aca_sample = """
    SECTION 1. INSURANCE MARKET REFORMS
    
    Private insurance shall be regulated to expand coverage to individuals with preexisting conditions.
    
    SECTION 2. INDIVIDUAL MANDATE
    
    All individuals shall be required to maintain health insurance coverage or pay a penalty.
    
    SECTION 3. COST CONTROLS
    
    Insurance companies shall be subject to price regulation and must maintain minimum coverage standards.
    Preventive care shall be covered with no cost-sharing.
    
    SECTION 4. MEDICAID EXPANSION
    
    States shall have the option to expand Medicaid eligibility to individuals earning up to 138% of federal poverty level.
    """
    
    print("\n" + "="*60)
    print("TEST 2: Multi-Payer Regulatory Framework Detection")
    print("="*60)
    
    extractor = create_context_aware_extractor()
    policy_type, confidence = extractor.assess_policy_type(aca_sample)
    
    print(f"\nDetected Policy Type: {policy_type}")
    print(f"Confidence: {confidence:.2%}")
    
    builder = extract_policy_context(aca_sample, "ACA Sample")
    print(f"\nPolicy Type: {builder['policy_type']}")
    print(f"Concepts Found: {len(builder['concepts'])}")
    
    print("\n--- Extracted Concepts ---")
    for key, concepts_list in builder['concepts'].items():
        if concepts_list:
            print(f"{key}: {len(concepts_list)} occurrence(s)")
    
    return builder


def test_hybrid_extraction():
    """Test on a policy that mixes multiple approaches."""
    hybrid_sample = """
    SECTION 1. COMPREHENSIVE HEALTHCARE REFORM
    
    This Act establishes a pathway to universal coverage through:
    
    PART A: SINGLE-PAYER FOUNDATION
    - All residents shall be enrolled in a federal health program
    - Zero copayments, deductibles, or premiums
    - Funded through a 6% payroll tax on employers and 3.5% on employees
    - Income-based supplemental contributions for high earners
    
    PART B: TRANSITION MECHANISMS
    - Existing Medicare and Medicaid systems shall be consolidated into the federal program
    - Private insurance companies shall be prohibited from duplicating coverage
    - A 10-year phase-in period beginning January 1, 2026
    
    PART C: ADMINISTRATIVE STRUCTURE
    - Regional oversight boards shall ensure equitable access
    - Quarterly reporting on coverage and outcomes
    - Annual adjustments to payroll tax rates based on medical inflation
    """
    
    print("\n" + "="*60)
    print("TEST 3: Hybrid Policy Detection")
    print("="*60)
    
    extractor = create_context_aware_extractor()
    policy_type, confidence = extractor.assess_policy_type(hybrid_sample)
    
    print(f"\nDetected Policy Type: {policy_type}")
    print(f"Confidence: {confidence:.2%}")
    
    builder = extract_policy_context(hybrid_sample, "Hybrid Reform")
    print(f"\nPolicy Type: {builder['policy_type']}")
    print(f"Type Confidence: {builder['type_confidence']:.2%}")
    print(f"Overall Assessment Confidence: {builder['assessment']['overall_confidence']:.2%}")
    
    print("\n--- Concept Composites (Themes) ---")
    for composite in builder['composites']:
        print(f"\n{composite['theme'].upper()}:")
        print(f"  Constituent concepts: {composite['constituent_count']}")
        print(f"  Confidence: {composite['confidence']:.2%}")
        if composite['derived_value']:
            print(f"  Details: {composite['derived_value']}")
    
    return builder


def test_assessment_accuracy():
    """Compare assessment accuracy across policy types."""
    print("\n" + "="*60)
    print("TEST 4: Assessment Accuracy Summary")
    print("="*60)
    
    test_results = {
        "Single-Payer (M4A-style)": test_single_payer_extraction(),
        "Multi-Payer (ACA-style)": test_multi_payer_extraction(),
        "Hybrid": test_hybrid_extraction(),
    }
    
    print("\n" + "="*60)
    print("ACCURACY SUMMARY")
    print("="*60)
    
    for policy_name, result in test_results.items():
        assessment = result['assessment']
        print(f"\n{policy_name}:")
        print(f"  Detected Type: {assessment['policy_type']}")
        print(f"  Overall Confidence: {assessment['overall_confidence']:.2%}")
        print(f"  Strengths ({len(assessment['strengths'])}): {', '.join(assessment['strengths'][:2])}")
        print(f"  Gaps ({len(assessment['gaps'])}): {', '.join(assessment['gaps'][:2]) if assessment['gaps'] else 'None'}")


def test_quantity_extraction():
    """Demonstrate quantity extraction (percentages, dates, amounts)."""
    print("\n" + "="*60)
    print("TEST 5: Quantity Extraction")
    print("="*60)
    
    sample = """
    A 7.5% employer payroll tax and 4% employee payroll tax shall fund $2.5 trillion in annual healthcare spending.
    Implementation shall occur over a 5-year phase-in beginning in 2026.
    By December 31, 2030, all residents shall be covered.
    """
    
    builder = extract_policy_context(sample, "Quantity Test")
    quantities = builder['quantities']
    
    print(f"\nPercentages found: {len(quantities['percentages'])}")
    for q in quantities['percentages']:
        print(f"  {q['value']}{q['unit']} - {q['context'][:50]}...")
    
    print(f"\nCurrencies found: {len(quantities['currencies'])}")
    for q in quantities['currencies']:
        print(f"  ${q['value']}{q['unit']} - {q['context'][:50]}...")
    
    print(f"\nTimeline indicators: {len(quantities['timelines'])}")
    for q in quantities['timelines']:
        print(f"  {q['value']} {q['unit']} - {q['context'][:50]}...")


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# POLICY CONTEXT EXTRACTION FRAMEWORK VALIDATION")
    print("#"*60)
    print("\nThis test suite validates semantic concept extraction")
    print("across diverse legislative approaches.")
    
    try:
        test_assessment_accuracy()
        test_quantity_extraction()
        
        print("\n" + "#"*60)
        print("# ALL TESTS COMPLETED SUCCESSFULLY")
        print("#"*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
