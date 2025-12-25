"""
Phase 2 Validation Script

This script demonstrates the Phase 2 validation framework by:
1. Running baseline simulations
2. Comparing against CBO and SSA authoritative baselines
3. Generating a comprehensive validation report
4. Rating model accuracy

Usage:
    python scripts/run_phase2_validation.py
    python scripts/run_phase2_validation.py --iterations 1000
    python scripts/run_phase2_validation.py --output reports/validation_report.txt
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase2_validation import run_comprehensive_validation
from core.phase2_integration import Phase2SimulationEngine, Phase2PolicyPackage


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Phase 2 validation against CBO and SSA baselines"
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of Monte Carlo iterations (default: 100)",
    )
    
    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="Number of years to project (default: 10)",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for validation report (default: console only)",
    )
    
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.10,
        help="Error tolerance for validation (default: 0.10 = 10%%)",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    return parser.parse_args()


def run_baseline_simulation(
    iterations: int = 100,
    years: int = 10,
) -> dict:
    """
    Run baseline simulation with no reforms.
    
    Args:
        iterations: Number of Monte Carlo iterations
        years: Number of years to project
        
    Returns:
        Dictionary with simulation results
    """
    print(f"\n{'='*60}")
    print("RUNNING BASELINE SIMULATION")
    print(f"{'='*60}")
    print(f"Monte Carlo iterations: {iterations}")
    print(f"Projection years: {years}")
    
    # Create baseline policy package (no reforms)
    baseline = Phase2PolicyPackage.baseline()
    
    # Initialize simulation engine
    engine = Phase2SimulationEngine(
        start_year=2024,
        projection_years=years,
        iterations=iterations,
    )
    
    # Run simulation
    print("\nSimulating Social Security...")
    ss_results = engine.simulate_social_security_reforms(baseline)
    
    print("Simulating tax reforms...")
    tax_results = engine.simulate_tax_reforms(baseline)
    
    print("Integrating revenue projections...")
    revenue_results = engine.simulate_revenue_scenarios(baseline)
    
    print("Combining fiscal outlook...")
    combined_results = engine.combine_fiscal_outlook(
        ss_results, tax_results, revenue_results
    )
    
    print("\n✅ Baseline simulation complete")
    
    return {
        'social_security': ss_results,
        'tax_reform': tax_results,
        'revenue': revenue_results,
        'combined': combined_results,
    }


def main():
    """Main execution function."""
    args = parse_arguments()
    
    print(f"\n{'='*60}")
    print("PHASE 2 VALIDATION FRAMEWORK")
    print(f"{'='*60}")
    print(f"Project: polisim")
    print(f"Version: Phase 2A")
    print(f"Date: 2025-12-24")
    print(f"{'='*60}\n")
    
    try:
        # Run baseline simulation
        results = run_baseline_simulation(
            iterations=args.iterations,
            years=args.years,
        )
        
        # Run comprehensive validation
        print(f"\n{'='*60}")
        print("VALIDATING AGAINST AUTHORITATIVE BASELINES")
        print(f"{'='*60}")
        print("Comparing against:")
        print("  - CBO 2024 Budget Outlook")
        print("  - SSA 2024 Trustees Report")
        print(f"Error tolerance: {args.tolerance*100:.1f}%\n")
        
        validation_results = run_comprehensive_validation(
            social_security_projections=results['social_security'],
            revenue_projections=results['revenue'],
            tolerance=args.tolerance,
        )
        
        # Generate validation report
        print(f"\n{'='*60}")
        print("VALIDATION REPORT")
        print(f"{'='*60}\n")
        
        report = validation_results['report']
        print(report)
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"\n✅ Report saved to: {output_path}")
        
        # Print summary
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        
        ss_validation = validation_results['social_security']
        revenue_validation = validation_results['revenue']
        baseline_validation = validation_results['baseline_consistency']
        
        print(f"\nSocial Security Validation:")
        print(f"  Total metrics: {ss_validation['total_metrics']}")
        print(f"  Within tolerance: {ss_validation['within_tolerance']}")
        print(f"  Accuracy: {ss_validation['within_tolerance']/ss_validation['total_metrics']*100:.1f}%")
        
        print(f"\nRevenue Validation:")
        print(f"  Total metrics: {revenue_validation['total_metrics']}")
        print(f"  Within tolerance: {revenue_validation['within_tolerance']}")
        print(f"  Accuracy: {revenue_validation['within_tolerance']/revenue_validation['total_metrics']*100:.1f}%")
        
        print(f"\nBaseline Consistency:")
        print(f"  GDP growth consistent: {baseline_validation['gdp_growth_consistent']}")
        print(f"  Revenue ratios consistent: {baseline_validation['revenue_ratios_consistent']}")
        print(f"  Debt trajectory consistent: {baseline_validation['debt_trajectory_consistent']}")
        
        # Determine overall rating
        total_metrics = (
            ss_validation['total_metrics'] + revenue_validation['total_metrics']
        )
        within_tolerance = (
            ss_validation['within_tolerance'] + revenue_validation['within_tolerance']
        )
        
        accuracy_rate = within_tolerance / total_metrics if total_metrics > 0 else 0
        
        if accuracy_rate >= 0.98:
            rating = "EXCELLENT"
            emoji = "🌟"
        elif accuracy_rate >= 0.95:
            rating = "GOOD"
            emoji = "✅"
        elif accuracy_rate >= 0.90:
            rating = "ACCEPTABLE"
            emoji = "👍"
        else:
            rating = "NEEDS IMPROVEMENT"
            emoji = "⚠️"
        
        print(f"\n{'='*60}")
        print(f"OVERALL RATING: {rating} {emoji}")
        print(f"{'='*60}")
        print(f"Model accuracy: {accuracy_rate*100:.1f}%")
        print(f"Metrics validated: {within_tolerance}/{total_metrics}")
        
        # Exit with appropriate code
        if accuracy_rate >= 0.90:
            print("\n✅ Validation PASSED - Model meets accuracy standards")
            return 0
        else:
            print("\n⚠️ Validation FAILED - Model needs improvement")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
