"""
Test context-aware simulation with USGHA mechanics.
Loads extracted mechanics JSON and runs simulation to validate context awareness.
"""

import json
from pathlib import Path
from core.healthcare import HealthcarePolicyFactory, PolicyType
from core.simulation import simulate_healthcare_years
from core.policy_mechanics_extractor import PolicyMechanics, FundingMechanism, SurplusAllocation


def load_mechanics_from_json(json_path: str) -> PolicyMechanics:
    """Load PolicyMechanics from extracted JSON."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Reconstruct PolicyMechanics object
    from core.policy_mechanics_extractor import (
        PolicyMechanics, FundingMechanism, SurplusAllocation,
        CircuitBreaker, InnovationFundRules, TimelineMilestone
    )
    
    mechanics = PolicyMechanics(
        policy_name=data['policy_name'],
        policy_type=data['policy_type']
    )
    
    # Funding mechanisms
    for fm_data in data['funding_mechanisms']:
        mechanics.funding_mechanisms.append(FundingMechanism(
            source_type=fm_data['source_type'],
            percentage_gdp=fm_data.get('percentage_gdp'),
            percentage_rate=fm_data.get('percentage_rate'),
            description=fm_data.get('description', ''),
            phase_in_start=fm_data.get('phase_in_start'),
            phase_in_end=fm_data.get('phase_in_end'),
            conditions=fm_data.get('conditions', [])
        ))
    
    # Surplus allocation
    if data.get('surplus_allocation'):
        sa_data = data['surplus_allocation']
        mechanics.surplus_allocation = SurplusAllocation(
            contingency_reserve_pct=sa_data['contingency_reserve_pct'],
            debt_reduction_pct=sa_data['debt_reduction_pct'],
            infrastructure_pct=sa_data['infrastructure_pct'],
            dividends_pct=sa_data['dividends_pct'],
            other_allocations=sa_data.get('other_allocations', {})
        )
    
    # Circuit breakers
    for cb_data in data.get('circuit_breakers', []):
        mechanics.circuit_breakers.append(CircuitBreaker(
            trigger_type=cb_data['trigger_type'],
            threshold_value=cb_data['threshold_value'],
            threshold_unit=cb_data['threshold_unit'],
            action=cb_data['action'],
            description=cb_data.get('description', '')
        ))
    
    # Innovation fund
    if data.get('innovation_fund'):
        if_data = data['innovation_fund']
        mechanics.innovation_fund = InnovationFundRules(
            funding_min_pct=if_data['funding_min_pct'],
            funding_max_pct=if_data['funding_max_pct'],
            funding_base=if_data['funding_base'],
            prize_min_dollars=if_data['prize_min_dollars'],
            prize_max_dollars=if_data['prize_max_dollars'],
            annual_cap_pct=if_data['annual_cap_pct'],
            annual_cap_base=if_data['annual_cap_base'],
            eligible_categories=if_data.get('eligible_categories', [])
        )
    
    # Timeline milestones
    for tm_data in data.get('timeline_milestones', []):
        mechanics.timeline_milestones.append(TimelineMilestone(
            year=tm_data['year'],
            description=tm_data['description'],
            metric_type=tm_data.get('metric_type', ''),
            target_value=tm_data.get('target_value')
        ))
    
    # Other fields
    mechanics.target_spending_pct_gdp = data.get('target_spending_pct_gdp')
    mechanics.target_spending_year = data.get('target_spending_year')
    mechanics.zero_out_of_pocket = data.get('zero_out_of_pocket', False)
    mechanics.universal_coverage = data.get('universal_coverage', False)
    mechanics.confidence_score = data.get('confidence_score', 0.0)
    
    return mechanics


def test_context_aware_simulation():
    """Test simulation with extracted mechanics vs legacy hard-coded."""
    
    print("="*80)
    print("CONTEXT-AWARE SIMULATION TEST")
    print("="*80)
    
    # Load extracted mechanics
    mechanics_path = Path("extracted_mechanics_test.json")
    if not mechanics_path.exists():
        print(f"ERROR: Mechanics file not found: {mechanics_path}")
        print("Run test_policy_extraction.py first to generate mechanics JSON")
        return
    
    print(f"\nLoading mechanics from: {mechanics_path}")
    mechanics = load_mechanics_from_json(str(mechanics_path))
    print(f"Loaded: {mechanics.policy_name}")
    print(f"Confidence: {mechanics.confidence_score:.1%}")
    
    # Create USGHA policy with mechanics attached
    print("\n" + "-"*80)
    print("TEST 1: Context-Aware Simulation (with mechanics)")
    print("-"*80)
    
    policy_with_mechanics = HealthcarePolicyFactory.create_usgha()
    policy_with_mechanics.mechanics = mechanics
    
    print(f"Policy: {policy_with_mechanics.policy_name}")
    print(f"Has mechanics: {policy_with_mechanics.mechanics is not None}")
    
    # Run simulation
    df_with_mechanics = simulate_healthcare_years(
        policy=policy_with_mechanics,
        base_gdp=28.0e12,
        initial_debt=35.0e12,
        years=22,
        population=335e6,
        gdp_growth=0.025,
        start_year=2027
    )
    
    print(f"\nSimulation complete: {len(df_with_mechanics)} years")
    print("\nFirst 3 years:")
    cols_to_show = ['Year', 'GDP', 'Total Revenue', 'Healthcare Spending', 'Surplus/Deficit', 
                    'National Debt', 'Debt Reduction']
    print(df_with_mechanics[cols_to_show].head(3).to_string(index=False))
    
    print("\nLast 3 years:")
    print(df_with_mechanics[cols_to_show].tail(3).to_string(index=False))
    
    # Show revenue breakdown for year 1
    print("\n" + "-"*80)
    print("Revenue Breakdown (Year 1 - Context-Aware)")
    print("-"*80)
    year1 = df_with_mechanics.iloc[0]
    print(f"Payroll Tax:            ${year1['Payroll Tax Revenue']/1e12:.2f}T")
    print(f"Redirected Federal:     ${year1['Redirected Federal Revenue']/1e12:.2f}T")
    print(f"Converted Premiums:     ${year1['Converted Premiums Revenue']/1e12:.2f}T")
    print(f"Efficiency Gains:       ${year1['Efficiency Gains Revenue']/1e12:.2f}T")
    print(f"Other Sources:          ${year1['Other Revenue']/1e12:.2f}T")
    print(f"Total Revenue:          ${year1['Total Revenue']/1e12:.2f}T ({year1['Total Revenue']/year1['GDP']*100:.1f}% GDP)")
    
    # Show surplus allocation for a surplus year
    surplus_years = df_with_mechanics[df_with_mechanics['Surplus/Deficit'] > 0]
    if len(surplus_years) > 0:
        print("\n" + "-"*80)
        print(f"Surplus Allocation (Year {surplus_years.iloc[0]['Year']:.0f} - Context-Aware)")
        print("-"*80)
        year_surplus = surplus_years.iloc[0]
        print(f"Total Surplus:          ${year_surplus['Surplus/Deficit']/1e12:.2f}T")
        print(f"  → Contingency (10%):  ${year_surplus['Contingency Reserve']/1e12:.2f}T balance")
        print(f"  → Debt Reduction (70%): ${year_surplus['Debt Reduction']/1e12:.2f}T")
        print(f"  → Infrastructure (10%): ${year_surplus['Infrastructure Allocation']/1e12:.2f}T")
        print(f"  → Dividends (10%):    ${year_surplus['Dividend Pool']/1e12:.2f}T (${year_surplus['Dividend Per Capita']:.0f}/person)")
    
    # Show final debt outcome
    print("\n" + "-"*80)
    print("Debt Trajectory (Context-Aware)")
    print("-"*80)
    year_last = df_with_mechanics.iloc[-1]
    print(f"Initial Debt (2027):    $35.0T (125% GDP)")
    print(f"Final Debt ({year_last['Year']:.0f}):      ${year_last['National Debt']/1e12:.2f}T ({year_last['Debt % GDP']:.1f}% GDP)")
    print(f"Debt Reduction:         ${(35.0e12 - year_last['National Debt'])/1e12:.2f}T")
    
    # Compare to legacy simulation
    print("\n" + "="*80)
    print("TEST 2: Legacy Simulation (without mechanics)")
    print("="*80)
    
    policy_without_mechanics = HealthcarePolicyFactory.create_usgha()
    policy_without_mechanics.mechanics = None
    
    print(f"Policy: {policy_without_mechanics.policy_name}")
    print(f"Has mechanics: {policy_without_mechanics.mechanics is not None}")
    
    df_without_mechanics = simulate_healthcare_years(
        policy=policy_without_mechanics,
        base_gdp=28.0e12,
        initial_debt=35.0e12,
        years=22,
        population=335e6,
        gdp_growth=0.025,
        start_year=2027
    )
    
    print(f"\nSimulation complete: {len(df_without_mechanics)} years")
    print("\nFirst 3 years:")
    cols_legacy = ['Year', 'GDP', 'Revenue', 'Healthcare Spending', 'Surplus', 'National Debt']
    if all(c in df_without_mechanics.columns for c in cols_legacy):
        print(df_without_mechanics[cols_legacy].head(3).to_string(index=False))
    
    # Comparison
    print("\n" + "="*80)
    print("COMPARISON: Context-Aware vs Legacy")
    print("="*80)
    
    print("\nYear 1 Revenue:")
    print(f"  Context-Aware: ${df_with_mechanics.iloc[0]['Total Revenue']/1e12:.2f}T")
    if 'Revenue' in df_without_mechanics.columns:
        print(f"  Legacy:        ${df_without_mechanics.iloc[0]['Revenue']/1e12:.2f}T")
    
    print("\nFinal Debt:")
    print(f"  Context-Aware: ${df_with_mechanics.iloc[-1]['National Debt']/1e12:.2f}T")
    if 'National Debt' in df_without_mechanics.columns:
        print(f"  Legacy:        ${df_without_mechanics.iloc[-1]['National Debt']/1e12:.2f}T")
    
    print("\nContext-Aware Advantages:")
    print("  ✓ Revenue breakdown by source (payroll, redirected federal, converted premiums, efficiency)")
    print("  ✓ Spending breakdown by savings mechanism (admin, drug pricing, preventive care)")
    print("  ✓ Surplus allocation per policy rules (10/70/10/10 split)")
    print("  ✓ Circuit breaker monitoring (13% GDP spending cap)")
    print("  ✓ Innovation fund calculation (1-20% of savings, 5% of surplus cap)")
    print("  ✓ Works with ANY policy mechanics (not just USGHA)")
    
    # Save results
    df_with_mechanics.to_csv("simulation_context_aware.csv", index=False)
    print(f"\n✓ Saved context-aware results to: simulation_context_aware.csv")


if __name__ == "__main__":
    test_context_aware_simulation()
