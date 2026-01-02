"""
Report Charts Integration Module
Adds visualizations to PDF and Excel reports using Plotly and matplotlib.

Features:
- Generate Plotly charts and embed in reports
- Convert Plotly to images for PDF/Excel
- Create summary visualizations
- Support multiple chart types
"""

import io
import os
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from openpyxl.drawing.image import Image as XLImage
    OPENPYXL_IMAGE_AVAILABLE = True
except ImportError:
    OPENPYXL_IMAGE_AVAILABLE = False


class ReportChartGenerator:
    """Generate charts for policy reports."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize chart generator.
        
        Args:
            temp_dir: Directory for temporary chart files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.chart_files: List[str] = []
    
    def create_deficit_projection_chart(
        self,
        years: List[int],
        baseline_deficit: List[float],
        policy_deficit: List[float],
        title: str = "Deficit Projection: Baseline vs Policy",
    ) -> Optional[str]:
        """Create deficit projection comparison chart.
        
        Args:
            years: List of years
            baseline_deficit: Baseline deficit values
            policy_deficit: Policy deficit values
            title: Chart title
        
        Returns:
            Path to generated chart file
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=years, y=baseline_deficit,
                mode='lines+markers',
                name='Baseline',
                line=dict(color='#d62728', width=2),
            ))
            
            fig.add_trace(go.Scatter(
                x=years, y=policy_deficit,
                mode='lines+markers',
                name='Policy Impact',
                line=dict(color='#2ca02c', width=2),
            ))
            
            fig.update_layout(
                title=title,
                xaxis_title="Year",
                yaxis_title="Deficit ($B)",
                hovermode='x unified',
                template='plotly_white',
                height=500,
                showlegend=True,
            )
            
            return self._export_plotly_to_image(fig, "deficit_projection.png")
        except Exception as e:
            print(f"Error creating deficit chart: {e}")
            return None
    
    def create_revenue_impact_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str = "Revenue Impact by Category",
    ) -> Optional[str]:
        """Create revenue impact bar chart.
        
        Args:
            categories: Category names
            values: Revenue values
            title: Chart title
        
        Returns:
            Path to generated chart file
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            colors = ['#2ca02c' if v > 0 else '#d62728' for v in values]
            
            fig = go.Figure(data=[
                go.Bar(x=categories, y=values, marker_color=colors)
            ])
            
            fig.update_layout(
                title=title,
                xaxis_title="Category",
                yaxis_title="Impact ($B)",
                template='plotly_white',
                height=400,
            )
            
            return self._export_plotly_to_image(fig, "revenue_impact.png")
        except Exception as e:
            print(f"Error creating revenue chart: {e}")
            return None
    
    def create_scenario_comparison_chart(
        self,
        scenario_names: List[str],
        metric_values: Dict[str, List[float]],
        title: str = "Scenario Comparison",
    ) -> Optional[str]:
        """Create multi-scenario comparison chart.
        
        Args:
            scenario_names: Names of scenarios
            metric_values: Dict of metric_name -> values list
            title: Chart title
        
        Returns:
            Path to generated chart file
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            fig = go.Figure()
            
            for metric, values in metric_values.items():
                fig.add_trace(go.Bar(
                    x=scenario_names,
                    y=values,
                    name=metric,
                ))
            
            fig.update_layout(
                title=title,
                xaxis_title="Scenario",
                yaxis_title="Value",
                barmode='group',
                template='plotly_white',
                height=400,
            )
            
            return self._export_plotly_to_image(fig, "scenario_comparison.png")
        except Exception as e:
            print(f"Error creating scenario comparison: {e}")
            return None
    
    def create_sensitivity_analysis_chart(
        self,
        parameter_names: List[str],
        sensitivities: List[float],
        title: str = "Sensitivity Analysis",
    ) -> Optional[str]:
        """Create sensitivity analysis tornado chart.
        
        Args:
            parameter_names: Names of parameters
            sensitivities: Sensitivity values
            title: Chart title
        
        Returns:
            Path to generated chart file
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # Sort by absolute sensitivity
            sorted_indices = sorted(range(len(sensitivities)), 
                                   key=lambda i: abs(sensitivities[i]), 
                                   reverse=True)
            
            sorted_names = [parameter_names[i] for i in sorted_indices]
            sorted_sens = [sensitivities[i] for i in sorted_indices]
            
            colors = ['#2ca02c' if v > 0 else '#d62728' for v in sorted_sens]
            
            fig = go.Figure(data=[
                go.Bar(
                    y=sorted_names,
                    x=sorted_sens,
                    orientation='h',
                    marker_color=colors,
                )
            ])
            
            fig.update_layout(
                title=title,
                xaxis_title="Sensitivity Impact (%)",
                yaxis_title="Parameter",
                template='plotly_white',
                height=400,
            )
            
            return self._export_plotly_to_image(fig, "sensitivity_analysis.png")
        except Exception as e:
            print(f"Error creating sensitivity chart: {e}")
            return None
    
    def create_monte_carlo_distribution_chart(
        self,
        simulation_results: np.ndarray,
        metric_name: str = "Outcome",
        title: Optional[str] = None,
    ) -> Optional[str]:
        """Create Monte Carlo simulation distribution chart.
        
        Args:
            simulation_results: Array of simulation results
            metric_name: Name of the metric
            title: Chart title
        
        Returns:
            Path to generated chart file
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            if title is None:
                title = f"Monte Carlo Distribution - {metric_name}"
            
            fig = go.Figure(data=[
                go.Histogram(
                    x=simulation_results,
                    nbinsx=50,
                    name=metric_name,
                    marker_color='#1f77b4',
                )
            ])
            
            # Add percentile lines
            p5 = np.percentile(simulation_results, 5)
            p50 = np.percentile(simulation_results, 50)
            p95 = np.percentile(simulation_results, 95)
            
            fig.add_vline(x=p5, line_dash="dash", line_color="red", 
                         annotation_text="5th percentile")
            fig.add_vline(x=p50, line_dash="dash", line_color="green",
                         annotation_text="Median")
            fig.add_vline(x=p95, line_dash="dash", line_color="orange",
                         annotation_text="95th percentile")
            
            fig.update_layout(
                title=title,
                xaxis_title=metric_name,
                yaxis_title="Frequency",
                template='plotly_white',
                height=400,
            )
            
            return self._export_plotly_to_image(fig, "monte_carlo_distribution.png")
        except Exception as e:
            print(f"Error creating Monte Carlo chart: {e}")
            return None
    
    def _export_plotly_to_image(self, fig: "go.Figure", filename: str) -> Optional[str]:
        """Export Plotly figure to image file.
        
        Args:
            fig: Plotly figure object
            filename: Output filename
        
        Returns:
            Path to saved image file, or None if failed
        """
        if not KALEIDO_AVAILABLE:
            print("Warning: kaleido required for chart export. Install with: pip install kaleido")
            return None
        
        try:
            filepath = os.path.join(self.temp_dir, filename)
            fig.write_image(filepath, format='png')
            self.chart_files.append(filepath)
            return filepath
        except Exception as e:
            print(f"Error exporting Plotly chart: {e}")
            return None
    
    def cleanup(self):
        """Clean up temporary chart files."""
        for filepath in self.chart_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"Warning: Could not delete {filepath}: {e}")


