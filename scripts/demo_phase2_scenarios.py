"""
Phase 2 Policy Scenario Demonstration

This script demonstrates the full capabilities of Phase 2A by running multiple
policy scenarios and comparing their fiscal impacts over 10 years.

Scenarios demonstrated:
1. Baseline (current law)
2. Comprehensive Progressive Reform
3. Moderate Reform Package
4. Revenue-Focused Reform
5. Climate-Focused Reform

Each scenario shows:
- Social Security trust fund trajectory
- Tax reform revenue impacts
- Combined fiscal outlook
- Depletion dates and solvency metrics

Usage:
    python scripts/demo_phase2_scenarios.py
    python scripts/demo_phase2_scenarios.py --years 20 --iterations 500
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase2_integration import (
    Phase2SimulationEngine,
    Phase2PolicyPackage,
    Phase2ReformPackages,
)
from core.social_security import SocialSecurityModel


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Demonstrate Phase 2 policy scenarios"
    )
    
    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="Number of years to project (default: 10)",
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of Monte Carlo iterations (default: 100)",
    )
    
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["baseline", "progressive", "moderate", "revenue", "climate"],
        help="Scenarios to run (default: all)",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file for results (optional)",
    )
    
    return parser.parse_args()


def format_currency(value: float) -> str:
    """Format value as currency in billions."""
    return f"${value:,.1f}B"


def format_year(value: float) -> str:
    """Format year value."""
    if value is None:
        return "Never"
    return f"{value:.1f}"


def print_scenario_header(name: str):
    """Print formatted scenario header."""
    print(f"\n{'='*70}")
    print(f"  SCENARIO: {name}")
    print(f"{'='*70}")


def summarize_social_security(results: pd.DataFrame, name: str):
    """Summarize Social Security projection results."""
    print(f"\n[Social Security] Trust Fund Projection ({name})")
    print("-" * 70)
    
    # Get first and last year data
    first_year = results[results['year'] == results['year'].min()]
    last_year = results[results['year'] == results['year'].max()]
    
    # Extract mean values (handling MultiIndex columns)
    if isinstance(results.columns, pd.MultiIndex):
        first_oasi = first_year[('oasi_balance_billions', 'mean')].values[0]
        last_oasi = last_year[('oasi_balance_billions', 'mean')].values[0]
    else:
        first_oasi = first_year['oasi_balance_billions'].mean()
        last_oasi = last_year['oasi_balance_billions'].mean()
    
    print(f"  Starting OASI Balance: {format_currency(first_oasi)}")
    print(f"  Ending OASI Balance:   {format_currency(last_oasi)}")
    print(f"  Change:                {format_currency(last_oasi - first_oasi)}")
    
    # Calculate depletion if it occurs
    if last_oasi <= 0:
        print(f"  Status:                [!] DEPLETED")
    elif last_oasi < first_oasi * 0.5:
        print(f"  Status:                [!] DECLINING RAPIDLY")
    elif last_oasi < first_oasi:
        print(f"  Status:                [-] DECLINING")
    else:
        print(f"  Status:                [OK] STABLE/GROWING")


def summarize_tax_reform(results: Dict[str, Any], name: str):
    """Summarize tax reform revenue results."""
    print(f"\n[Tax Reform] Revenue ({name})")
    print("-" * 70)
    
    if not results:
        print("  No tax reforms in this scenario")
        return
    
    total_revenue = 0
    for tax_type, data in results.items():
        if 'total_revenue_10yr' in data:
            revenue = data['total_revenue_10yr']
            total_revenue += revenue
            print(f"  {tax_type.replace('_', ' ').title()}: {format_currency(revenue)}")
    
    if total_revenue > 0:
        print(f"  {'-'*66}")
        print(f"  Total Tax Reform Revenue: {format_currency(total_revenue)}")


def run_scenario(
    name: str,
    package: Phase2PolicyPackage,
    engine: Phase2SimulationEngine,
    years: int,
    iterations: int,
) -> Dict[str, Any]:
    """Run a single policy scenario."""
    print_scenario_header(name)
    
    print(f"\nRunning simulation...")
    print(f"  Years: {years}")
    print(f"  Iterations: {iterations}")
    
    # Run comprehensive simulation
    results = engine.simulate_comprehensive_reform(
        policy_package=package,
        years=years,
        gdp_growth_rate=0.025,  # 2.5% annual GDP growth
        iterations=iterations,
    )
    
    # Extract results
    ss_results = results['social_security']
    tax_results_df = results['tax_reforms']
    
    # Summarize Social Security results
    summarize_social_security(ss_results, name)
    
    # Process tax reform results
    if isinstance(tax_results_df, pd.DataFrame) and not tax_results_df.empty:
        # Calculate 10-year totals by tax type
        tax_summary = {}
        for col in tax_results_df.columns:
            if col != 'year':
                total_10yr = tax_results_df[col].sum()
                if total_10yr > 0:
                    tax_summary[col] = {'total_revenue_10yr': total_10yr}
        summarize_tax_reform(tax_summary, name)
    else:
        tax_summary = {}
        summarize_tax_reform(tax_summary, name)
    
    # Calculate solvency
    print(f"\nSolvency Analysis")
    print("-" * 70)
    
    # Analyze trust fund trajectory
    first_year_data = ss_results[ss_results['year'] == ss_results['year'].min()]
    last_year_data = ss_results[ss_results['year'] == ss_results['year'].max()]
    
    if isinstance(ss_results.columns, pd.MultiIndex):
        first_balance = first_year_data[('oasi_balance_billions', 'mean')].values[0]
        last_balance = last_year_data[('oasi_balance_billions', 'mean')].values[0]
    else:
        first_balance = first_year_data['oasi_balance_billions'].mean()
        last_balance = last_year_data['oasi_balance_billions'].mean()
    
    if last_balance <= 0:
        print(f"  [!] OASI depletes within projection period")
    else:
        decline_rate = (first_balance - last_balance) / first_balance if first_balance > 0 else 0
        years_to_depletion = years / decline_rate if decline_rate > 0 else float('inf')
        if years_to_depletion < 30:
            print(f"  [!] OASI projected to deplete in ~{years_to_depletion:.0f} years")
        else:
            print(f"  [OK] OASI remains solvent (>30 years)")
    
    print(f"  Status:         [OK] Simulation complete")
    
    return {
        "name": name,
        "social_security": ss_results,
        "tax_reform": tax_summary,
    }


def compare_scenarios(results: Dict[str, Dict[str, Any]]):
    """Compare multiple scenarios side by side."""
    print(f"\n{'='*70}")
    print("  SCENARIO COMPARISON")
    print(f"{'='*70}")
    
    print(f"\n[Comparison] Trust Fund Balance (End of Period)")
    print("-" * 70)
    
    for name, data in results.items():
        ss_results = data["social_security"]
        last_year = ss_results[ss_results['year'] == ss_results['year'].max()]
        
        if isinstance(ss_results.columns, pd.MultiIndex):
            balance = last_year[('oasi_balance_billions', 'mean')].values[0]
        else:
            balance = last_year['oasi_balance_billions'].mean()
        
        status = "[OK]" if balance > 0 else "[!]"
        print(f"  {status} {name:30s}: {format_currency(balance)}")
    
    print(f"\n[Comparison] Tax Reform Revenue (10-Year Total)")
    print("-" * 70)
    
    for name, data in results.items():
        tax_results = data["tax_reform"]
        total = sum(
            data.get('total_revenue_10yr', 0) 
            for data in tax_results.values()
        )
        if total > 0:
            print(f"  [+] {name:30s}: {format_currency(total)}")
        else:
            print(f"  [-] {name:30s}: No tax reforms")


def main():
    """Main execution function."""
    args = parse_arguments()
    
    print(f"\n{'='*70}")
    print("  PHASE 2 POLICY SCENARIO DEMONSTRATION")
    print(f"{'='*70}")
    print(f"  Project: polisim")
    print(f"  Version: Phase 2A Complete")
    print(f"  Date: 2025-12-24")
    print(f"{'='*70}\n")
    
    # Initialize simulation engine
    engine = Phase2SimulationEngine(
        base_gdp=27000.0,  # 2025 US GDP in billions
        population=335.0,  # US population in millions
        start_year=2025,
        seed=42,  # For reproducibility
    )
    
    # Define scenarios to run
    scenarios = {
        "baseline": ("Baseline (Current Law)", Phase2PolicyPackage()),
        "progressive": ("Comprehensive Progressive Reform", Phase2ReformPackages.comprehensive_progressive_reform()),
        "moderate": ("Moderate Reform Package", Phase2ReformPackages.moderate_reform()),
        "revenue": ("Revenue-Focused Reform", Phase2ReformPackages.revenue_focused_reform()),
        "climate": ("Climate-Focused Reform", Phase2ReformPackages.climate_focused_reform()),
    }
    
    # Filter to requested scenarios
    scenarios_to_run = {
        k: v for k, v in scenarios.items() 
        if k in args.scenarios
    }
    
    if not scenarios_to_run:
        print("[!] No valid scenarios selected!")
        print(f"Available scenarios: {list(scenarios.keys())}")
        return 1
    
    # Run all scenarios
    results = {}
    for key, (name, package) in scenarios_to_run.items():
        try:
            results[name] = run_scenario(name, package, engine, args.years, args.iterations)
        except Exception as e:
            print(f"\n[!] Error running {name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Compare scenarios
    if len(results) > 1:
        compare_scenarios(results)
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create summary DataFrame
        summary_data = []
        for name, data in results.items():
            ss_results = data["social_security"]
            last_year = ss_results[ss_results['year'] == ss_results['year'].max()]
            
            if isinstance(ss_results.columns, pd.MultiIndex):
                balance = last_year[('oasi_balance_billions', 'mean')].values[0]
            else:
                balance = last_year['oasi_balance_billions'].mean()
            
            tax_revenue = sum(
                data.get('total_revenue_10yr', 0) 
                for data in data["tax_reform"].values()
            )
            
            summary_data.append({
                "Scenario": name,
                "Final_OASI_Balance_Billions": balance,
                "Tax_Reform_Revenue_10yr_Billions": tax_revenue,
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(output_path, index=False)
        print(f"\n[Saved] Results saved to: {output_path}")
    
    # Final summary
    print(f"\n{'='*70}")
    print("  DEMONSTRATION COMPLETE")
    print(f"{'='*70}")
    print(f"  Scenarios run: {len(results)}")
    print(f"  Projection period: {args.years} years")
    print(f"  Monte Carlo iterations: {args.iterations}")
    print(f"\n[OK] All Phase 2A capabilities demonstrated successfully!")
    print(f"{'='*70}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
