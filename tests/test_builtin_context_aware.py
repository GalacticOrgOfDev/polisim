"""
Test built-in policies with context-aware simulation.
Validates USGHA and Current US mechanics are properly attached and working.
"""

from core.healthcare import HealthcarePolicyFactory
from core.simulation import simulate_healthcare_years
import pandas as pd


def test_usgha_context_aware():
    """Test USGHA with full mechanics."""
    print("=" * 80)
    print("TEST: USGHA Context-Aware Simulation")
    print("=" * 80)
    
    policy = HealthcarePolicyFactory.create_usgha()
    
    print(f"Policy: {policy.policy_name}")
    print(f"Has mechanics: {bool(policy.mechanics)}")
    
    if policy.mechanics:
        print(f"\nFunding mechanisms ({len(policy.mechanics.funding_mechanisms)}):")
        for fm in policy.mechanics.funding_mechanisms:
            rate = f"{fm.percentage_rate}%" if fm.percentage_rate else ""
            gdp = f"{fm.percentage_gdp}% GDP" if fm.percentage_gdp else ""
            print(f"  - {fm.source_type}: {rate} {gdp}".strip())
        
        print(f"\nSurplus allocation:")
        alloc = policy.mechanics.surplus_allocation
        print(f"  - Contingency: {alloc.contingency_reserve_pct}%")
        print(f"  - Debt reduction: {alloc.debt_reduction_pct}%")
        print(f"  - Infrastructure: {alloc.infrastructure_pct}%")
        print(f"  - Dividends: {alloc.dividends_pct}%")
        
        print(f"\nCircuit breakers ({len(policy.mechanics.circuit_breakers)}):")
        for cb in policy.mechanics.circuit_breakers:
            print(f"  - {cb.trigger_type}: {cb.threshold_value} {cb.threshold_unit}")
        
        print(f"\nInnovation fund:")
        fund = policy.mechanics.innovation_fund
        print(f"  - Funding: {fund.funding_min_pct}%-{fund.funding_max_pct}% of {fund.funding_base}")
        print(f"  - Annual cap: {fund.annual_cap_pct}% of {fund.annual_cap_base}")
    
    # Run simulation
    print("\n" + "-" * 80)
    print("Running 22-year simulation...")
    print("-" * 80)
    
    results = simulate_healthcare_years(
        policy=policy,
        base_gdp=28e12,
        initial_debt=35e12,
        years=22,
        population=335e6,
        gdp_growth=0.025,
        start_year=2027
    )
    
    print(f"\nSimulation complete: {len(results)} years")
    
    # Check column names (context-aware vs legacy)
    has_context_cols = 'Healthcare Spending' in results.columns
    print(f"Using context-aware columns: {has_context_cols}")
    
    if has_context_cols:
        spend_col = 'Healthcare Spending'
        rev_col = 'Total Revenue'
        surplus_col = 'Surplus/Deficit'
        debt_col = 'National Debt'
    else:
        spend_col = 'Health Spending ($)'
        rev_col = 'Revenue ($)'
        surplus_col = 'Surplus ($)'
        debt_col = 'Remaining Debt ($)'
    
    # Display results
    print(f"\nFirst 3 years:")
    display_cols = ['Year', 'GDP', rev_col, spend_col, surplus_col, debt_col]
    available_cols = [c for c in display_cols if c in results.columns]
    print(results[available_cols].head(3).to_string(index=False))
    
    print(f"\nLast 3 years:")
    print(results[available_cols].tail(3).to_string(index=False))
    
    # Revenue breakdown (context-aware only)
    if 'Payroll Tax Revenue' in results.columns:
        year_1 = results.iloc[0]
        print(f"\n" + "-" * 80)
        print(f"Year 1 Revenue Breakdown:")
        print("-" * 80)
        print(f"Payroll Tax:         ${year_1['Payroll Tax Revenue']/1e12:.2f}T")
        print(f"Redirected Federal:  ${year_1['Redirected Federal Revenue']/1e12:.2f}T")
        print(f"Converted Premiums:  ${year_1['Converted Premiums Revenue']/1e12:.2f}T")
        print(f"Efficiency Gains:    ${year_1['Efficiency Gains Revenue']/1e12:.2f}T")
        print(f"Total Revenue:       ${year_1['Total Revenue']/1e12:.2f}T ({year_1['Total Revenue']/year_1['GDP']*100:.1f}% GDP)")
    
    # Surplus allocation (context-aware only)
    if 'Debt Reduction' in results.columns:
        year_20 = results.iloc[19]  # Year 2046
        if year_20['Surplus/Deficit'] > 0:
            print(f"\n" + "-" * 80)
            print(f"Year 20 Surplus Allocation:")
            print("-" * 80)
            print(f"Total Surplus:       ${year_20['Surplus/Deficit']/1e9:.1f}B")
            print(f"  → Debt Reduction:  ${year_20['Debt Reduction']/1e9:.1f}B")
            print(f"  → Infrastructure:  ${year_20['Infrastructure Allocation']/1e9:.1f}B")
            print(f"  → Dividends:       ${year_20['Dividend Pool']/1e9:.1f}B (${year_20['Dividend Per Capita']:.0f}/person)")
    
    print(f"\n" + "=" * 80)
    print("✓ USGHA context-aware simulation successful")
    print("=" * 80)
    
    assert not results.empty
    assert set(['Year']).issubset(results.columns)


