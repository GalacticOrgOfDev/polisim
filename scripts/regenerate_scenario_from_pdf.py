#!/usr/bin/env python3
"""
Regenerate scenario JSON from PDF extraction.

This script extracts policy mechanics from a PDF and generates a properly
formatted scenario JSON file with all funding mechanisms and their GDP percentages.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_extractor import extract_policy_mechanics, PolicyMechanicsExtractor
from core.healthcare import PolicyType


def mechanics_to_scenario_dict(mechanics, policy_name: str, policy_type: str = "USGHA") -> dict:
    """
    Convert PolicyMechanics to scenario JSON format.
    
    Args:
        mechanics: PolicyMechanics object from extraction
        policy_name: Name of the policy
        policy_type: Type (USGHA, M4A, etc.)
    
    Returns:
        Dictionary in scenario JSON format
    """
    scenario = {
        "policy_name": policy_name,
        "policy_type": policy_type,
        "description": f"Generated from PDF extraction - {len(mechanics.funding_mechanisms)} funding mechanisms",
        "mechanics": {
            "funding_mechanisms": [],
            "surplus_allocation": None,
            "circuit_breakers": [],
            "innovation_fund": None,
            "timeline_milestones": [],
            "target_spending_pct_gdp": mechanics.target_spending_pct_gdp,
            "target_spending_year": mechanics.target_spending_year,
            "universal_coverage": mechanics.universal_coverage,
            "zero_out_of_pocket": mechanics.zero_out_of_pocket,
            "confidence_score": mechanics.confidence_score
        }
    }
    
    # Add funding mechanisms
    for mech in mechanics.funding_mechanisms:
        mech_dict = {
            "source_type": mech.source_type,
            "description": mech.description,
            "percentage_rate": mech.percentage_rate,
            "percentage_gdp": mech.percentage_gdp,
        }
        
        # Optional fields
        if mech.phase_in_start:
            mech_dict["phase_in_start"] = mech.phase_in_start
        if mech.phase_in_end:
            mech_dict["phase_in_end"] = mech.phase_in_end
        if mech.conditions:
            mech_dict["conditions"] = mech.conditions
        if mech.estimated_amount:
            mech_dict["estimated_amount"] = mech.estimated_amount
            
        scenario["mechanics"]["funding_mechanisms"].append(mech_dict)
    
    # Add surplus allocation
    if mechanics.surplus_allocation:
        scenario["mechanics"]["surplus_allocation"] = {
            "contingency_reserve_pct": mechanics.surplus_allocation.contingency_reserve_pct,
            "debt_reduction_pct": mechanics.surplus_allocation.debt_reduction_pct,
            "infrastructure_pct": mechanics.surplus_allocation.infrastructure_pct,
            "dividends_pct": mechanics.surplus_allocation.dividends_pct,
            "other_allocations": mechanics.surplus_allocation.other_allocations,
            "trigger_conditions": mechanics.surplus_allocation.trigger_conditions
        }
    
    # Add circuit breakers
    for cb in mechanics.circuit_breakers:
        scenario["mechanics"]["circuit_breakers"].append({
            "trigger_type": cb.trigger_type,
            "threshold_value": cb.threshold_value,
            "threshold_unit": cb.threshold_unit,
            "action": cb.action,
            "description": cb.description
        })
    
    # Add innovation fund
    if mechanics.innovation_fund:
        scenario["mechanics"]["innovation_fund"] = {
            "funding_min_pct": mechanics.innovation_fund.funding_min_pct,
            "funding_max_pct": mechanics.innovation_fund.funding_max_pct,
            "funding_base": mechanics.innovation_fund.funding_base,
            "prize_min_dollars": mechanics.innovation_fund.prize_min_dollars,
            "prize_max_dollars": mechanics.innovation_fund.prize_max_dollars,
            "annual_cap_pct": mechanics.innovation_fund.annual_cap_pct
        }
    
    # Add timeline milestones
    for milestone in mechanics.timeline_milestones:
        scenario["mechanics"]["timeline_milestones"].append({
            "year": milestone.year,
            "description": milestone.description,
            "metric_type": milestone.metric_type,
            "target_value": milestone.target_value
        })
    
    return scenario


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Regenerate scenario JSON from PDF extraction")
    parser.add_argument("pdf_path", help="Path to policy PDF file")
    parser.add_argument("--output", "-o", help="Output JSON file path", default=None)
    parser.add_argument("--policy-name", help="Policy name", default=None)
    parser.add_argument("--policy-type", help="Policy type (USGHA, M4A, etc.)", default="USGHA")
    parser.add_argument("--use-standard", action="store_true", help="Use standard extraction (not context-aware)")
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"❌ Error: PDF not found at {pdf_path}")
        return 1
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Default: policies/scenario_{filename}.json
        output_path = project_root / "policies" / f"scenario_{pdf_path.stem.lower().replace(' ', '_')}.json"
    
    # Determine policy name
    policy_name = args.policy_name or pdf_path.stem
    
    print("=" * 80)
    print("SCENARIO GENERATION FROM PDF")
    print("=" * 80)
    print(f"\nInput PDF: {pdf_path}")
    print(f"Output JSON: {output_path}")
    print(f"Policy Name: {policy_name}")
    print(f"Policy Type: {args.policy_type}")
    
    # Extract text from PDF
    print("\n1. Extracting text from PDF...")
    processor = PolicyPDFProcessor()
    text = processor.extract_text_from_pdf(pdf_path)
    print(f"   ✓ Extracted {len(text):,} characters")
    
    # Extract mechanics
    print("\n2. Extracting policy mechanics...")
    if args.use_standard:
        print("   Using standard extraction (non-context-aware)")
        mechanics = PolicyMechanicsExtractor.extract_generic_healthcare_mechanics(text, policy_name)
    else:
        print("   Using context-aware extraction")
        mechanics = extract_policy_mechanics(text, policy_type="healthcare")
    
    print(f"   ✓ Found {len(mechanics.funding_mechanisms)} funding mechanisms")
    
    # Calculate total revenue
    total_gdp_pct = sum(m.percentage_gdp or 0 for m in mechanics.funding_mechanisms)
    print(f"   ✓ Total revenue: {total_gdp_pct:.2f}% GDP")
    
    # Show mechanism summary
    print("\n3. Funding Mechanisms:")
    for i, mech in enumerate(mechanics.funding_mechanisms, 1):
        rate_str = f"{mech.percentage_rate}%" if mech.percentage_rate else "N/A"
        gdp_str = f"{mech.percentage_gdp:.2f}%" if mech.percentage_gdp else "N/A"
        print(f"   {i:2d}. {mech.source_type:30s} Rate: {rate_str:6s} GDP: {gdp_str:6s}")
    
    # Convert to scenario dict
    print("\n4. Generating scenario JSON...")
    scenario = mechanics_to_scenario_dict(mechanics, policy_name, args.policy_type)
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Wrote scenario to {output_path}")
    
    # Validation
    print("\n5. Validation:")
    file_size = output_path.stat().st_size
    print(f"   ✓ File size: {file_size:,} bytes")
    
    # Test loading
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        mech_count = len(loaded.get("mechanics", {}).get("funding_mechanisms", []))
        print(f"   ✓ JSON valid: {mech_count} mechanisms")
    except Exception as e:
        print(f"   ❌ JSON validation failed: {e}")
        return 1
    
    print("\n" + "=" * 80)
    print("✓ SUCCESS: Scenario generated successfully!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
