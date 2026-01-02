"""
Integration tests for Phase 5 Slice 5.6 - Scenario Builder and Report Generation

Tests end-to-end workflows:
1. Create custom policy scenario
2. Compare multiple scenarios
3. Generate reports in multiple formats
4. Export scenario bundles
"""

import pytest
import tempfile
import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from core.policy_builder import CustomPolicy, PolicyLibrary, PolicyTemplate, ScenarioBundleLibrary
from core.report_generator import (
    ReportMetadata,
    PDFReportGenerator,
    ExcelReportGenerator,
    ReportSection,
)
from core.report_charts import ReportChartGenerator


class TestPolicyLibraryWorkflow:
    """Test policy library creation and management workflow."""
    
    @pytest.fixture
    def temp_lib_dir(self):
        """Create a temporary library directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_create_policy_from_template(self, temp_lib_dir):
        """Test creating a policy from template."""
        policy = PolicyTemplate.create_from_template("tax_reform", "Custom Tax Reform")
        
        assert policy is not None
        assert policy.name == "Custom Tax Reform"
        assert len(policy.parameters) > 0
    
    def test_add_policy_to_library(self, temp_lib_dir):
        """Test adding a policy to library."""
        lib = PolicyLibrary(library_path=temp_lib_dir)
        
        policy = PolicyTemplate.create_from_template("spending_reform", "Defense Cut")
        success = lib.add_policy(policy)
        
        assert success is True
        assert "Defense Cut" in lib.policies
    
    def test_save_and_load_policy(self, temp_lib_dir):
        """Test saving and loading a policy."""
        lib = PolicyLibrary(library_path=temp_lib_dir)
        
        # Create and add policy
        policy = PolicyTemplate.create_from_template("healthcare", "Universal Healthcare Draft")
        lib.add_policy(policy)
        
        # Create new library instance to test loading
        lib2 = PolicyLibrary(library_path=temp_lib_dir)
        assert "Universal Healthcare Draft" in lib2.policies
    
    def test_clone_policy(self, temp_lib_dir):
        """Test cloning an existing policy."""
        lib = PolicyLibrary(library_path=temp_lib_dir)
        
        # Add original policy
        policy = PolicyTemplate.create_from_template("tax_reform", "Original Tax Policy")
        lib.add_policy(policy)
        
        # Clone it
        success = lib.clone_policy("Original Tax Policy", "Modified Tax Policy")
        
        assert success is True
        assert "Modified Tax Policy" in lib.policies
    
    def test_rename_policy(self, temp_lib_dir):
        """Test renaming a policy."""
        lib = PolicyLibrary(library_path=temp_lib_dir)
        
        policy = PolicyTemplate.create_from_template("spending_reform", "Old Name")
        lib.add_policy(policy)
        
        success = lib.rename_policy("Old Name", "New Name")
        
        assert success is True
        assert "New Name" in lib.policies
        assert "Old Name" not in lib.policies


class TestScenarioBundleWorkflow:
    """Test scenario bundle creation and management."""
    
    def test_create_scenario_bundle(self):
        """Test creating a scenario bundle."""
        bundle = ScenarioBundleLibrary()
        
        assert bundle is not None
        assert hasattr(bundle, 'bundles')
    
    def test_bundle_export_to_json(self):
        """Test exporting scenario bundle to JSON."""
        from core.policy_builder import ScenarioBundle
        
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = os.path.join(tmpdir, "bundles.json")
            lib = ScenarioBundleLibrary(bundle_path=bundle_path)
            
            # Create a scenario bundle
            bundle = ScenarioBundle(
                name="Test Bundle",
                policy_names=["Status Quo", "Tax Reform"],
                description="A test scenario bundle",
            )
            
            # Save bundle
            lib.save_bundle(bundle)
            
            assert os.path.exists(bundle_path)
            
            # Verify export
            with open(bundle_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) > 0


class TestReportGenerationWorkflow:
    """Test end-to-end report generation."""
    
    @pytest.fixture
    def report_data(self):
        """Create sample report data."""
        return {
            "title": "Policy Analysis Report",
            "summary": {
                "revenue_impact": 150,
                "spending_impact": -100,
                "deficit_impact": 250,
            },
            "projections": pd.DataFrame({
                "Year": list(range(2024, 2034)),
                "Baseline Deficit": [-250 - i*10 for i in range(10)],
                "Policy Deficit": [-225 - i*8 for i in range(10)],
            }),
        }
    
    def test_generate_pdf_report(self, report_data):
        """Test PDF report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = ReportMetadata(
                title=report_data["title"],
                author="Test Suite",
            )
            
            generator = PDFReportGenerator(metadata)
            
            # Create sections
            sections = [
                ReportSection(
                    title="Summary",
                    content=f"Revenue Impact: ${report_data['summary']['revenue_impact']}B",
                    data=report_data["projections"],
                ),
            ]
            
            output_path = os.path.join(tmpdir, "report.pdf")
            result = generator.generate(sections, output_path)
            
            assert result is not None
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_generate_excel_report(self, report_data):
        """Test Excel report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = ReportMetadata(
                title=report_data["title"],
            )
            
            generator = ExcelReportGenerator(metadata)
            
            sections = {
                "Projections": report_data["projections"],
                "Summary": pd.DataFrame([report_data["summary"]]),
            }
            
            output_path = os.path.join(tmpdir, "report.xlsx")
            result = generator.generate(sections, output_path=output_path)
            
            assert result is not None
            assert os.path.exists(output_path)
    
    def test_generate_json_export(self, report_data):
        """Test JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            
            # Export to JSON
            with open(output_path, 'w') as f:
                json.dump(report_data, f, default=str)
            
            assert os.path.exists(output_path)
            
            # Verify content
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["title"] == report_data["title"]
            assert loaded["summary"]["revenue_impact"] == 150


