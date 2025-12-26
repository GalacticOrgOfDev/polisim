#!/usr/bin/env python3
"""
Phase 3 Unified Budget Projection Demo

Demonstrates the CombinedFiscalOutlookModel with:
- Unified federal budget projections (revenues, spending, debt, interest)
- Multi-scenario comparisons
- Monte Carlo uncertainty analysis
- Healthcare integration (Medicare/Medicaid)
- Social Security projections
- Economic feedback loops

Usage:
    python scripts/demo_phase3_unified.py --years 30 --iterations 1000
    python scripts/demo_phase3_unified.py --scenarios baseline progressive --output results.csv
    python scripts/demo_phase3_unified.py --quick  # Fast demo mode
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.combined_outlook import CombinedFiscalOutlookModel
from core.config import Config
from core.validation import ValidationError


def print_section(title: str, width: int = 80):
    """Print formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def format_currency(value: float, decimals: int = 2) -> str:
    """Format value as currency in trillions."""
    if abs(value) >= 1e12:
        return f"${value / 1e12:,.{decimals}f}T"
    elif abs(value) >= 1e9:
        return f"${value / 1e9:,.{decimals}f}B"
    else:
        return f"${value / 1e6:,.{decimals}f}M"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage."""
    return f"{value * 100:,.{decimals}f}%"


def run_baseline_projection(years: int = 30, iterations: int = 1000, verbose: bool = True):
    """Run baseline (current law) projection."""
    if verbose:
        print_section(f"Baseline Projection ({years} years, {iterations:,} iterations)")
    
    model = CombinedFiscalOutlookModel()
    
    try:
        results = model.project_unified_budget(
            years=years,
            iterations=iterations,
            scenario_name="baseline"
        )
        
        if verbose:
            print_results_summary(results, "Baseline (Current Law)")
        
        return results
    
    except ValidationError as e:
        print(f"❌ Validation Error: {e}")
        print("   Check input parameters and try again.")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None


def run_policy_projection(
    scenario_name: str,
    years: int = 30,
    iterations: int = 1000,
    verbose: bool = True
) -> Optional[Dict]:
    """Run projection for a specific policy scenario."""
    if verbose:
        print_section(f"{scenario_name.title()} Scenario ({years} years)")
    
    model = CombinedFiscalOutlookModel()
    
    try:
        results = model.project_unified_budget(
            years=years,
            iterations=iterations,
            scenario_name=scenario_name
        )
        
        if verbose:
            print_results_summary(results, scenario_name.title())
        
        return results
    
    except ValidationError as e:
        print(f"❌ Validation Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error running {scenario_name}: {e}")
        return None


def print_results_summary(results: Dict, scenario_name: str):
    """Print formatted summary of projection results."""
    print(f"📊 {scenario_name} - Summary Results\n")
    
    # Extract key metrics
    final_year = results['years'][-1]
    
    # Revenues
    initial_revenue = results['total_revenues'][0]
    final_revenue = results['total_revenues'][-1]
    revenue_growth = (final_revenue - initial_revenue) / initial_revenue
    
    # Spending
    initial_spending = results['total_spending'][0]
    final_spending = results['total_spending'][-1]
    spending_growth = (final_spending - initial_spending) / initial_spending
    
    # Debt
    initial_debt = results['debt'][0]
    final_debt = results['debt'][-1]
    debt_increase = final_debt - initial_debt
    
    # Deficit/Surplus
    initial_deficit = results['deficits'][0]
    final_deficit = results['deficits'][-1]
    
    # GDP metrics
    initial_gdp = results['gdp'][0]
    final_gdp = results['gdp'][-1]
    initial_debt_gdp = (initial_debt / initial_gdp) * 100
    final_debt_gdp = (final_debt / final_gdp) * 100
    
    print("┌─ Fiscal Summary ─────────────────────────────────────────────┐")
    print(f"│ Year Range:      {results['years'][0]} → {final_year}")
    print(f"│ Projection Type: {results.get('projection_type', 'deterministic')}")
    print("├──────────────────────────────────────────────────────────────┤")
    print(f"│ 💰 Revenues:     {format_currency(initial_revenue)} → {format_currency(final_revenue)}")
    print(f"│    Growth:       {format_percentage(revenue_growth)}")
    print("├──────────────────────────────────────────────────────────────┤")
    print(f"│ 💸 Spending:     {format_currency(initial_spending)} → {format_currency(final_spending)}")
    print(f"│    Growth:       {format_percentage(spending_growth)}")
    print("├──────────────────────────────────────────────────────────────┤")
    print(f"│ 📉 Deficit:      {format_currency(abs(initial_deficit))} → {format_currency(abs(final_deficit))}")
    print(f"│    Trend:        {'Improving' if final_deficit > initial_deficit else 'Worsening'}")
    print("├──────────────────────────────────────────────────────────────┤")
    print(f"│ 🏦 Debt:         {format_currency(initial_debt)} → {format_currency(final_debt)}")
    print(f"│    Change:       +{format_currency(debt_increase)}")
    print(f"│    % of GDP:     {initial_debt_gdp:.1f}% → {final_debt_gdp:.1f}%")
    print("└──────────────────────────────────────────────────────────────┘")
    
    # Check for concerning trends
    warnings = []
    if final_debt_gdp > 150:
        warnings.append(f"⚠️  High debt-to-GDP ratio: {final_debt_gdp:.1f}%")
    if final_deficit < -2e12:  # >$2T deficit
        warnings.append(f"⚠️  Large deficit: {format_currency(abs(final_deficit))}")
    if spending_growth > 0.5:  # >50% growth
        warnings.append(f"⚠️  Rapid spending growth: {format_percentage(spending_growth)}")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   {warning}")
    
    print()


def compare_scenarios(
    scenario_results: Dict[str, Dict],
    years: int = 30
) -> pd.DataFrame:
    """Compare multiple scenarios side-by-side."""
    print_section(f"Scenario Comparison (Year {years})")
    
    comparison_data = []
    
    for scenario_name, results in scenario_results.items():
        if results is None:
            continue
        
        final_idx = -1  # Last year
        
        comparison_data.append({
            'Scenario': scenario_name.title(),
            'Final Debt ($T)': results['debt'][final_idx] / 1e12,
            'Final Debt/GDP (%)': (results['debt'][final_idx] / results['gdp'][final_idx]) * 100,
            'Final Deficit ($T)': results['deficits'][final_idx] / 1e12,
            'Total Revenue ($T)': results['total_revenues'][final_idx] / 1e12,
            'Total Spending ($T)': results['total_spending'][final_idx] / 1e12,
            'Interest Cost ($T)': results['interest_spending'][final_idx] / 1e12,
        })
    
    df = pd.DataFrame(comparison_data)
    
    # Format for display
    print(df.to_string(index=False))
    print()
    
    # Calculate differences from baseline
    if 'Baseline' in df['Scenario'].values:
        print("📊 Differences from Baseline:")
        print("─" * 60)
        
        baseline_row = df[df['Scenario'] == 'Baseline'].iloc[0]
        
        for _, row in df.iterrows():
            if row['Scenario'] == 'Baseline':
                continue
            
            debt_diff = row['Final Debt ($T)'] - baseline_row['Final Debt ($T)']
            deficit_diff = row['Final Deficit ($T)'] - baseline_row['Final Deficit ($T)']
            
            print(f"\n{row['Scenario']}:")
            print(f"  Debt:    {debt_diff:+.2f}T ({debt_diff / baseline_row['Final Debt ($T)'] * 100:+.1f}%)")
            print(f"  Deficit: {deficit_diff:+.2f}T ({deficit_diff / abs(baseline_row['Final Deficit ($T)']) * 100:+.1f}%)")
    
    print()
    return df


def export_to_csv(scenario_results: Dict[str, Dict], output_path: str):
    """Export all scenario results to CSV."""
    print(f"\n💾 Exporting results to {output_path}...")
    
    all_data = []
    
    for scenario_name, results in scenario_results.items():
        if results is None:
            continue
        
        for i, year in enumerate(results['years']):
            all_data.append({
                'scenario': scenario_name,
                'year': year,
                'gdp': results['gdp'][i],
                'total_revenue': results['total_revenues'][i],
                'total_spending': results['total_spending'][i],
                'deficit': results['deficits'][i],
                'debt': results['debt'][i],
                'debt_to_gdp_pct': (results['debt'][i] / results['gdp'][i]) * 100,
                'interest_spending': results['interest_spending'][i],
                'medicare_spending': results.get('medicare_spending', [0] * len(results['years']))[i],
                'medicaid_spending': results.get('medicaid_spending', [0] * len(results['years']))[i],
                'social_security_spending': results.get('social_security_spending', [0] * len(results['years']))[i],
            })
    
    df = pd.DataFrame(all_data)
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(all_data)} rows to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3 Unified Budget Projection Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick demo (10 years, 100 iterations)
  python scripts/demo_phase3_unified.py --quick
  
  # Full projection (30 years, 1000 iterations)
  python scripts/demo_phase3_unified.py --years 30 --iterations 1000
  
  # Compare specific scenarios
  python scripts/demo_phase3_unified.py --scenarios baseline progressive --years 20
  
  # Export to CSV
  python scripts/demo_phase3_unified.py --scenarios baseline progressive --output phase3_results.csv
        """
    )
    
    parser.add_argument('--years', type=int, default=30, help='Years to project (default: 30)')
    parser.add_argument('--iterations', type=int, default=1000, help='Monte Carlo iterations (default: 1000)')
    parser.add_argument('--scenarios', nargs='+', default=['baseline'], 
                       help='Scenarios to run: baseline, progressive, etc.')
    parser.add_argument('--output', type=str, help='CSV output file path')
    parser.add_argument('--quick', action='store_true', help='Quick mode: 10 years, 100 iterations')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    
    args = parser.parse_args()
    
    # Quick mode overrides
    if args.quick:
        args.years = 10
        args.iterations = 100
        print("🚀 Quick Mode: 10 years, 100 iterations\n")
    
    verbose = not args.quiet
    
    # Print header
    if verbose:
        print("\n" + "=" * 80)
        print("  POLISIM - Phase 3 Unified Budget Projection Demo")
        print("=" * 80)
        print(f"\n📅 Projection Period: {args.years} years")
        print(f"🎲 Monte Carlo Iterations: {args.iterations:,}")
        print(f"📊 Scenarios: {', '.join(args.scenarios)}")
        if args.output:
            print(f"💾 Output: {args.output}")
    
    # Run projections
    scenario_results = {}
    
    for scenario in args.scenarios:
        if scenario.lower() == 'baseline':
            results = run_baseline_projection(args.years, args.iterations, verbose)
        else:
            results = run_policy_projection(scenario, args.years, args.iterations, verbose)
        
        scenario_results[scenario] = results
    
    # Compare scenarios if multiple
    if len(scenario_results) > 1:
        comparison_df = compare_scenarios(scenario_results, args.years)
    
    # Export if requested
    if args.output:
        export_to_csv(scenario_results, args.output)
    
    # Summary
    if verbose:
        print_section("Demo Complete")
        print("✅ Phase 3 unified budget projection complete!")
        print(f"📊 Analyzed {len(scenario_results)} scenario(s)")
        print(f"📅 Projected {args.years} years into the future")
        print(f"🎲 Used {args.iterations:,} Monte Carlo iterations")
        if args.output:
            print(f"💾 Results saved to {args.output}")
        print()


if __name__ == "__main__":
    main()
