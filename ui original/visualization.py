"""
Advanced visualization module for polisim.

Provides:
- Multi-scenario overlay charts
- Monte Carlo distribution histograms
- Sensitivity analysis heatmaps
- Cost-saving waterfall charts
- CBO-style budget summaries
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

logger = logging.getLogger(__name__)


class SimulationVisualizer:
    """Visualize simulation results with matplotlib."""
    
    def __init__(self, style: str = "seaborn-v0_8-darkgrid", figsize: Tuple[int, int] = (14, 8)):
        """Initialize visualizer with style and figure size."""
        try:
            plt.style.use(style)
        except:
            logger.warning(f"Style {style} not available, using default")
        self.figsize = figsize
        self.colors = {
            'baseline': '#0066CC',  # Blue
            'policy': '#00AA00',    # Green
            'diff': '#CC0000',      # Red
            'historical': '#999999',  # Gray
        }
    
    def plot_scenario_overlay(
        self,
        scenarios: Dict[str, pd.DataFrame],
        metric: str = 'Debt',
        title: Optional[str] = None,
        output_file: Optional[str] = None,
    ) -> plt.Figure:
        """
        Plot multiple scenarios overlaid on same chart.
        
        Args:
            scenarios: Dict of scenario_name -> DataFrame
            metric: Column name to plot (e.g., 'Debt', 'GDP', 'Spending')
            title: Chart title
            output_file: Optional file path to save
        
        Returns:
            matplotlib Figure
        """
        logger.info(f"Creating overlay chart for {len(scenarios)} scenarios, metric={metric}")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if not title:
            title = f"{metric} Projections: Scenario Comparison"
        
        for scenario_name, df in scenarios.items():
            color = self.colors.get(scenario_name.lower(), None)
            ax.plot(
                df['Year'],
                df[metric],
                marker='o',
                label=scenario_name,
                linewidth=2.5,
                color=color,
            )
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel(f'{metric} ($T)' if metric in ['GDP', 'Debt', 'Revenue', 'Spending'] else metric, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Format y-axis as trillions
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.1f}T'))
        
        if output_file:
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved overlay chart to {output_file}")
        
        return fig
    
    def plot_monte_carlo_distribution(
        self,
        samples: np.ndarray,
        scenario_name: str = "Scenario",
        metric: str = "Debt",
        year: int = -1,
        percentiles: List[int] = [10, 25, 50, 75, 90],
        output_file: Optional[str] = None,
    ) -> plt.Figure:
        """
        Plot histogram of Monte Carlo samples with percentile markers.
        
        Args:
            samples: Array of simulation results (1D)
            scenario_name: Name for plot title
            metric: Metric name
            year: Year for which samples are from
            percentiles: Which percentiles to mark
            output_file: Optional file path to save
        
        Returns:
            matplotlib Figure
        """
        logger.info(f"Creating Monte Carlo distribution for {len(samples)} samples")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Histogram
        counts, bins, patches = ax.hist(
            samples,
            bins=50,
            color=self.colors['baseline'],
            alpha=0.7,
            edgecolor='black',
            linewidth=1.2,
        )
        
        # Mark percentiles with vertical lines
        percentile_colors = {
            10: '#FF0000', 25: '#FF6600', 50: '#000000',
            75: '#FF6600', 90: '#FF0000'
        }
        
        for p in percentiles:
            value = np.percentile(samples, p)
            ax.axvline(
                value,
                color=percentile_colors.get(p, '#000000'),
                linestyle='--' if p != 50 else '-',
                linewidth=2,
                label=f'{p}th: ${value:.2f}T',
                alpha=0.8,
            )
        
        mean = samples.mean()
        ax.axvline(mean, color='green', linestyle=':', linewidth=2.5, label=f'Mean: ${mean:.2f}T')
        
        ax.set_xlabel(f'{metric} Value ($T)', fontsize=12)
        ax.set_ylabel('Frequency (# simulations)', fontsize=12)
        ax.set_title(f'{scenario_name}: {metric} Distribution\n({len(samples)} Monte Carlo iterations)', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add statistics box
        stats_text = f"Mean: ${mean:.2f}T\nStd Dev: ${samples.std():.2f}T\nMin: ${samples.min():.2f}T\nMax: ${samples.max():.2f}T"
        ax.text(
            0.98, 0.97, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
        )
        
        if output_file:
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved distribution chart to {output_file}")
        
        return fig
    
    def plot_sensitivity_heatmap(
        self,
        sensitivity_results: pd.DataFrame,
        output_file: Optional[str] = None,
    ) -> plt.Figure:
        """
        Plot sensitivity analysis as heatmap.
        
        Args:
            sensitivity_results: DataFrame with columns [Parameter, Low, High, Impact]
            output_file: Optional file path to save
        
        Returns:
            matplotlib Figure
        """
        logger.info(f"Creating sensitivity heatmap for {len(sensitivity_results)} parameters")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Sort by impact (largest first)
        df = sensitivity_results.sort_values('Impact', ascending=False, key=abs)
        
        # Create horizontal bar chart (tornado diagram)
        y_pos = np.arange(len(df))
        impacts = df['Impact'].values
        
        colors = ['#CC0000' if x > 0 else '#0066CC' for x in impacts]
        ax.barh(y_pos, impacts, color=colors, alpha=0.7, edgecolor='black')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['Parameter'].values, fontsize=11)
        ax.set_xlabel('Impact on Final Debt ($T)', fontsize=12)
        ax.set_title('Sensitivity Analysis: Tornado Diagram\n(Parameter Impact on Outcomes)', 
                    fontsize=14, fontweight='bold')
        ax.axvline(0, color='black', linewidth=0.8)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (impact, param) in enumerate(zip(impacts, df['Parameter'])):
            ax.text(impact + 0.1 if impact > 0 else impact - 0.1, i, f'${impact:.2f}T',
                   va='center', ha='left' if impact > 0 else 'right', fontsize=10)
        
        if output_file:
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved sensitivity heatmap to {output_file}")
        
        return fig
    
    def plot_cost_waterfall(
        self,
        baseline: float,
        policy: float,
        components: Optional[Dict[str, float]] = None,
        title: str = "Cost Savings Waterfall",
        output_file: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create waterfall chart showing cost reduction from baseline to policy.
        
        Args:
            baseline: Baseline total cost
            policy: Policy total cost
            components: Optional dict of component_name -> cost_change
            title: Chart title
            output_file: Optional file path to save
        
        Returns:
            matplotlib Figure
        """
        logger.info(f"Creating waterfall chart: ${baseline:.2f}T baseline -> ${policy:.2f}T policy")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Build waterfall data
        if components:
            x_labels = ['Baseline'] + list(components.keys()) + ['Policy']
            x_pos = np.arange(len(x_labels))
            
            # Calculate cumulative values
            values = [baseline] + list(components.values()) + [0]  # Last placeholder
            cumulative = [baseline]
            for change in components.values():
                cumulative.append(cumulative[-1] + change)
            values[-1] = cumulative[-1]  # Set final value
            
            # Plot bars
            colors = []
            for i, (label, change) in enumerate(components.items()):
                colors.append('#00AA00' if change < 0 else '#CC0000')  # Green for savings, red for increases
            colors = ['#0066CC'] + colors + ['#00AA00']  # Blue baseline, green policy
            
            for i in range(len(x_pos) - 1):
                if i == 0:
                    ax.bar(i, values[i], color=colors[i], alpha=0.7, edgecolor='black', linewidth=1.5)
                else:
                    # Draw from previous cumulative to new value
                    change = values[i]
                    bottom = cumulative[i-1]
                    ax.bar(i, abs(change), bottom=bottom if change > 0 else bottom + change,
                          color=colors[i], alpha=0.7, edgecolor='black', linewidth=1.5)
            
            # Final policy bar
            ax.bar(len(x_pos) - 1, values[-1], color=colors[-1], alpha=0.7, edgecolor='black', linewidth=1.5)
        else:
            # Simple two-bar comparison
            x_labels = ['Baseline', 'Policy']
            x_pos = [0, 1]
            values = [baseline, policy]
            colors = [self.colors['baseline'], self.colors['policy']]
            
            ax.bar(x_pos, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5, width=0.5)
        
        # Add connecting lines
        if components:
            for i in range(len(cumulative) - 1):
                ax.plot([i + 0.4, i + 0.6], [cumulative[i], cumulative[i]], 'k--', linewidth=1)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels, fontsize=11)
        ax.set_ylabel('Annual Cost ($T)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.1f}T'))
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add savings annotation
        savings = baseline - policy
        pct_savings = (savings / baseline) * 100 if baseline != 0 else 0
        ax.text(
            0.98, 0.97, f'Total Savings: ${savings:.2f}T ({pct_savings:.1f}%)',
            transform=ax.transAxes,
            fontsize=12,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8, edgecolor='darkgreen', linewidth=2),
            fontweight='bold',
        )
        
        if output_file:
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved waterfall chart to {output_file}")
        
        return fig
    
    def plot_percentile_bands(
        self,
        years: np.ndarray,
        percentiles: Dict[str, np.ndarray],
        metric: str = "Debt",
        title: Optional[str] = None,
        output_file: Optional[str] = None,
    ) -> plt.Figure:
        """
        Plot uncertainty bands using percentiles (10th, 25th, 50th, 75th, 90th).
        
        Args:
            years: Array of years
            percentiles: Dict with keys like '10th', '50th', '90th'
            metric: Metric name
            title: Chart title
            output_file: Optional file path to save
        
        Returns:
            matplotlib Figure
        """
        logger.info(f"Creating percentile bands chart for {metric}")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if not title:
            title = f"{metric} Projections with Uncertainty Bands"
        
        # Plot bands
        ax.fill_between(years, percentiles.get('10th', percentiles.get('10', [])), 
                       percentiles.get('90th', percentiles.get('90', [])),
                       alpha=0.2, color='#0066CC', label='80% Range (10th-90th)')
        
        ax.fill_between(years, percentiles.get('25th', percentiles.get('25', [])), 
                       percentiles.get('75th', percentiles.get('75', [])),
                       alpha=0.4, color='#0066CC', label='50% Range (25th-75th)')
        
        # Plot median
        median_key = '50th' if '50th' in percentiles else '50'
        if median_key in percentiles:
            ax.plot(years, percentiles[median_key], color='#000000', linewidth=2.5, 
                   label='Median (50th)', marker='o')
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel(f'{metric} ($T)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.1f}T'))
        
        if output_file:
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved percentile bands chart to {output_file}")
        
        return fig


