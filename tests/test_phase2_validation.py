"""
Tests for Phase 2 Validation Framework.

Tests baseline data, validation metrics, and accuracy assessments.
"""

import pytest
import pandas as pd
import numpy as np

from core.phase2_validation import (
    CBOBaselineData,
    SSABaselineData,
    ValidationMetrics,
    Phase2Validator,
    run_comprehensive_validation,
)
from core.phase2_integration import (
    Phase2SimulationEngine,
    Phase2PolicyPackage,
)
from core.social_security import SocialSecurityModel


class TestCBOBaselineData:
    """Test CBO baseline data structure."""
    
    def test_cbo_baseline_initialization(self):
        """CBO baseline initializes with default values."""
        cbo = CBOBaselineData()
        
        assert len(cbo.gdp_nominal) > 0
        assert len(cbo.total_revenue) > 0
        assert len(cbo.individual_income_tax) > 0
        
        # Check 2025 values exist
        assert 2025 in cbo.gdp_nominal
        assert 2025 in cbo.total_revenue
    
    def test_cbo_from_2024_outlook(self):
        """Load CBO 2024 outlook baseline."""
        cbo = CBOBaselineData.from_cbo_2024_outlook()
        
        # Should have multi-year projections
        assert len(cbo.gdp_nominal) >= 5
        
        # GDP should grow over time
        years = sorted(cbo.gdp_nominal.keys())
        for i in range(1, len(years)):
            assert cbo.gdp_nominal[years[i]] > cbo.gdp_nominal[years[i-1]]
    
    def test_cbo_revenue_components_sum(self):
        """Revenue components should be reasonable relative to total."""
        cbo = CBOBaselineData()
        
        year = 2025
        individual = cbo.individual_income_tax[year]
        corporate = cbo.corporate_income_tax[year]
        payroll = cbo.payroll_tax[year]
        total = cbo.total_revenue[year]
        
        # Components should be significant portion of total
        component_sum = individual + corporate + payroll
        assert component_sum < total  # Not all revenue captured
        assert component_sum > total * 0.8  # But most of it


class TestSSABaselineData:
    """Test SSA baseline data structure."""
    
    def test_ssa_baseline_initialization(self):
        """SSA baseline initializes with default values."""
        ssa = SSABaselineData()
        
        assert len(ssa.oasi_balance) > 0
        assert len(ssa.payroll_tax_income) > 0
        assert len(ssa.benefit_payments) > 0
        
        # Check 2025 values
        assert 2025 in ssa.oasi_balance
        assert 2025 in ssa.payroll_tax_income
    
    def test_ssa_from_2024_trustees(self):
        """Load SSA 2024 trustees report baseline."""
        ssa = SSABaselineData.from_ssa_2024_trustees()
        
        # Should have depletion estimate
        assert ssa.oasi_depletion_year_estimate is not None
        assert ssa.oasi_depletion_year_estimate >= 2030
        assert ssa.oasi_depletion_year_estimate <= 2040
    
    def test_ssa_trust_fund_declines(self):
        """OASI trust fund should decline over time (under current law)."""
        ssa = SSABaselineData()
        
        years = sorted([y for y in ssa.oasi_balance.keys() if y >= 2025 and y <= 2030])
        
        # Balance should generally decline
        declining_years = 0
        for i in range(1, len(years)):
            if ssa.oasi_balance[years[i]] < ssa.oasi_balance[years[i-1]]:
                declining_years += 1
        
        # Most years should show decline
        assert declining_years >= len(years) - 2
    
    def test_ssa_beneficiaries_increase(self):
        """Beneficiary counts should increase (aging population)."""
        ssa = SSABaselineData()
        
        years = sorted(ssa.oasi_beneficiaries.keys())
        
        for i in range(1, len(years)):
            assert ssa.oasi_beneficiaries[years[i]] > ssa.oasi_beneficiaries[years[i-1]]


