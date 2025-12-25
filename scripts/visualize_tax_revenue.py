"""
Tax Revenue Breakdown Visualization

Creates charts showing tax revenue projections by type (wealth, consumption, carbon, FTT)
with breakdown by year and cumulative totals.

Usage:
    python scripts/visualize_tax_revenue.py --scenario progressive --years 10
    python scripts/visualize_tax_revenue.py --compare baseline progressive moderate
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.phase2_integration import Phase2SimulationEngine, Phase2PolicyPackage, Phase2ReformPackages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_revenue_stacked_area(
    tax_results: pd.DataFrame,
    title: str,
    output_path: Optional[Path] = None,
) -> Figure:
    """
    Create stacked area chart showing tax revenue by type over time.
    
    Args:
        tax_results: DataFrame with tax revenue by type and year
        title: Chart title
        output_path: Path to save chart (optional)
        
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Get years
    years = tax_results['year'].values
    
    # Identify tax columns (exclude 'year')
    tax_columns = [col for col in tax_results.columns if col != 'year']
    
    if not tax_columns:
        logger.warning("No tax revenue columns found")
        ax.text(0.5, 0.5, 'No Tax Reforms', ha='center', va='center', fontsize=16)
        return fig
    
    # Create stacked area
    colors = {
        'wealth_tax': '#1f77b4',
        'consumption_tax': '#ff7f0e',
        'carbon_tax': '#2ca02c',
        'ftt': '#d62728',
    }
    
    revenue_data = []
    labels = []
    plot_colors = []
    
    for col in tax_columns:
        revenue_data.append(tax_results[col].values)
        # Clean up column name for label
        label = col.replace('_', ' ').title().replace('Ftt', 'FTT')
        labels.append(label)
        plot_colors.append(colors.get(col, '#888888'))
    
    ax.stackplot(years, *revenue_data, labels=labels, colors=plot_colors, alpha=0.7)
    
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Annual Revenue (Billions $)', fontsize=12)
    ax.set_title(f'Tax Reform Revenue by Type - {title}', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}B'))
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Revenue area chart saved to {output_path}")
    
    return fig