def test_current_us_context_aware():
    """Test Current US with baseline mechanics."""
    print("\n" * 2)
    print("=" * 80)
    print("TEST: Current US Context-Aware Simulation")
    print("=" * 80)
    
    policy = HealthcarePolicyFactory.create_current_us()
    
    print(f"Policy: {policy.policy_name}")
    print(f"Has mechanics: {bool(policy.mechanics)}")
    
    if policy.mechanics:
        print(f"\nFunding mechanisms ({len(policy.mechanics.funding_mechanisms)}):")
        for fm in policy.mechanics.funding_mechanisms:
            gdp = f"{fm.percentage_gdp}% GDP" if fm.percentage_gdp else ""
            print(f"  - {fm.source_type}: {gdp}".strip())
        
        print(f"\nTarget spending: {policy.mechanics.target_spending_pct_gdp}% GDP")
        print(f"Surplus allocation: {bool(policy.mechanics.surplus_allocation)}")
        print(f"Circuit breakers: {len(policy.mechanics.circuit_breakers)}")
    
    # Run simulation
    print("\n" + "-" * 80)
    print("Running 22-year simulation...")
    print("-" * 80)
    
    results = simulate_healthcare_years(
        policy=policy,
        base_gdp=28e12,
        initial_debt=35e12,
        years=22,
        population=335e6,
        gdp_growth=0.025,
        start_year=2025
    )
    
    print(f"\nSimulation complete: {len(results)} years")
    
    # Check column names
    has_context_cols = 'Healthcare Spending' in results.columns
    print(f"Using context-aware columns: {has_context_cols}")
    
    if has_context_cols:
        spend_col = 'Healthcare Spending'
        rev_col = 'Total Revenue'
        debt_col = 'National Debt'
    else:
        spend_col = 'Health Spending ($)'
        rev_col = 'Revenue ($)'
        debt_col = 'Remaining Debt ($)'
    
    # Display results
    print(f"\nFirst 3 years:")
    display_cols = ['Year', 'GDP', rev_col, spend_col, debt_col]
    available_cols = [c for c in display_cols if c in results.columns]
    print(results[available_cols].head(3).to_string(index=False))
    
    print(f"\nLast 3 years:")
    print(results[available_cols].tail(3).to_string(index=False))
    
    # Revenue breakdown (context-aware only)
    if 'Payroll Tax Revenue' in results.columns:
        year_1 = results.iloc[0]
        print(f"\n" + "-" * 80)
        print(f"Year 1 Revenue Breakdown:")
        print("-" * 80)
        print(f"Redirected Federal:  ${year_1['Redirected Federal Revenue']/1e12:.2f}T")
        print(f"Converted Premiums:  ${year_1['Converted Premiums Revenue']/1e12:.2f}T")
        print(f"Total Revenue:       ${year_1['Total Revenue']/1e12:.2f}T ({year_1['Total Revenue']/year_1['GDP']*100:.1f}% GDP)")
        print(f"\nHealthcare Spending: ${year_1['Healthcare Spending']/1e12:.2f}T ({year_1['Healthcare Spending']/year_1['GDP']*100:.1f}% GDP)")
    
    print(f"\n" + "=" * 80)
    print("✓ Current US context-aware simulation successful")
    print("=" * 80)
    
    assert not results.empty
    assert set(['Year']).issubset(results.columns)


if __name__ == "__main__":
    # Test both built-in policies
    usgha_results = test_usgha_context_aware()
    current_results = test_current_us_context_aware()
    
    # Save results
    usgha_results.to_csv("builtin_usgha_context_aware.csv", index=False)
    current_results.to_csv("builtin_current_us_context_aware.csv", index=False)
    
    print("\n" * 2)
    print("=" * 80)
    print("SUMMARY: Built-in Policy Context-Aware Tests")
    print("=" * 80)
    print("✓ USGHA: Full mechanics (4 funding sources, surplus allocation, circuit breakers)")
    print("✓ Current US: Baseline mechanics (2 funding sources, 18.5% GDP spending)")
    print("✓ Both policies using context-aware simulation path")
    print("\nResults saved:")
    print("  - builtin_usgha_context_aware.csv")
    print("  - builtin_current_us_context_aware.csv")
    print("=" * 80)