class TestValidationMetrics:
    """Test validation metrics calculation."""
    
    def test_metric_within_tolerance(self):
        """Metric within tolerance passes."""
        metric = ValidationMetrics(
            metric_name="Test",
            model_value=100.0,
            baseline_value=105.0,
            absolute_error=5.0,
            percentage_error=4.76,
            within_tolerance=True,
        )
        
        assert metric.within_tolerance is True
        assert "✓" in str(metric)
    
    def test_metric_outside_tolerance(self):
        """Metric outside tolerance fails."""
        metric = ValidationMetrics(
            metric_name="Test",
            model_value=100.0,
            baseline_value=150.0,
            absolute_error=50.0,
            percentage_error=33.33,
            within_tolerance=False,
        )
        
        assert metric.within_tolerance is False
        assert "✗" in str(metric)


class TestPhase2Validator:
    """Test Phase 2 validation framework."""
    
    def test_validator_initialization(self):
        """Validator initializes with baseline data."""
        validator = Phase2Validator(tolerance_pct=10.0)
        
        assert validator.cbo is not None
        assert validator.ssa is not None
        assert validator.tolerance_pct == 10.0
    
    def test_validate_social_security_projections(self):
        """Validate Social Security projections against baseline."""
        # Create model projections
        model = SocialSecurityModel(start_year=2025, seed=42)
        projections = model.project_trust_funds(years=10, iterations=100)
        
        # Run validation
        validator = Phase2Validator(tolerance_pct=20.0)  # Generous tolerance for testing
        results = validator.validate_social_security_projections(projections)
        
        assert results['validation_type'] == 'Social Security'
        assert results['total_comparisons'] > 0
        assert 'accuracy_percentage' in results
        assert 'metrics' in results
        assert len(results['metrics']) > 0
    
    def test_validate_revenue_projections(self):
        """Validate revenue projection growth rates."""
        # Create sample revenue projections
        revenue_df = pd.DataFrame({
            'year': [2025, 2026, 2027, 2028, 2029],
            'total_revenue': [100, 103, 106, 109, 112],  # ~3% growth
        })
        
        validator = Phase2Validator(tolerance_pct=50.0)  # Very generous
        results = validator.validate_revenue_projections(revenue_df, "tax_reform")
        
        assert results['validation_type'] == 'tax_reform Revenue'
        assert 'accuracy_percentage' in results
    
    def test_validate_baseline_consistency(self):
        """Validate baseline consistency checks."""
        # Create mock model output
        model_output = {
            'overview': pd.DataFrame({
                'year': [2025, 2026, 2027],
                'gdp': [28000, 28700, 29400],
                'total_new_revenue': [0, 0, 0],
            }),
            'social_security': pd.DataFrame({
                'year': [2025, 2026, 2027],
                'iteration': [0, 0, 0],
                'oasi_balance_billions': [2800, 2700, 2600],
            }),
        }
        
        validator = Phase2Validator()
        results = validator.validate_baseline_consistency(model_output)
        
        assert results['validation_type'] == 'Baseline Consistency'
        assert results['total_checks'] > 0
        assert 'passed' in results
        assert 'checks' in results
    
    def test_generate_validation_report(self):
        """Generate comprehensive validation report."""
        validator = Phase2Validator()
        
        # Mock validation results
        ss_validation = {
            'baseline_source': 'SSA 2024',
            'accuracy_percentage': 85.0,
            'within_tolerance': 17,
            'total_comparisons': 20,
            'mean_absolute_error_pct': 8.5,
            'metrics': [],
        }
        
        revenue_validation = {
            'baseline_source': 'CBO 2024',
            'accuracy_percentage': 90.0,
            'within_tolerance': 9,
            'total_comparisons': 10,
            'mean_absolute_error_pct': 5.2,
            'metrics': [],
        }
        
        baseline_validation = {
            'total_checks': 2,
            'passed': 2,
            'checks': [
                {'check': 'GDP Growth', 'status': 'PASS', 'value': '2.5%', 'expected': '2-3%'},
                {'check': 'SS Depletion', 'status': 'PASS', 'value': 'Early 2030s', 'expected': 'Early 2030s'},
            ],
        }
        
        report = validator.generate_validation_report(
            ss_validation,
            revenue_validation,
            baseline_validation,
        )
        
        assert "PHASE 2 VALIDATION REPORT" in report
        assert "Social Security Validation" in report
        assert "Revenue Validation" in report
        assert "Baseline Consistency" in report
        assert "OVERALL VALIDATION SCORE" in report
    
    def test_calculate_metric(self):
        """Calculate validation metric with tolerance check."""
        validator = Phase2Validator(tolerance_pct=10.0)
        
        # Within tolerance
        metric1 = validator._calculate_metric("Test1", 100.0, 105.0)
        assert metric1.percentage_error < 10.0
        assert metric1.within_tolerance is True
        
        # Outside tolerance
        metric2 = validator._calculate_metric("Test2", 100.0, 120.0)
        assert metric2.percentage_error > 10.0
        assert metric2.within_tolerance is False


