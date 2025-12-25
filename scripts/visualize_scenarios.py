"""
Multi-Scenario Comparison Dashboard

Creates a comprehensive dashboard comparing multiple policy scenarios across
trust fund trajectories, tax revenues, and fiscal outcomes.

Usage:
    python scripts/visualize_scenarios.py --scenarios baseline progressive moderate
    python scripts/visualize_scenarios.py --all --years 20 --iterations 100
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.figure import Figure
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.phase2_integration import Phase2SimulationEngine, Phase2PolicyPackage, Phase2ReformPackages
from core.social_security import SocialSecurityModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_scenarios(
    scenario_keys: List[str],
    years: int,
    iterations: int,
) -> Dict[str, Dict[str, any]]:
    """
    Run multiple scenarios and collect results.
    
    Args:
        scenario_keys: List of scenario keys to run
        years: Projection years
        iterations: Monte Carlo iterations
        
    Returns:
        Dictionary mapping scenario names to results
    """
    engine = Phase2SimulationEngine(
        base_gdp=27000.0,
        population=335.0,
        start_year=2025,
        seed=42,
    )
    
    scenarios_map = {
        "baseline": ("Baseline (Current Law)", Phase2PolicyPackage()),
        "progressive": ("Progressive Reform", Phase2ReformPackages.comprehensive_progressive_reform()),
        "moderate": ("Moderate Reform", Phase2ReformPackages.moderate_reform()),
        "revenue": ("Revenue-Focused Reform", Phase2ReformPackages.revenue_focused_reform()),
        "climate": ("Climate-Focused Reform", Phase2ReformPackages.climate_focused_reform()),
    }
    
    results = {}
    
    for key in scenario_keys:
        if key not in scenarios_map:
            logger.warning(f"Unknown scenario: {key}, skipping")
            continue
        
        name, package = scenarios_map[key]
        logger.info(f"Running scenario: {name}")
        
        sim_results = engine.simulate_comprehensive_reform(
            policy_package=package,
            years=years,
            gdp_growth_rate=0.025,
            iterations=iterations,
        )
        
        results[name] = {
            'social_security': sim_results['social_security'],
            'tax_reforms': sim_results['tax_reforms'],
            'key': key,
        }
    
    return results


def create_dashboard(
    results: Dict[str, Dict],
    output_path: Path,
    years: int,
):
    """
    Create comprehensive multi-scenario dashboard.
    
    Args:
        results: Dictionary of scenario results
        output_path: Path to save dashboard
        years: Number of projection years
    """
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Top row: Trust fund trajectories
    ax_oasi = fig.add_subplot(gs[0, 0])
    ax_di = fig.add_subplot(gs[0, 1])
    ax_combined = fig.add_subplot(gs[0, 2])
    
    # Middle row: Tax revenues and solvency
    ax_tax_total = fig.add_subplot(gs[1, 0])
    ax_tax_breakdown = fig.add_subplot(gs[1, 1])
    ax_solvency = fig.add_subplot(gs[1, 2])
    
    # Bottom row: Fiscal metrics
    ax_net_impact = fig.add_subplot(gs[2, 0])
    ax_depletion = fig.add_subplot(gs[2, 1])
    ax_summary = fig.add_subplot(gs[2, 2])
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
    
    # 1. OASI Trust Fund Trajectories
    for (name, data), color in zip(results.items(), colors):
        ss_df = data['social_security']
        has_stats = isinstance(ss_df.columns, pd.MultiIndex)
        
        if has_stats:
            years_data = ss_df['year']
            oasi_mean = ss_df[('oasi_balance_billions', 'mean')]
            ax_oasi.plot(years_data, oasi_mean, label=name, color=color, linewidth=2)
        else:
            ax_oasi.plot(ss_df['year'], ss_df['oasi_balance_billions'], label=name, color=color, linewidth=2)
    
    ax_oasi.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax_oasi.set_title('OASI Trust Fund Balance', fontweight='bold')
    ax_oasi.set_xlabel('Year')
    ax_oasi.set_ylabel('Balance ($B)')
    ax_oasi.legend(loc='best', fontsize=8)
    ax_oasi.grid(True, alpha=0.3)
    
    # 2. DI Trust Fund Trajectories
    for (name, data), color in zip(results.items(), colors):
        ss_df = data['social_security']
        has_stats = isinstance(ss_df.columns, pd.MultiIndex)
        
        if has_stats:
            years_data = ss_df['year']
            di_mean = ss_df[('di_balance_billions', 'mean')]
            ax_di.plot(years_data, di_mean, label=name, color=color, linewidth=2)
        else:
            ax_di.plot(ss_df['year'], ss_df['di_balance_billions'], label=name, color=color, linewidth=2)
    
    ax_di.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax_di.set_title('DI Trust Fund Balance', fontweight='bold')
    ax_di.set_xlabel('Year')
    ax_di.set_ylabel('Balance ($B)')
    ax_di.legend(loc='best', fontsize=8)
    ax_di.grid(True, alpha=0.3)
    
    # 3. Combined OASDI
    for (name, data), color in zip(results.items(), colors):
        ss_df = data['social_security']
        has_stats = isinstance(ss_df.columns, pd.MultiIndex)
        
        if has_stats:
            years_data = ss_df['year']
            oasi_mean = ss_df[('oasi_balance_billions', 'mean')]
            di_mean = ss_df[('di_balance_billions', 'mean')]
            combined = oasi_mean + di_mean
        else:
            years_data = ss_df['year']
            combined = ss_df['oasi_balance_billions'] + ss_df['di_balance_billions']
        
        ax_combined.plot(years_data, combined, label=name, color=color, linewidth=2)
    
    ax_combined.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax_combined.set_title('Combined OASDI Balance', fontweight='bold')
    ax_combined.set_xlabel('Year')
    ax_combined.set_ylabel('Balance ($B)')
    ax_combined.legend(loc='best', fontsize=8)
    ax_combined.grid(True, alpha=0.3)
    
    # 4. Total Tax Revenue (Cumulative)
    for (name, data), color in zip(results.items(), colors):
        tax_df = data['tax_reforms']
        if not tax_df.empty:
            tax_cols = [c for c in tax_df.columns if c != 'year']
            if tax_cols:
                total_annual = tax_df[tax_cols].sum(axis=1)
                cumulative = total_annual.cumsum()
                ax_tax_total.plot(tax_df['year'], cumulative, label=name, color=color, linewidth=2)
    
    ax_tax_total.set_title('Cumulative Tax Revenue', fontweight='bold')
    ax_tax_total.set_xlabel('Year')
    ax_tax_total.set_ylabel('Revenue ($B)')
    ax_tax_total.legend(loc='best', fontsize=8)
    ax_tax_total.grid(True, alpha=0.3)
    
    # 5. Tax Revenue Breakdown (Bar chart for final totals)
    scenario_names = []
    tax_totals = []
    
    for name, data in results.items():
        tax_df = data['tax_reforms']
        if not tax_df.empty:
            tax_cols = [c for c in tax_df.columns if c != 'year']
            if tax_cols:
                total = tax_df[tax_cols].sum().sum()
                scenario_names.append(name)
                tax_totals.append(total)
    
    if scenario_names:
        bars = ax_tax_breakdown.bar(range(len(scenario_names)), tax_totals, color=colors[:len(scenario_names)])
        ax_tax_breakdown.set_xticks(range(len(scenario_names)))
        ax_tax_breakdown.set_xticklabels(scenario_names, rotation=45, ha='right', fontsize=8)
        ax_tax_breakdown.set_title(f'Total Tax Revenue ({years}yr)', fontweight='bold')
        ax_tax_breakdown.set_ylabel('Revenue ($B)')
        ax_tax_breakdown.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax_tax_breakdown.text(bar.get_x() + bar.get_width()/2., height,
                                    f'${height:,.0f}B', ha='center', va='bottom', fontsize=8)
    
    # 6. Solvency Probability
    model = SocialSecurityModel()
    scenario_names_solv = []
    oasi_probs = []
    di_probs = []
    
    for name, data in results.items():
        ss_df = data['social_security']
        solvency = model.estimate_solvency_dates(ss_df)
        
        scenario_names_solv.append(name)
        oasi_probs.append(solvency.get('OASI', {}).get('probability_depleted', 0.0) * 100)
        di_probs.append(solvency.get('DI', {}).get('probability_depleted', 0.0) * 100)
    
    x = np.arange(len(scenario_names_solv))
    width = 0.35
    
    ax_solvency.bar(x - width/2, oasi_probs, width, label='OASI', alpha=0.7)
    ax_solvency.bar(x + width/2, di_probs, width, label='DI', alpha=0.7)
    ax_solvency.set_xticks(x)
    ax_solvency.set_xticklabels(scenario_names_solv, rotation=45, ha='right', fontsize=8)
    ax_solvency.set_title('Depletion Probability', fontweight='bold')
    ax_solvency.set_ylabel('Probability (%)')
    ax_solvency.legend()
    ax_solvency.grid(True, alpha=0.3, axis='y')
    
    # 7. Net Fiscal Impact (Trust fund change + Tax revenue)
    scenario_names_net = []
    net_impacts = []
    
    for name, data in results.items():
        ss_df = data['social_security']
        has_stats = isinstance(ss_df.columns, pd.MultiIndex)
        
        # SS change
        if has_stats:
            first_oasi = ss_df[('oasi_balance_billions', 'mean')].iloc[0]
            last_oasi = ss_df[('oasi_balance_billions', 'mean')].iloc[-1]
            first_di = ss_df[('di_balance_billions', 'mean')].iloc[0]
            last_di = ss_df[('di_balance_billions', 'mean')].iloc[-1]
        else:
            first_oasi = ss_df['oasi_balance_billions'].iloc[0]
            last_oasi = ss_df['oasi_balance_billions'].iloc[-1]
            first_di = ss_df['di_balance_billions'].iloc[0]
            last_di = ss_df['di_balance_billions'].iloc[-1]
        
        ss_change = (last_oasi - first_oasi) + (last_di - first_di)
        
        # Tax revenue
        tax_df = data['tax_reforms']
        if not tax_df.empty:
            tax_cols = [c for c in tax_df.columns if c != 'year']
            tax_total = tax_df[tax_cols].sum().sum() if tax_cols else 0
        else:
            tax_total = 0
        
        net_impact = ss_change + tax_total
        scenario_names_net.append(name)
        net_impacts.append(net_impact)
    
    bars = ax_net_impact.bar(range(len(scenario_names_net)), net_impacts, 
                            color=['red' if x < 0 else 'green' for x in net_impacts],
                            alpha=0.7)
    ax_net_impact.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax_net_impact.set_xticks(range(len(scenario_names_net)))
    ax_net_impact.set_xticklabels(scenario_names_net, rotation=45, ha='right', fontsize=8)
    ax_net_impact.set_title(f'Net Fiscal Impact ({years}yr)', fontweight='bold')
    ax_net_impact.set_ylabel('Impact ($B)')
    ax_net_impact.grid(True, alpha=0.3, axis='y')
    
    # 8. Depletion Years
    scenario_names_depl = []
    oasi_depl_years = []
    
    for name, data in results.items():
        ss_df = data['social_security']
        solvency = model.estimate_solvency_dates(ss_df)
        
        scenario_names_depl.append(name)
        oasi_year = solvency.get('OASI', {}).get('depletion_year_median')
        oasi_depl_years.append(oasi_year if oasi_year else years + 2025 + 10)  # Beyond projection if no depletion
    
    bars = ax_depletion.barh(range(len(scenario_names_depl)), oasi_depl_years, alpha=0.7)
    ax_depletion.set_yticks(range(len(scenario_names_depl)))
    ax_depletion.set_yticklabels(scenario_names_depl, fontsize=8)
    ax_depletion.set_title('OASI Depletion Year (Median)', fontweight='bold')
    ax_depletion.set_xlabel('Year')
    ax_depletion.axvline(x=2025, color='gray', linestyle='--', alpha=0.5, label='Start')
    ax_depletion.axvline(x=2025+years, color='red', linestyle='--', alpha=0.5, label='Projection End')
    ax_depletion.legend(fontsize=8)
    ax_depletion.grid(True, alpha=0.3, axis='x')
    
    # 9. Summary Table
    ax_summary.axis('off')
    
    table_data = []
    headers = ['Scenario', f'OASI Balance\n(Year {2025+years})', f'Tax Revenue\n({years}yr)', 'Depletion\nProbability']
    
    for name, data in results.items():
        ss_df = data['social_security']
        has_stats = isinstance(ss_df.columns, pd.MultiIndex)
        
        if has_stats:
            final_oasi = ss_df[('oasi_balance_billions', 'mean')].iloc[-1]
        else:
            final_oasi = ss_df['oasi_balance_billions'].iloc[-1]
        
        tax_df = data['tax_reforms']
        if not tax_df.empty:
            tax_cols = [c for c in tax_df.columns if c != 'year']
            tax_total = tax_df[tax_cols].sum().sum() if tax_cols else 0
        else:
            tax_total = 0
        
        solvency = model.estimate_solvency_dates(ss_df)
        depl_prob = solvency.get('OASI', {}).get('probability_depleted', 0.0)
        
        table_data.append([
            name,
            f'${final_oasi:,.0f}B',
            f'${tax_total:,.0f}B',
            f'{depl_prob*100:.0f}%'
        ])
    
    table = ax_summary.table(cellText=table_data, colLabels=headers,
                            cellLoc='center', loc='center',
                            colWidths=[0.35, 0.25, 0.20, 0.20])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style header
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax_summary.set_title('Summary Metrics', fontweight='bold', pad=20)
    
    # Overall title
    fig.suptitle(f'Policy Scenario Comparison Dashboard ({years}-Year Projection)', 
                fontsize=16, fontweight='bold', y=0.98)
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Dashboard saved to {output_path}")
    
    return fig


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Create multi-scenario comparison dashboard"
    )
    parser.add_argument(
        "--scenarios",
        nargs='+',
        choices=["baseline", "progressive", "moderate", "revenue", "climate"],
        help="Scenarios to compare",
    )
    parser.add_argument(
        "--all",
        action='store_true',
        help="Compare all available scenarios",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=10,
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
        default="reports/charts/dashboard.png",
        help="Output path for dashboard",
    )
    
    args = parser.parse_args()
    
    if args.all:
        scenario_keys = ["baseline", "progressive", "moderate", "revenue", "climate"]
    elif args.scenarios:
        scenario_keys = args.scenarios
    else:
        scenario_keys = ["baseline", "progressive", "moderate"]
    
    logger.info(f"Creating dashboard for scenarios: {scenario_keys}")
    
    # Run scenarios
    results = run_scenarios(scenario_keys, args.years, args.iterations)
    
    # Create dashboard
    output_path = Path(args.output)
    create_dashboard(results, output_path, args.years)
    
    logger.info("Dashboard creation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
