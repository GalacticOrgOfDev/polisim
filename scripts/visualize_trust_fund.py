"""
Trust Fund Trajectory Visualization

Creates interactive charts showing Social Security trust fund projections
with uncertainty bands from Monte Carlo simulation.

Usage:
    python scripts/visualize_trust_fund.py --input results.csv --output charts/
    python scripts/visualize_trust_fund.py --scenario baseline --years 30
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.phase2_integration import Phase2SimulationEngine, Phase2PolicyPackage, Phase2ReformPackages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_trust_fund_chart(
    results: pd.DataFrame,
    title: str,
    output_path: Optional[Path] = None,
    show_uncertainty: bool = True,
) -> Figure:
    """
    Create trust fund trajectory chart with uncertainty bands.
    
    Args:
        results: DataFrame from Phase2SimulationEngine with trust fund projections
        title: Chart title
        output_path: Path to save chart (optional)
        show_uncertainty: Whether to show confidence intervals
        
    Returns:
        matplotlib Figure object
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Check if we have aggregated results (MultiIndex columns)
    has_stats = isinstance(results.columns, pd.MultiIndex)
    
    # OASI Trust Fund
    if has_stats:
        years = results['year']
        oasi_mean = results[('oasi_balance_billions', 'mean')]
        oasi_std = results[('oasi_balance_billions', 'std')]
        
        # Plot mean line
        ax1.plot(years, oasi_mean, 'b-', linewidth=2, label='Mean Projection')
        
        if show_uncertainty:
            # 90% confidence interval (±1.65 std dev)
            oasi_upper = oasi_mean + 1.65 * oasi_std
            oasi_lower = oasi_mean - 1.65 * oasi_std
            ax1.fill_between(years, oasi_lower, oasi_upper, alpha=0.3, color='blue', label='90% Confidence')
            
            # 50% confidence interval (±0.67 std dev)
            oasi_upper_50 = oasi_mean + 0.67 * oasi_std
            oasi_lower_50 = oasi_mean - 0.67 * oasi_std
            ax1.fill_between(years, oasi_lower_50, oasi_upper_50, alpha=0.5, color='blue', label='50% Confidence')
    else:
        # Simple line plot without uncertainty
        ax1.plot(results['year'], results['oasi_balance_billions'], 'b-', linewidth=2)
    
    ax1.axhline(y=0, color='r', linestyle='--', linewidth=1, label='Depletion')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Balance (Billions $)', fontsize=12)
    ax1.set_title(f'OASI Trust Fund - {title}', fontsize=14, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # DI Trust Fund
    if has_stats:
        di_mean = results[('di_balance_billions', 'mean')]
        di_std = results[('di_balance_billions', 'std')]
        
        ax2.plot(years, di_mean, 'g-', linewidth=2, label='Mean Projection')
        
        if show_uncertainty:
            di_upper = di_mean + 1.65 * di_std
            di_lower = di_mean - 1.65 * di_std
            ax2.fill_between(years, di_lower, di_upper, alpha=0.3, color='green', label='90% Confidence')
            
            di_upper_50 = di_mean + 0.67 * di_std
            di_lower_50 = di_mean - 0.67 * di_std
            ax2.fill_between(years, di_lower_50, di_upper_50, alpha=0.5, color='green', label='50% Confidence')
    else:
        ax2.plot(results['year'], results['di_balance_billions'], 'g-', linewidth=2)
    
    ax2.axhline(y=0, color='r', linestyle='--', linewidth=1, label='Depletion')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Balance (Billions $)', fontsize=12)
    ax2.set_title(f'DI Trust Fund - {title}', fontsize=14, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Chart saved to {output_path}")
    
    return fig


def create_combined_trust_fund_chart(
    results: pd.DataFrame,
    title: str,
    output_path: Optional[Path] = None,
) -> Figure:
    """
    Create combined OASDI trust fund chart.
    
    Args:
        results: DataFrame with trust fund projections
        title: Chart title
        output_path: Path to save chart (optional)
        
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    has_stats = isinstance(results.columns, pd.MultiIndex)
    
    if has_stats:
        years = results['year']
        oasi_mean = results[('oasi_balance_billions', 'mean')]
        di_mean = results[('di_balance_billions', 'mean')]
        combined_mean = oasi_mean + di_mean
        
        oasi_std = results[('oasi_balance_billions', 'std')]
        di_std = results[('di_balance_billions', 'std')]
        # Assume independence for combined std dev
        combined_std = np.sqrt(oasi_std**2 + di_std**2)
        
        # Plot individual funds
        ax.plot(years, oasi_mean, 'b-', linewidth=2, label='OASI', alpha=0.7)
        ax.plot(years, di_mean, 'g-', linewidth=2, label='DI', alpha=0.7)
        ax.plot(years, combined_mean, 'k-', linewidth=3, label='Combined OASDI')
        
        # Combined uncertainty
        combined_upper = combined_mean + 1.65 * combined_std
        combined_lower = combined_mean - 1.65 * combined_std
        ax.fill_between(years, combined_lower, combined_upper, alpha=0.2, color='gray', label='90% Confidence')
    else:
        years = results['year']
        oasi = results['oasi_balance_billions']
        di = results['di_balance_billions']
        combined = oasi + di
        
        ax.plot(years, oasi, 'b-', linewidth=2, label='OASI', alpha=0.7)
        ax.plot(years, di, 'g-', linewidth=2, label='DI', alpha=0.7)
        ax.plot(years, combined, 'k-', linewidth=3, label='Combined OASDI')
    
    ax.axhline(y=0, color='r', linestyle='--', linewidth=1, label='Depletion')
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Balance (Billions $)', fontsize=12)
    ax.set_title(f'Combined OASDI Trust Fund - {title}', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Combined chart saved to {output_path}")
    
    return fig


def create_depletion_probability_chart(
    scenarios: Dict[str, pd.DataFrame],
    output_path: Optional[Path] = None,
) -> Figure:
    """
    Create bar chart showing depletion probabilities across scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to projection DataFrames
        output_path: Path to save chart (optional)
        
    Returns:
        matplotlib Figure object
    """
    from core.social_security import SocialSecurityModel
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scenario_names = []
    oasi_probs = []
    di_probs = []
    
    model = SocialSecurityModel()
    
    for name, results in scenarios.items():
        scenario_names.append(name)
        
        # Calculate depletion probability
        solvency = model.estimate_solvency_dates(results)
        
        oasi_prob = solvency.get('OASI', {}).get('probability_depleted', 0.0)
        di_prob = solvency.get('DI', {}).get('probability_depleted', 0.0)
        
        oasi_probs.append(oasi_prob * 100)  # Convert to percentage
        di_probs.append(di_prob * 100)
    
    x = np.arange(len(scenario_names))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, oasi_probs, width, label='OASI', color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, di_probs, width, label='DI', color='green', alpha=0.7)
    
    ax.set_xlabel('Scenario', fontsize=12)
    ax.set_ylabel('Depletion Probability (%)', fontsize=12)
    ax.set_title('Trust Fund Depletion Probability by Scenario', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(scenario_names, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Depletion probability chart saved to {output_path}")
    
    return fig


def run_visualization(
    scenario: str,
    years: int,
    iterations: int,
    output_dir: Path,
):
    """
    Run simulation and create visualizations.
    
    Args:
        scenario: Scenario name
        years: Projection years
        iterations: Monte Carlo iterations
        output_dir: Output directory for charts
    """
    logger.info(f"Running {scenario} scenario: {years} years, {iterations} iterations")
    
    # Initialize engine
    engine = Phase2SimulationEngine(
        base_gdp=27000.0,
        population=335.0,
        start_year=2025,
        seed=42,
    )
    
    # Select policy package
    scenarios_map = {
        "baseline": ("Baseline (Current Law)", Phase2PolicyPackage()),
        "progressive": ("Progressive Reform", Phase2ReformPackages.comprehensive_progressive_reform()),
        "moderate": ("Moderate Reform", Phase2ReformPackages.moderate_reform()),
        "revenue": ("Revenue-Focused Reform", Phase2ReformPackages.revenue_focused_reform()),
        "climate": ("Climate-Focused Reform", Phase2ReformPackages.climate_focused_reform()),
    }
    
    if scenario not in scenarios_map:
        logger.error(f"Unknown scenario: {scenario}")
        logger.info(f"Available scenarios: {list(scenarios_map.keys())}")
        return
    
    name, package = scenarios_map[scenario]
    
    # Run simulation
    results = engine.simulate_comprehensive_reform(
        policy_package=package,
        years=years,
        gdp_growth_rate=0.025,
        iterations=iterations,
    )
    
    ss_results = results['social_security']
    
    # Create visualizations
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Separate OASI and DI charts
    create_trust_fund_chart(
        ss_results,
        name,
        output_path=output_dir / f"{scenario}_trust_funds.png",
        show_uncertainty=True,
    )
    
    # Combined chart
    create_combined_trust_fund_chart(
        ss_results,
        name,
        output_path=output_dir / f"{scenario}_combined.png",
    )
    
    logger.info(f"Visualizations complete for {scenario}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Visualize Social Security trust fund projections"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="baseline",
        choices=["baseline", "progressive", "moderate", "revenue", "climate"],
        help="Policy scenario to visualize",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=30,
        help="Number of years to project",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Monte Carlo iterations",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/charts/trust_fund",
        help="Output directory for charts",
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    
    run_visualization(
        scenario=args.scenario,
        years=args.years,
        iterations=args.iterations,
        output_dir=output_dir,
    )
    
    logger.info("Trust fund visualization complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