def create_cumulative_revenue_chart(
    tax_results: pd.DataFrame,
    title: str,
    output_path: Optional[Path] = None,
) -> Figure:
    """
    Create line chart showing cumulative revenue over time.
    
    Args:
        tax_results: DataFrame with tax revenue by type and year
        title: Chart title
        output_path: Path to save chart (optional)
        
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    years = tax_results['year'].values
    tax_columns = [col for col in tax_results.columns if col != 'year']
    
    if not tax_columns:
        ax.text(0.5, 0.5, 'No Tax Reforms', ha='center', va='center', fontsize=16)
        return fig
    
    colors = {
        'wealth_tax': '#1f77b4',
        'consumption_tax': '#ff7f0e',
        'carbon_tax': '#2ca02c',
        'ftt': '#d62728',
    }
    
    # Calculate cumulative sums
    for col in tax_columns:
        cumsum = tax_results[col].cumsum()
        label = col.replace('_', ' ').title().replace('Ftt', 'FTT')
        color = colors.get(col, '#888888')
        ax.plot(years, cumsum, linewidth=2.5, label=label, color=color)
    
    # Total line
    total_annual = tax_results[tax_columns].sum(axis=1)
    total_cumsum = total_annual.cumsum()
    ax.plot(years, total_cumsum, 'k--', linewidth=3, label='Total', alpha=0.8)
    
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Cumulative Revenue (Billions $)', fontsize=12)
    ax.set_title(f'Cumulative Tax Revenue - {title}', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}B'))
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Cumulative revenue chart saved to {output_path}")
    
    return fig


def create_revenue_pie_chart(
    tax_results: pd.DataFrame,
    title: str,
    output_path: Optional[Path] = None,
) -> Figure:
    """
    Create pie chart showing total revenue breakdown by tax type.
    
    Args:
        tax_results: DataFrame with tax revenue by type and year
        title: Chart title
        output_path: Path to save chart (optional)
        
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    tax_columns = [col for col in tax_results.columns if col != 'year']
    
    if not tax_columns:
        ax.text(0.5, 0.5, 'No Tax Reforms', ha='center', va='center', fontsize=16)
        return fig
    
    # Calculate totals
    totals = {col: tax_results[col].sum() for col in tax_columns}
    
    # Filter out zero revenues
    totals = {k: v for k, v in totals.items() if v > 0}
    
    if not totals:
        ax.text(0.5, 0.5, 'No Revenue Generated', ha='center', va='center', fontsize=16)
        return fig
    
    colors = {
        'wealth_tax': '#1f77b4',
        'consumption_tax': '#ff7f0e',
        'carbon_tax': '#2ca02c',
        'ftt': '#d62728',
    }
    
    labels = [col.replace('_', ' ').title().replace('Ftt', 'FTT') for col in totals.keys()]
    sizes = list(totals.values())
    pie_colors = [colors.get(col, '#888888') for col in totals.keys()]
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=pie_colors,
        autopct=lambda pct: f'{pct:.1f}%\n(${pct*sum(sizes)/100:,.0f}B)',
        startangle=90,
        textprops={'fontsize': 10}
    )
    
    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title(f'Total Revenue Breakdown - {title}', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Revenue pie chart saved to {output_path}")
    
    return fig


def create_comparison_bar_chart(
    scenarios: Dict[str, pd.DataFrame],
    output_path: Optional[Path] = None,
) -> Figure:
    """
    Create grouped bar chart comparing total revenue across scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to tax results DataFrames
        output_path: Path to save chart (optional)
        
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    scenario_names = list(scenarios.keys())
    tax_types = set()
    
    # Identify all tax types across scenarios
    for df in scenarios.values():
        tax_types.update([col for col in df.columns if col != 'year'])
    
    tax_types = sorted(tax_types)
    
    if not tax_types:
        ax.text(0.5, 0.5, 'No Tax Reforms Found', ha='center', va='center', fontsize=16)
        return fig
    
    # Calculate totals for each scenario and tax type
    data = {tax_type: [] for tax_type in tax_types}
    
    for scenario_name in scenario_names:
        df = scenarios[scenario_name]
        for tax_type in tax_types:
            if tax_type in df.columns:
                total = df[tax_type].sum()
            else:
                total = 0
            data[tax_type].append(total)
    
    # Create grouped bars
    x = np.arange(len(scenario_names))
    width = 0.8 / len(tax_types)
    
    colors = {
        'wealth_tax': '#1f77b4',
        'consumption_tax': '#ff7f0e',
        'carbon_tax': '#2ca02c',
        'ftt': '#d62728',
    }
    
    for i, tax_type in enumerate(tax_types):
        offset = width * i - (width * len(tax_types) / 2) + width / 2
        label = tax_type.replace('_', ' ').title().replace('Ftt', 'FTT')
        color = colors.get(tax_type, '#888888')
        ax.bar(x + offset, data[tax_type], width, label=label, color=color, alpha=0.8)
    
    ax.set_xlabel('Scenario', fontsize=12)
    ax.set_ylabel('Total Revenue (Billions $)', fontsize=12)
    ax.set_title('Tax Revenue Comparison by Scenario', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(scenario_names, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}B'))
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Comparison bar chart saved to {output_path}")
    
    return fig


def run_single_visualization(
    scenario: str,
    years: int,
    output_dir: Path,
):
    """Run simulation and create visualizations for a single scenario."""
    logger.info(f"Visualizing {scenario} scenario: {years} years")
    
    engine = Phase2SimulationEngine(
        base_gdp=27000.0,
        population=335.0,
        start_year=2025,
        seed=42,
    )
    
    scenarios_map = {
        "baseline": ("Baseline", Phase2PolicyPackage()),
        "progressive": ("Progressive Reform", Phase2ReformPackages.comprehensive_progressive_reform()),
        "moderate": ("Moderate Reform", Phase2ReformPackages.moderate_reform()),
        "revenue": ("Revenue-Focused", Phase2ReformPackages.revenue_focused_reform()),
        "climate": ("Climate-Focused", Phase2ReformPackages.climate_focused_reform()),
    }
    
    if scenario not in scenarios_map:
        logger.error(f"Unknown scenario: {scenario}")
        return
    
    name, package = scenarios_map[scenario]
    
    results = engine.simulate_comprehensive_reform(
        policy_package=package,
        years=years,
        gdp_growth_rate=0.025,
        iterations=50,
    )
    
    tax_results = results['tax_reforms']
    
    if tax_results.empty or len([c for c in tax_results.columns if c != 'year']) == 0:
        logger.info(f"{scenario} has no tax reforms - skipping visualization")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create all visualizations
    create_revenue_stacked_area(
        tax_results,
        name,
        output_path=output_dir / f"{scenario}_revenue_area.png",
    )
    
    create_cumulative_revenue_chart(
        tax_results,
        name,
        output_path=output_dir / f"{scenario}_cumulative.png",
    )
    
    create_revenue_pie_chart(
        tax_results,
        name,
        output_path=output_dir / f"{scenario}_pie.png",
    )
    
    logger.info(f"Tax revenue visualizations complete for {scenario}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Visualize tax reform revenue projections"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="progressive",
        choices=["baseline", "progressive", "moderate", "revenue", "climate"],
        help="Policy scenario to visualize",
    )
    parser.add_argument(
        "--compare",
        nargs='+',
        choices=["baseline", "progressive", "moderate", "revenue", "climate"],
        help="Compare multiple scenarios (creates comparison chart)",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="Number of years to project",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/charts/tax_revenue",
        help="Output directory for charts",
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output)
    
    if args.compare:
        # Multi-scenario comparison
        logger.info(f"Comparing scenarios: {args.compare}")
        
        engine = Phase2SimulationEngine(
            base_gdp=27000.0,
            population=335.0,
            start_year=2025,
            seed=42,
        )
        
        scenarios_map = {
            "baseline": ("Baseline", Phase2PolicyPackage()),
            "progressive": ("Progressive", Phase2ReformPackages.comprehensive_progressive_reform()),
            "moderate": ("Moderate", Phase2ReformPackages.moderate_reform()),
            "revenue": ("Revenue-Focused", Phase2ReformPackages.revenue_focused_reform()),
            "climate": ("Climate-Focused", Phase2ReformPackages.climate_focused_reform()),
        }
        
        scenario_results = {}
        for scenario_key in args.compare:
            name, package = scenarios_map[scenario_key]
            results = engine.simulate_comprehensive_reform(
                policy_package=package,
                years=args.years,
                gdp_growth_rate=0.025,
                iterations=50,
            )
            scenario_results[name] = results['tax_reforms']
        
        output_dir.mkdir(parents=True, exist_ok=True)
        create_comparison_bar_chart(
            scenario_results,
            output_path=output_dir / "comparison.png",
        )
    else:
        # Single scenario
        run_single_visualization(
            scenario=args.scenario,
            years=args.years,
            output_dir=output_dir,
        )
    
    logger.info("Tax revenue visualization complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