class TestIntegrationValidation:
    """Test validation with real Phase 2 integration."""
    
    def test_validation_with_baseline_scenario(self):
        """Validate baseline (no reforms) scenario."""
        # Run baseline simulation
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
            seed=42,
        )
        
        baseline = Phase2PolicyPackage()
        results = engine.simulate_comprehensive_reform(
            baseline, years=10, iterations=100
        )
        
        # Run validation
        validator = Phase2Validator(tolerance_pct=25.0)  # Generous for testing
        
        ss_validation = validator.validate_social_security_projections(
            results['social_security']
        )
        
        # Should have some accuracy
        assert ss_validation['accuracy_percentage'] > 0
        assert ss_validation['total_comparisons'] > 0
    
    def test_comprehensive_validation_function(self):
        """Test comprehensive validation function."""
        # Create minimal model output
        model_output = {
            'overview': pd.DataFrame({
                'year': [2025, 2026],
                'gdp': [28000, 28700],
                'total_new_revenue': [0, 0],
            }),
            'tax_reforms': pd.DataFrame({
                'year': [2025, 2026],
                'total_revenue': [100, 103],
            }),
            'social_security': pd.DataFrame({
                'year': [2025, 2026] * 10,
                'iteration': [i for i in range(10) for _ in range(2)],
                'oasi_balance_billions': [2800, 2700] * 10,
                'payroll_tax_income_billions': [1120, 1165] * 10,
                'benefit_payments_billions': [1250, 1310] * 10,
            }),
        }
        
        report = run_comprehensive_validation(model_output, tolerance_pct=20.0)
        
        assert isinstance(report, str)
        assert "VALIDATION REPORT" in report
        assert "OVERALL VALIDATION SCORE" in report


class TestValidationAccuracy:
    """Test validation accuracy assessments."""
    
    def test_excellent_accuracy_rating(self):
        """Accuracy >= 90% rated as EXCELLENT."""
        validator = Phase2Validator()
        
        ss_val = {
            'baseline_source': 'SSA',
            'accuracy_percentage': 95.0,
            'within_tolerance': 19,
            'total_comparisons': 20,
            'mean_absolute_error_pct': 3.0,
            'metrics': [],
        }
        
        rev_val = {
            'baseline_source': 'CBO',
            'accuracy_percentage': 92.0,
            'within_tolerance': 9,
            'total_comparisons': 10,
            'mean_absolute_error_pct': 4.0,
            'metrics': [],
        }
        
        base_val = {
            'total_checks': 2,
            'passed': 2,
            'checks': [],
        }
        
        report = validator.generate_validation_report(ss_val, rev_val, base_val)
        
        assert "EXCELLENT" in report
    
    def test_good_accuracy_rating(self):
        """Accuracy 75-90% rated as GOOD."""
        validator = Phase2Validator()
        
        ss_val = {
            'baseline_source': 'SSA',
            'accuracy_percentage': 80.0,
            'within_tolerance': 16,
            'total_comparisons': 20,
            'mean_absolute_error_pct': 12.0,
            'metrics': [],
        }
        
        rev_val = {
            'baseline_source': 'CBO',
            'accuracy_percentage': 78.0,
            'within_tolerance': 7,
            'total_comparisons': 10,
            'mean_absolute_error_pct': 15.0,
            'metrics': [],
        }
        
        base_val = {
            'total_checks': 2,
            'passed': 2,
            'checks': [],
        }
        
        report = validator.generate_validation_report(ss_val, rev_val, base_val)
        
        assert "GOOD" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
