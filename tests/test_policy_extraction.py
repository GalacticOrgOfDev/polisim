"""
Test script for policy mechanics extraction.
Tests the new extractor against USGHA text to validate mechanics extraction.
"""

from pathlib import Path
import json
import sys
import pytest
from core.policy_mechanics_extractor import extract_policy_mechanics, PolicyMechanics


def run_usgha_extraction():
    """Run USGHA extraction and return mechanics, pass rate, and error reason."""
    # Load USGHA PDF
    usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")
    if not usgha_path.exists():
        return None, None, f"USGHA PDF not found at: {usgha_path}"

    # Extract text from PDF
    from core.pdf_policy_parser import PolicyPDFProcessor
    processor = PolicyPDFProcessor()
    usgha_text = processor.extract_text_from_pdf(usgha_path)

    if "[PDF extraction requires" in usgha_text or "[Error extracting PDF" in usgha_text:
        print(f"ERROR: {usgha_text}")
        print("\nAttempting to install PDF library...")
        import subprocess
        subprocess.run(['pip', 'install', 'pdfplumber'], check=True)
        # Try again after install
        usgha_text = processor.extract_text_from_pdf(usgha_path)
        if "[PDF extraction requires" in usgha_text or "[Error extracting PDF" in usgha_text:
            return None, None, f"Extraction failed after install: {usgha_text}"

    print("="*80)
    print("TESTING POLICY MECHANICS EXTRACTION FROM PDF")
    print("="*80)
    print(f"PDF: {usgha_path.name}")
    print(f"Extracted text: {len(usgha_text):,} characters\n")
    
    # Save raw text for debugging
    with open("extracted_pdf_text_debug.txt", 'w', encoding='utf-8') as f:
        f.write(usgha_text)
    print("Saved raw PDF text to: extracted_pdf_text_debug.txt\n")
    
    # Extract mechanics
    print("Extracting policy mechanics...")
    mechanics = extract_policy_mechanics(usgha_text, policy_type="healthcare")
    
    # Display results
    print("\n" + "="*80)
    print("EXTRACTION RESULTS")
    print("="*80)
    
    print(f"\nPolicy Name: {mechanics.policy_name}")
    print(f"Policy Type: {mechanics.policy_type}")
    print(f"Confidence Score: {mechanics.confidence_score:.2%}")
    
    # Funding Mechanisms
    print("\n" + "-"*80)
    print("FUNDING MECHANISMS")
    print("-"*80)
    if mechanics.funding_mechanisms:
        for i, funding in enumerate(mechanics.funding_mechanisms, 1):
            print(f"\n{i}. {funding.source_type.upper()}")
            if funding.percentage_rate:
                print(f"   Rate: {funding.percentage_rate}%")
            if funding.percentage_gdp:
                print(f"   GDP Impact: {funding.percentage_gdp}%")
            print(f"   Description: {funding.description}")
            if funding.phase_in_start and funding.phase_in_end:
                print(f"   Phase-in: {funding.phase_in_start}-{funding.phase_in_end}")
    else:
        print("⚠️  NO FUNDING MECHANISMS EXTRACTED")
    
    # Surplus Allocation
    print("\n" + "-"*80)
    print("SURPLUS ALLOCATION")
    print("-"*80)
    if mechanics.surplus_allocation:
        alloc = mechanics.surplus_allocation
        print(f"Contingency Reserves: {alloc.contingency_reserve_pct}%")
        print(f"Debt Reduction: {alloc.debt_reduction_pct}%")
        print(f"Infrastructure/Education/Research: {alloc.infrastructure_pct}%")
        print(f"Direct Dividends: {alloc.dividends_pct}%")
        total = (alloc.contingency_reserve_pct + alloc.debt_reduction_pct + 
                alloc.infrastructure_pct + alloc.dividends_pct)
        print(f"Total Allocated: {total}%")
        if alloc.other_allocations:
            print("Other Allocations:")
            for dest, pct in alloc.other_allocations.items():
                print(f"  - {dest}: {pct}%")
    else:
        print("⚠️  NO SURPLUS ALLOCATION EXTRACTED")
    
    # Circuit Breakers
    print("\n" + "-"*80)
    print("CIRCUIT BREAKERS / FISCAL SAFEGUARDS")
    print("-"*80)
    if mechanics.circuit_breakers:
        for i, breaker in enumerate(mechanics.circuit_breakers, 1):
            print(f"\n{i}. {breaker.trigger_type.upper()}")
            print(f"   Threshold: {breaker.threshold_value} {breaker.threshold_unit}")
            print(f"   Action: {breaker.action}")
            print(f"   Description: {breaker.description}")
    else:
        print("⚠️  NO CIRCUIT BREAKERS EXTRACTED")
    
    # Innovation Fund
    print("\n" + "-"*80)
    print("INNOVATION FUND RULES")
    print("-"*80)
    if mechanics.innovation_fund:
        fund = mechanics.innovation_fund
        print(f"Funding Range: {fund.funding_min_pct}%-{fund.funding_max_pct}% of {fund.funding_base}")
        print(f"Prize Range: ${fund.prize_min_dollars:,.0f} - ${fund.prize_max_dollars:,.0f}")
        print(f"Annual Cap: {fund.annual_cap_pct}% of {fund.annual_cap_base}")
        if fund.eligible_categories:
            print(f"Eligible Categories: {', '.join(fund.eligible_categories)}")
    else:
        print("⚠️  NO INNOVATION FUND RULES EXTRACTED")
    
    # Timeline Milestones
    print("\n" + "-"*80)
    print("TIMELINE MILESTONES")
    print("-"*80)
    if mechanics.timeline_milestones:
        for milestone in mechanics.timeline_milestones:
            target_str = f" (target: {milestone.target_value})" if milestone.target_value else ""
            print(f"{milestone.year}: {milestone.description}{target_str}")
    else:
        print("⚠️  NO TIMELINE MILESTONES EXTRACTED")
    
    # Spending Target
    print("\n" + "-"*80)
    print("SPENDING TARGET")
    print("-"*80)
    if mechanics.target_spending_pct_gdp:
        print(f"Target: {mechanics.target_spending_pct_gdp}% of GDP")
        if mechanics.target_spending_year:
            print(f"Target Year: {mechanics.target_spending_year}")
    else:
        print("⚠️  NO SPENDING TARGET EXTRACTED")
    
    # Coverage Provisions
    print("\n" + "-"*80)
    print("COVERAGE PROVISIONS")
    print("-"*80)
    print(f"Zero Out-of-Pocket: {'✓ YES' if mechanics.zero_out_of_pocket else '✗ NO'}")
    print(f"Universal Coverage: {'✓ YES' if mechanics.universal_coverage else '✗ NO'}")
    
    # Expected values comparison
    print("\n" + "="*80)
    print("VALIDATION AGAINST EXPECTED USGHA VALUES")
    print("="*80)
    
    validations = []
    
    # Check surplus allocation (should be 10/70/10/10)
    if mechanics.surplus_allocation:
        alloc = mechanics.surplus_allocation
        expected_reserves = 10.0
        expected_debt = 70.0
        expected_infra = 10.0
        expected_div = 10.0
        
        if alloc.contingency_reserve_pct == expected_reserves:
            validations.append(("✓", "Contingency reserves: 10%"))
        else:
            validations.append(("✗", f"Contingency reserves: Expected 10%, got {alloc.contingency_reserve_pct}%"))
        
        if alloc.debt_reduction_pct == expected_debt:
            validations.append(("✓", "Debt reduction: 70%"))
        else:
            validations.append(("✗", f"Debt reduction: Expected 70%, got {alloc.debt_reduction_pct}%"))
        
        if alloc.infrastructure_pct == expected_infra:
            validations.append(("✓", "Infrastructure: 10%"))
        else:
            validations.append(("✗", f"Infrastructure: Expected 10%, got {alloc.infrastructure_pct}%"))
        
        if alloc.dividends_pct == expected_div:
            validations.append(("✓", "Dividends: 10%"))
        else:
            validations.append(("✗", f"Dividends: Expected 10%, got {alloc.dividends_pct}%"))
    else:
        validations.append(("✗", "Surplus allocation: NOT EXTRACTED"))
    
    # Check spending target (should be 7% by 2045)
    if mechanics.target_spending_pct_gdp == 7.0:
        validations.append(("✓", "Spending target: 7% GDP"))
    else:
        validations.append(("✗", f"Spending target: Expected 7%, got {mechanics.target_spending_pct_gdp}%"))
    
    if mechanics.target_spending_year == 2045:
        validations.append(("✓", "Target year: 2045"))
    else:
        validations.append(("✗", f"Target year: Expected 2045, got {mechanics.target_spending_year}"))
    
    # Check circuit breaker (13% GDP cap)
    has_spending_cap = any(
        b.trigger_type == "spending_cap" and b.threshold_value == 13.0
        for b in mechanics.circuit_breakers
    )
    if has_spending_cap:
        validations.append(("✓", "Circuit breaker: 13% GDP spending cap"))
    else:
        validations.append(("✗", "Circuit breaker: 13% GDP spending cap NOT FOUND"))
    
    # Check innovation fund (1-20% of savings, capped at 5% of surpluses)
    if mechanics.innovation_fund:
        fund = mechanics.innovation_fund
        if fund.funding_min_pct == 1.0 and fund.funding_max_pct == 20.0:
            validations.append(("✓", "Innovation fund: 1-20% of savings"))
        else:
            validations.append(("✗", f"Innovation fund: Expected 1-20%, got {fund.funding_min_pct}-{fund.funding_max_pct}%"))
        
        if fund.annual_cap_pct == 5.0:
            validations.append(("✓", "Innovation fund cap: 5% of surpluses"))
        else:
            validations.append(("✗", f"Innovation fund cap: Expected 5%, got {fund.annual_cap_pct}%"))
    else:
        validations.append(("✗", "Innovation fund: NOT EXTRACTED"))
    
    # Check coverage provisions
    if mechanics.zero_out_of_pocket:
        validations.append(("✓", "Zero out-of-pocket coverage"))
    else:
        validations.append(("✗", "Zero out-of-pocket coverage NOT DETECTED"))
    
    if mechanics.universal_coverage:
        validations.append(("✓", "Universal coverage"))
    else:
        validations.append(("✗", "Universal coverage NOT DETECTED"))
    
    # Print validation results
    print()
    for status, message in validations:
        print(f"{status} {message}")
    
    # Summary
    passed = sum(1 for s, _ in validations if s == "✓")
    total = len(validations)
    pass_rate = passed / total if total > 0 else 0
    
    print("\n" + "="*80)
    print(f"VALIDATION SUMMARY: {passed}/{total} checks passed ({pass_rate:.1%})")
    print("="*80)
    
    if pass_rate >= 0.8:
        print("✓ EXTRACTION QUALITY: GOOD")
    elif pass_rate >= 0.5:
        print("⚠️  EXTRACTION QUALITY: NEEDS IMPROVEMENT")
    else:
        print("✗ EXTRACTION QUALITY: POOR - Major issues detected")
    
    return mechanics, pass_rate, None