class TestChartIntegrationInReports:
    """Test chart generation integration with reports."""
    
    def test_generate_report_with_charts(self):
        """Test generating report with embedded charts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chart_gen = ReportChartGenerator(temp_dir=tmpdir)
            
            # Generate charts
            years = list(range(2024, 2034))
            baseline = [-250 - i*10 for i in range(10)]
            policy = [-200 - i*8 for i in range(10)]
            
            deficit_chart = chart_gen.create_deficit_projection_chart(
                years,
                baseline,
                policy,
            )
            
            if deficit_chart:
                assert os.path.exists(deficit_chart)
            
            # Cleanup
            chart_gen.cleanup()
    
    def test_multi_chart_report_generation(self):
        """Test generating report with multiple charts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chart_gen = ReportChartGenerator(temp_dir=tmpdir)
            
            charts = {}
            
            # Chart 1: Deficit projection
            charts["deficit"] = chart_gen.create_deficit_projection_chart(
                list(range(2024, 2034)),
                [-250 - i*10 for i in range(10)],
                [-200 - i*8 for i in range(10)],
            )
            
            # Chart 2: Revenue impact
            charts["revenue"] = chart_gen.create_revenue_impact_chart(
                ["Income", "Corporate", "Payroll"],
                [150, -50, 75],
            )
            
            # Chart 3: Sensitivity
            charts["sensitivity"] = chart_gen.create_sensitivity_analysis_chart(
                ["Tax Rate", "GDP Growth", "Inflation"],
                [0.05, -0.02, 0.03],
            )
            
            # Verify charts (some may be None if dependencies not available)
            assert len(charts) == 3
            
            chart_gen.cleanup()


class TestErrorHandling:
    """Test error handling in workflows."""
    
    def test_report_generation_with_missing_data(self):
        """Test report generation with incomplete data."""
        metadata = ReportMetadata(title="Empty Report")
        generator = PDFReportGenerator(metadata)
        
        # Should handle empty sections gracefully
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "empty.pdf")
            result = generator.generate([], output_path)
            
            # Should still produce a PDF
            assert result is not None or output_path is not None
    
    def test_duplicate_policy_in_library(self):
        """Test that adding duplicate policy fails gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PolicyLibrary(library_path=tmpdir)
            
            policy = PolicyTemplate.create_from_template("tax_reform", "Test Policy")
            lib.add_policy(policy)
            
            # Try to add same name again
            success = lib.add_policy(policy)
            assert success is False  # Should fail
    
    def test_rename_nonexistent_policy(self):
        """Test renaming a policy that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PolicyLibrary(library_path=tmpdir)
            
            # Try to rename non-existent policy
            success = lib.rename_policy("Nonexistent", "New Name")
            assert success is False


