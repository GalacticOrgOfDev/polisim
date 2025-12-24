"""
Quick Start: Using the Context-Aware Framework

This script demonstrates how to use the new framework to extract policy mechanics
from diverse legislative sources without writing new code.
"""

import sys
sys.path.insert(0, '/e:/AI Projects/polisim')

from core.policy_context_framework import create_context_aware_extractor
from core.policy_mechanics_builder import extract_policy_context
import json


def example_1_single_payer():
    """Example: Extract M4A-style single-payer mechanics."""
    print("\n" + "="*70)
    print("EXAMPLE 1: M4A-Style Single-Payer (S.1655)")
    print("="*70)
    
    m4a_excerpt = """
    TITLE I—NATIONAL HEALTH INSURANCE PROGRAM
    
    SEC. 101. ESTABLISHMENT OF PROGRAM
    The Secretary of Health and Human Services shall establish a national health 
    insurance program to provide health insurance coverage for all residents of the 
    United States. All residents shall receive comprehensive coverage with no 
    copayments, deductibles, or cost-sharing of any kind.
    
    SEC. 102. FUNDING
    (a) PAYROLL TAXES.—There is imposed a tax on employers of 7.5 percent of 
    payroll. Employees shall contribute 4 percent of wages.
    
    (b) PROGRESSIVE INCOME TAX.—A progressive income tax on individuals earning 
    over $200,000 per year shall fund additional program costs.
    
    (c) REDIRECTION OF EXISTING SPENDING.—All federal health spending under Medicare, 
    Medicaid, and Veterans Affairs shall be consolidated into the national program.
    """
    
    # Extract with framework
    result = extract_policy_context(m4a_excerpt, "S.1655 Medicare for All")
    
    print(f"\n✓ Detected policy type: {result['policy_type']}")
    print(f"✓ Type confidence: {result['type_confidence']:.0%}")
    
    print(f"\n📊 Concepts Extracted:")
    for key in sorted(result['concepts'].keys()):
        if result['concepts'][key]:
            print(f"  • {key}: {len(result['concepts'][key])} instance(s)")
    
    print(f"\n💰 Funding Sources Found:")
    for q in result['quantities']['percentages']:
        print(f"  • {q['value']:.1f}% - {q['context'][:60]}...")
    
    print(f"\n✅ Assessment:")
    print(f"  • Strengths: {', '.join(result['assessment']['strengths'][:3])}")
    print(f"  • Gaps: {', '.join(result['assessment']['gaps']) if result['assessment']['gaps'] else 'None'}")
    print(f"  • Overall confidence: {result['assessment']['overall_confidence']:.0%}")
    
    return result


def example_2_multi_payer():
    """Example: Extract ACA-style multi-payer with regulation."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-Payer with Regulation (ACA-Style)")
    print("="*70)
    
    aca_excerpt = """
    TITLE I—QUALITY, AFFORDABLE HEALTH CARE FOR ALL AMERICANS
    
    SEC. 1001. INSURANCE MARKET REFORMS
    The private health insurance market shall be reformed through regulation. 
    Insurance companies shall not deny coverage based on preexisting conditions.
    
    SEC. 1002. INDIVIDUAL MANDATE
    All individuals shall be required to maintain minimum essential coverage 
    or pay a shared responsibility payment.
    
    SEC. 1003. AFFORDABILITY MEASURES
    (a) TAX CREDITS.—Federal tax credits shall be provided to individuals earning 
    100-400% of federal poverty level.
    
    (b) MEDICAID EXPANSION.—States are encouraged to expand Medicaid to individuals 
    earning up to 138% of federal poverty level.
    
    SEC. 1004. INSURANCE REGULATION
    Health insurance companies shall implement medical loss ratios ensuring that 
    at least 80% of premium revenue goes to medical care.
    """
    
    extractor = create_context_aware_extractor()
    policy_type, confidence = extractor.assess_policy_type(aca_excerpt)
    
    print(f"\n✓ Detected policy type: {policy_type}")
    print(f"✓ Type confidence: {confidence:.0%}")
    
    result = extract_policy_context(aca_excerpt, "ACA Healthcare Reform")
    
    print(f"\n📊 Concepts Extracted:")
    for key in sorted(result['concepts'].keys()):
        if result['concepts'][key]:
            print(f"  • {key}: {len(result['concepts'][key])} instance(s)")
    
    print(f"\n✅ Assessment:")
    print(f"  • Detected as: {result['policy_type']}")
    print(f"  • Strengths: {', '.join(result['assessment']['strengths'][:3])}")
    print(f"  • Gaps: {', '.join(result['assessment']['gaps'][:2]) if result['assessment']['gaps'] else 'None'}")
    
    return result


def example_3_novel_policy():
    """Example: Framework extracts novel policy WITHOUT new code."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Novel Policy (Hybrid Single-Payer + Public Option)")
    print("="*70)
    
    novel_excerpt = """
    TITLE I—UNIVERSAL COVERAGE FRAMEWORK
    
    SEC. 101. COVERAGE GUARANTEE
    All residents shall receive coverage through either:
    (1) A federally-operated plan with zero cost-sharing, or
    (2) Approved private plans meeting federal standards
    
    SEC. 102. FEDERAL PLAN FINANCING
    A single-payer federal plan shall be funded through:
    - An employer tax of 6% on payroll
    - An employee tax of 3% on wages
    - Progressive income taxes on high earners
    - Administrative efficiency savings from healthcare consolidation
    
    SEC. 103. TIMELINE
    The federal plan shall begin enrollment January 1, 2027.
    Full implementation shall be achieved by January 1, 2030.
    """
    
    result = extract_policy_context(novel_excerpt, "Hybrid Coverage Framework")
    
    print(f"\n✓ Framework successfully extracted: {len(result['concepts'])} concept types")
    print(f"✓ Identified {len(result['composites'])} major themes")
    
    # Show all extracted themes
    print(f"\n📋 Policy Structure (automatically identified):")
    for composite in result['composites']:
        print(f"  • {composite['theme'].upper()}: {composite['constituent_count']} concept(s), "
              f"{composite['confidence']:.0%} confidence")
    
    # Show quantities
    print(f"\n💰 Funding & Timeline Identified:")
    for pct in result['quantities']['percentages']:
        print(f"  • {pct['value']:.1f}% funding rate")
    for timeline in result['quantities']['timelines']:
        print(f"  • {int(timeline['value'])} {timeline['unit']} timeline")
    
    print(f"\n✅ Policy can now be simulated without manual parameter entry")
    
    return result