class ExcelChartEmbedder:
    """Embed images in Excel workbooks."""
    
    @staticmethod
    def embed_chart_in_worksheet(
        worksheet: "openpyxl.worksheet.worksheet.Worksheet",
        chart_path: str,
        cell_position: str = "A1",
        width: int = 15,
        height: int = 10,
    ) -> bool:
        """Embed an image chart in an Excel worksheet.
        
        Args:
            worksheet: openpyxl worksheet
            chart_path: Path to chart image
            cell_position: Cell to insert chart
            width: Chart width in cm
            height: Chart height in cm
        
        Returns:
            True if successful, False otherwise
        """
        if not OPENPYXL_IMAGE_AVAILABLE:
            return False
        
        try:
            if not os.path.exists(chart_path):
                return False
            
            img = XLImage(chart_path)
            img.width = width
            img.height = height
            
            worksheet.add_image(img, cell_position)
            return True
        except Exception as e:
            print(f"Error embedding chart in Excel: {e}")
            return False


def demo():
    """Demo the chart generators."""
    import matplotlib.pyplot as plt
    
    # Create sample data
    years = list(range(2024, 2034))
    baseline = [-200 - i*10 for i in range(len(years))]
    policy = [-150 - i*8 for i in range(len(years))]
    
    gen = ReportChartGenerator()
    
    # Generate deficit chart
    chart = gen.create_deficit_projection_chart(years, baseline, policy)
    if chart:
        print(f"✅ Deficit chart created: {chart}")
    
    # Generate revenue impact chart
    categories = ["Income Tax", "Corporate Tax", "Payroll Tax", "Excise Tax"]
    values = [50, -30, 40, 10]
    
    chart = gen.create_revenue_impact_chart(categories, values)
    if chart:
        print(f"✅ Revenue chart created: {chart}")
    
    # Cleanup
    gen.cleanup()


if __name__ == "__main__":
    demo()