class CboBudgetSummaryVisualizer:
    """Create CBO-style budget summary visualizations."""
    
    def __init__(self, figsize: Tuple[int, int] = (16, 10)):
        self.figsize = figsize
    
    def plot_budget_summary(
        self,
        revenue_data: Dict[str, float],
        spending_data: Dict[str, float],
        deficit: float,
        debt: float,
        output_file: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create comprehensive CBO-style budget summary with pie charts and metrics.
        
        Args:
            revenue_data: Dict of revenue_source -> amount
            spending_data: Dict of spending_category -> amount
            deficit: Deficit/surplus amount
            debt: Total national debt
            output_file: Optional file path to save
        
        Returns:
            matplotlib Figure
        """
        logger.info("Creating CBO-style budget summary visualization")
        
        fig = plt.figure(figsize=self.figsize)
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Revenue pie chart
        ax1 = fig.add_subplot(gs[0, 0])
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(revenue_data)))
        ax1.pie(revenue_data.values(), labels=revenue_data.keys(), autopct='%1.1f%%',
               colors=colors, startangle=90)
        ax1.set_title('Revenue Sources', fontsize=12, fontweight='bold')
        
        # Spending pie chart
        ax2 = fig.add_subplot(gs[0, 1])
        colors = plt.cm.Reds(np.linspace(0.4, 0.8, len(spending_data)))
        ax2.pie(spending_data.values(), labels=spending_data.keys(), autopct='%1.1f%%',
               colors=colors, startangle=90)
        ax2.set_title('Spending Categories', fontsize=12, fontweight='bold')
        
        # Summary table
        ax3 = fig.add_subplot(gs[1, :])
        ax3.axis('off')
        
        total_revenue = sum(revenue_data.values())
        total_spending = sum(spending_data.values())
        
        summary_data = [
            ['Total Revenue', f'${total_revenue:.2f}T'],
            ['Total Spending', f'${total_spending:.2f}T'],
            ['Deficit / (Surplus)', f'${deficit:.2f}T' if deficit >= 0 else f'(${abs(deficit):.2f}T)'],
            ['National Debt', f'${debt:.2f}T'],
        ]
        
        table = ax3.table(cellText=summary_data, colLabels=['Metric', 'Amount'],
                         cellLoc='center', loc='center', colWidths=[0.3, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2)
        
        # Color header
        for i in range(2):
            table[(0, i)].set_facecolor('#0066CC')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(summary_data) + 1):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#E8E8E8')
        
        fig.suptitle('Federal Budget Summary', fontsize=16, fontweight='bold', y=0.98)
        
        if output_file:
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved CBO summary to {output_file}")
        
        return fig