def test_usgha_extraction():
    """Test extraction against actual USGHA PDF file."""
    mechanics, pass_rate, error_reason = run_usgha_extraction()
    if error_reason:
        pytest.skip(error_reason)
    assert mechanics is not None, "Policy mechanics extraction returned no results"
    assert pass_rate is not None and pass_rate >= 0.8, f"Pass rate {pass_rate:.1%} below threshold"


def save_extraction_as_json(mechanics: PolicyMechanics, output_path: str = "extracted_mechanics_test.json"):
    """Save extracted mechanics as JSON for inspection."""
    
    # Convert dataclass to dict manually (better control than asdict)
    output = {
        "policy_name": mechanics.policy_name,
        "policy_type": mechanics.policy_type,
        "confidence_score": mechanics.confidence_score,
        "funding_mechanisms": [
            {
                "source_type": f.source_type,
                "percentage_gdp": f.percentage_gdp,
                "percentage_rate": f.percentage_rate,
                "description": f.description,
                "phase_in_start": f.phase_in_start,
                "phase_in_end": f.phase_in_end,
                "conditions": f.conditions
            }
            for f in mechanics.funding_mechanisms
        ],
        "surplus_allocation": {
            "contingency_reserve_pct": mechanics.surplus_allocation.contingency_reserve_pct,
            "debt_reduction_pct": mechanics.surplus_allocation.debt_reduction_pct,
            "infrastructure_pct": mechanics.surplus_allocation.infrastructure_pct,
            "dividends_pct": mechanics.surplus_allocation.dividends_pct,
            "other_allocations": mechanics.surplus_allocation.other_allocations
        } if mechanics.surplus_allocation else None,
        "circuit_breakers": [
            {
                "trigger_type": b.trigger_type,
                "threshold_value": b.threshold_value,
                "threshold_unit": b.threshold_unit,
                "action": b.action,
                "description": b.description
            }
            for b in mechanics.circuit_breakers
        ],
        "innovation_fund": {
            "funding_min_pct": mechanics.innovation_fund.funding_min_pct,
            "funding_max_pct": mechanics.innovation_fund.funding_max_pct,
            "funding_base": mechanics.innovation_fund.funding_base,
            "prize_min_dollars": mechanics.innovation_fund.prize_min_dollars,
            "prize_max_dollars": mechanics.innovation_fund.prize_max_dollars,
            "annual_cap_pct": mechanics.innovation_fund.annual_cap_pct,
            "annual_cap_base": mechanics.innovation_fund.annual_cap_base,
            "eligible_categories": mechanics.innovation_fund.eligible_categories
        } if mechanics.innovation_fund else None,
        "timeline_milestones": [
            {
                "year": m.year,
                "description": m.description,
                "metric_type": m.metric_type,
                "target_value": m.target_value
            }
            for m in mechanics.timeline_milestones
        ],
        "target_spending_pct_gdp": mechanics.target_spending_pct_gdp,
        "target_spending_year": mechanics.target_spending_year,
        "zero_out_of_pocket": mechanics.zero_out_of_pocket,
        "universal_coverage": mechanics.universal_coverage
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Extracted mechanics saved to: {output_path}")


if __name__ == "__main__":
    mechanics, _, error_reason = run_usgha_extraction()
    if mechanics is None:
        print(error_reason)
        sys.exit(1)
    save_extraction_as_json(mechanics)