def example_4_comparison():
    """Example: Compare extraction across policy types."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Cross-Policy Comparison")
    print("="*70)
    
    policies = {
        "Single-Payer": """
            All residents shall be covered by a single federal plan. 
            Funding comes from payroll tax (7% employer, 4% employee) 
            and income tax. Zero cost-sharing at point of service.
        """,
        "Multi-Payer": """
            Private insurance shall be regulated. Individuals must maintain 
            coverage or pay a penalty. Tax credits subsidize premiums. 
            Medical loss ratios ensure affordability.
        """,
        "Hybrid": """
            A public option competes with private plans. Both provide 
            zero-cost preventive care. Funding through employer tax (5%), 
            employee payroll tax (2%), and general revenue.
        """,
    }
    
    extractor = create_context_aware_extractor()
    
    print("\n Policy Type          | Type Detected   | Confidence | Concepts | Assessment")
    print("─" * 85)
    
    for policy_name, policy_text in policies.items():
        detected_type, confidence = extractor.assess_policy_type(policy_text)
        result = extract_policy_context(policy_text, policy_name)
        concept_count = len([v for v in result['concepts'].values() if v])
        assessment_conf = result['assessment']['overall_confidence']
        
        print(f" {policy_name:19} | {detected_type:15} | {confidence:9.0%} | {concept_count:8} | {assessment_conf:.0%}")


def example_5_framework_extensibility():
    """Example: Adding a new policy type."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Extending Framework (Wealth-Tax Healthcare)")
    print("="*70)
    
    from core.policy_context_framework import ConceptTaxonomy, ConceptExpression
    
    # Define a new policy domain
    wealth_tax_healthcare = ConceptTaxonomy(
        domain_name="wealth_tax_healthcare",
        description="Healthcare funded through wealth or financial transaction taxes",
        concepts={
            "wealth_tax": [
                ConceptExpression(
                    pattern=r"wealth\s+tax|net\s+worth\s+tax",
                    context_clues=["fund", "healthcare", "revenue"],
                    confidence_boost=0.2
                ),
            ],
            "financial_transaction_tax": [
                ConceptExpression(
                    pattern=r"financial\s+transaction\s+tax|securities\s+tax",
                    context_clues=["stock", "bond", "trading"],
                    confidence_boost=0.2
                ),
            ],
            "universal_coverage": [
                ConceptExpression(
                    pattern=r"all\s+residents|universal\s+coverage",
                    confidence_boost=0.2
                ),
            ],
        },
        required_concepts={"universal_coverage"},
        scoring_weights={
            "wealth_tax": 0.3,
            "financial_transaction_tax": 0.3,
            "universal_coverage": 0.4,
        }
    )
    
    # Register new taxonomy
    extractor = create_context_aware_extractor()
    extractor.register_taxonomy(wealth_tax_healthcare)
    
    print("\n✓ New policy type registered: 'wealth_tax_healthcare'")
    
    # Test on novel policy
    novel_policy = """
    All residents shall receive comprehensive healthcare. Funding shall come from 
    a 0.1% financial transaction tax on securities trades. Additionally, a 2% 
    wealth tax on net worth exceeding $50 million shall support the program.
    """
    
    detected_type, confidence = extractor.assess_policy_type(novel_policy)
    print(f"\n✓ Framework detected new policy type: {detected_type}")
    print(f"✓ Confidence: {confidence:.0%}")
    print(f"\nNo code rewrites needed—just register a new taxonomy!")


def main():
    """Run all examples."""
    print("\n" + "#"*70)
    print("# CONTEXT-AWARE POLICY EXTRACTION: QUICK START EXAMPLES")
    print("#"*70)
    print("\nDemonstrating how the framework handles diverse legislative sources")
    print("without requiring code changes for each new policy type.")
    
    try:
        example_1_single_payer()
        example_2_multi_payer()
        example_3_novel_policy()
        example_4_comparison()
        example_5_framework_extensibility()
        
        print("\n" + "#"*70)
        print("# ✅ ALL EXAMPLES COMPLETED")
        print("#"*70)
        print("\nKey Takeaways:")
        print("  1. Framework identifies policy type automatically")
        print("  2. Extracts concepts across diverse legislative formats")
        print("  3. Handles novel policies without code changes")
        print("  4. Provides full traceability and confidence scoring")
        print("  5. Extensible: new policies = new taxonomy registration\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