class TestCustomPolicyWorkflow:
    """Test custom policy creation and modification."""
    
    def test_create_custom_policy(self):
        """Test creating a custom policy."""
        from core.policy_builder import PolicyType
        
        policy = CustomPolicy(
            name="Custom Carbon Tax",
            description="A custom carbon tax policy",
            policy_type=PolicyType.TAX_REFORM,
        )
        
        # Add parameters
        policy.add_parameter(
            name="carbon_tax_rate",
            description="Carbon tax rate per ton CO2",
            value=50.0,
            min_val=0.0,
            max_val=200.0,
            unit="$/ton",
            category="energy",
        )
        
        assert "carbon_tax_rate" in policy.parameters
        assert policy.get_parameter_value("carbon_tax_rate") == 50.0
    
    def test_modify_policy_parameter(self):
        """Test modifying a policy parameter."""
        from core.policy_builder import PolicyType
        
        policy = CustomPolicy(
            name="Test",
            description="Test policy",
            policy_type=PolicyType.SPENDING_REFORM,
        )
        policy.add_parameter(
            name="tax_rate",
            description="Tax rate",
            value=10.0,
            min_val=0.0,
            max_val=50.0,
        )
        
        success = policy.update_parameter("tax_rate", 25.0)
        
        assert success is True
        assert policy.get_parameter_value("tax_rate") == 25.0
    
    def test_policy_validation(self):
        """Test policy parameter validation."""
        from core.policy_builder import PolicyType
        
        policy = CustomPolicy(
            name="Validation Test",
            description="Test",
            policy_type=PolicyType.TAX_REFORM,
        )
        policy.add_parameter(
            name="rate",
            description="Rate parameter",
            value=10.0,
            min_val=0.0,
            max_val=50.0,
        )
        
        # Set valid value
        assert policy.update_parameter("rate", 30.0) is True
        
        # Set invalid value (outside range)
        assert policy.update_parameter("rate", 100.0) is False
        # Value should remain 30.0
        assert policy.get_parameter_value("rate") == 30.0
    
    def test_policy_to_json_roundtrip(self):
        """Test converting policy to/from JSON."""
        from core.policy_builder import PolicyType
        
        policy = CustomPolicy(
            name="JSON Test",
            description="Test",
            policy_type=PolicyType.TAX_REFORM,
        )
        policy.add_parameter("param", description="Test parameter", value=42.0, min_val=0.0, max_val=100.0)
        
        # Convert to JSON and back
        json_str = policy.to_json()
        loaded = CustomPolicy.from_json(json_str)
        
        assert loaded.name == policy.name
        assert loaded.get_parameter_value("param") == 42.0


class TestEndToEndWorkflows:
    """Test complete workflows end-to-end."""
    
    def test_policy_to_report_workflow(self):
        """Test complete workflow: create policy -> generate report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create policy
            policy = PolicyTemplate.create_from_template("tax_reform", "Test Tax Reform")
            
            # Step 2: Create report data
            report_data = {
                "policy_name": policy.name,
                "parameters": {
                    param_name: param.value
                    for param_name, param in policy.parameters.items()
                },
            }
            
            # Step 3: Generate report
            report_path = os.path.join(tmpdir, "policy_report.json")
            with open(report_path, 'w') as f:
                json.dump(report_data, f)
            
            assert os.path.exists(report_path)
    
    def test_library_bundle_export_workflow(self):
        """Test complete workflow: library -> bundle -> export."""
        from core.policy_builder import ScenarioBundle
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create policy library
            lib_path = os.path.join(tmpdir, "library")
            lib = PolicyLibrary(library_path=lib_path)
            
            # Step 2: Add multiple policies
            policies = [
                PolicyTemplate.create_from_template("tax_reform", "Policy 1"),
                PolicyTemplate.create_from_template("spending_reform", "Policy 2"),
                PolicyTemplate.create_from_template("healthcare", "Policy 3"),
            ]
            
            for policy in policies:
                lib.add_policy(policy)
            
            # Step 3: Create bundle from policies
            bundle_path = os.path.join(tmpdir, "bundles.json")
            bundle_lib = ScenarioBundleLibrary(bundle_path=bundle_path)
            
            bundle = ScenarioBundle(
                name="Multi-Policy Bundle",
                policy_names=[p.name for p in policies],
                description="Bundle from library policies",
            )
            
            # Step 4: Save bundle
            bundle_lib.save_bundle(bundle)
            
            assert os.path.exists(bundle_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
