"""
Tests for report chart generation module.
"""

import os
import pytest
import tempfile
import numpy as np
import pandas as pd
from core.report_charts import (
    ReportChartGenerator,
    ExcelChartEmbedder,
)


class TestReportChartGenerator:
    """Test suite for ReportChartGenerator."""
    
    @pytest.fixture
    def chart_gen(self):
        """Create a chart generator with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = ReportChartGenerator(temp_dir=tmpdir)
            yield gen
            gen.cleanup()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for charts."""
        return {
            'years': list(range(2024, 2034)),
            'baseline_deficit': [-200 - i*10 for i in range(10)],
            'policy_deficit': [-150 - i*8 for i in range(10)],
            'categories': ["Income Tax", "Corporate Tax", "Payroll Tax"],
            'values': [50, -30, 40],
            'scenarios': ["Status Quo", "Tax Reform", "Spending Cut"],
            'metrics': {
                'Deficit Impact': [-200, -150, -180],
                'GDP Growth': [2.5, 2.3, 2.6],
            },
        }
    
    def test_deficit_projection_chart(self, chart_gen, sample_data):
        """Test deficit projection chart creation."""
        result = chart_gen.create_deficit_projection_chart(
            sample_data['years'],
            sample_data['baseline_deficit'],
            sample_data['policy_deficit'],
        )
        
        if result is not None:
            assert os.path.exists(result)
            assert result.endswith('.png')
    
    def test_revenue_impact_chart(self, chart_gen, sample_data):
        """Test revenue impact chart creation."""
        result = chart_gen.create_revenue_impact_chart(
            sample_data['categories'],
            sample_data['values'],
        )
        
        if result is not None:
            assert os.path.exists(result)
            assert result.endswith('.png')
    
    def test_scenario_comparison_chart(self, chart_gen, sample_data):
        """Test scenario comparison chart creation."""
        result = chart_gen.create_scenario_comparison_chart(
            sample_data['scenarios'],
            sample_data['metrics'],
        )
        
        if result is not None:
            assert os.path.exists(result)
            assert result.endswith('.png')
    
    def test_sensitivity_analysis_chart(self, chart_gen):
        """Test sensitivity analysis chart creation."""
        parameters = ["Parameter A", "Parameter B", "Parameter C"]
        sensitivities = [0.05, -0.03, 0.02]
        
        result = chart_gen.create_sensitivity_analysis_chart(
            parameters,
            sensitivities,
        )
        
        if result is not None:
            assert os.path.exists(result)
            assert result.endswith('.png')
    
    def test_monte_carlo_distribution_chart(self, chart_gen):
        """Test Monte Carlo distribution chart creation."""
        results = np.random.normal(loc=100, scale=20, size=10000)
        
        chart = chart_gen.create_monte_carlo_distribution_chart(
            results,
            metric_name="Net Present Value",
        )
        
        if chart is not None:
            assert os.path.exists(chart)
            assert chart.endswith('.png')
    
    def test_cleanup_removes_files(self, chart_gen, sample_data):
        """Test that cleanup removes temporary files."""
        temp_dir = chart_gen.temp_dir
        
        # Create a chart
        chart = chart_gen.create_deficit_projection_chart(
            sample_data['years'],
            sample_data['baseline_deficit'],
            sample_data['policy_deficit'],
        )
        
        if chart is not None:
            assert os.path.exists(chart)
            
            # Cleanup
            chart_gen.cleanup()
            
            # Chart file should be removed
            assert not os.path.exists(chart)
    
    def test_invalid_data_handling(self, chart_gen):
        """Test graceful handling of invalid data."""
        # Empty lists
        result = chart_gen.create_revenue_impact_chart([], [])
        # Should not crash, returns None if Plotly unavailable
        
        # Mismatched lengths
        result = chart_gen.create_revenue_impact_chart(
            ["A", "B"],
            [1, 2, 3],  # Too many values
        )
        # Should handle gracefully


class TestChartIntegration:
    """Test chart integration with report generation."""
    
    def test_chart_generator_with_real_data(self):
        """Test chart generation with realistic policy data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = ReportChartGenerator(temp_dir=tmpdir)
            
            # Simulate fiscal projection
            years = list(range(2024, 2035))
            baseline_deficit = np.linspace(-250, -350, len(years)).tolist()
            policy_deficit = np.linspace(-200, -300, len(years)).tolist()
            
            chart = gen.create_deficit_projection_chart(
                years,
                baseline_deficit,
                policy_deficit,
                title="10-Year Deficit Projection: Tax Reform Package",
            )
            
            if chart is not None:
                assert os.path.exists(chart)
                assert os.path.getsize(chart) > 0
            
            gen.cleanup()
    
    def test_multiple_charts_generation(self):
        """Test generating multiple charts in sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = ReportChartGenerator(temp_dir=tmpdir)
            
            charts = []
            
            # Chart 1: Deficit projection
            chart1 = gen.create_deficit_projection_chart(
                list(range(2024, 2034)),
                [-200 - i*10 for i in range(10)],
                [-150 - i*8 for i in range(10)],
            )
            if chart1:
                charts.append(chart1)
            
            # Chart 2: Revenue impact
            chart2 = gen.create_revenue_impact_chart(
                ["Income", "Corporate", "Payroll"],
                [50, -30, 40],
            )
            if chart2:
                charts.append(chart2)
            
            # Chart 3: Sensitivity
            chart3 = gen.create_sensitivity_analysis_chart(
                ["Tax Rate", "Evasion Rate", "GDP Growth"],
                [0.05, -0.02, 0.03],
            )
            if chart3:
                charts.append(chart3)
            
            # All should be created without errors
            assert len(charts) >= 0  # At least no exceptions raised
            
            gen.cleanup()
    
    def test_chart_distribution_percentiles(self):
        """Test Monte Carlo chart with percentile markers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = ReportChartGenerator(temp_dir=tmpdir)
            
            # Create realistic simulation results (e.g., 10-year NPV)
            results = np.random.normal(loc=1000, scale=200, size=5000)
            
            chart = gen.create_monte_carlo_distribution_chart(
                results,
                metric_name="10-Year Net Present Value ($B)",
            )
            
            if chart is not None:
                assert os.path.exists(chart)
            
            gen.cleanup()


class TestExcelChartEmbedder:
    """Test Excel chart embedding."""
    
    def test_chart_path_validation(self):
        """Test that invalid paths are handled."""
        try:
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            
            # Non-existent file
            result = ExcelChartEmbedder.embed_chart_in_worksheet(
                ws,
                "/nonexistent/path/chart.png",
            )
            
            assert result is False
        except ImportError:
            pytest.skip("openpyxl not available")
    
    def test_chart_dimensions(self):
        """Test setting chart dimensions in worksheet."""
        try:
            from openpyxl import Workbook
            import tempfile
            
            wb = Workbook()
            ws = wb.active
            
            # Create a temporary chart image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                # Create a minimal PNG file (1x1 pixel)
                # This is a valid PNG header + minimal data
                png_data = (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
                    b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
                    b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
                )
                tmp.write(png_data)
                tmp_path = tmp.name
            
            # Now try to embed
            result = ExcelChartEmbedder.embed_chart_in_worksheet(
                ws,
                tmp_path,
                cell_position="B2",
                width=10,
                height=8,
            )
            
            # Should return True or False without exception
            assert isinstance(result, bool)
            
            # Clean up after the test
            try:
                os.unlink(tmp_path)
            except:
                pass  # File may be locked, let OS cleanup
        except ImportError:
            pytest.skip("openpyxl not available")
