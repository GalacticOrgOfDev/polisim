"""
Edge Cases Tests - Fiscal Models

Tests edge cases, error handling, and boundary conditions for
Social Security and Revenue modeling components.
"""

import pytest
import numpy as np
import pandas as pd
from core.social_security import SocialSecurityModel
from core.revenue_modeling import FederalRevenueModel


class TestFiscalModelEdgeCases:
    """Test edge cases and boundary conditions for fiscal models."""

    def test_single_iteration(self):
        """Test with single Monte Carlo iteration."""
        model = SocialSecurityModel()
        result = model.project_trust_funds(years=5, iterations=1)
        
        assert len(result) == 5  # 5 years
        assert result['iteration'].unique() == [0]
        assert all(result['oasi_balance_billions'] >= 0)

    def test_very_high_iterations(self):
        """Test with high iteration count (performance edge case)."""
        model = SocialSecurityModel()
        result = model.project_trust_funds(years=5, iterations=5000)
        
        assert len(result) == 25000  # 5 years * 5000 iterations
        assert len(result['iteration'].unique()) == 5000

    def test_negative_balance_handling(self):
        """Test that negative balances are handled correctly."""
        model = SocialSecurityModel()
        # Project far enough to potentially deplete funds
        result = model.project_trust_funds(years=50, iterations=100)
        
        # Check that balances never go negative (clamped to 0)
        assert all(result['oasi_balance_billions'] >= 0)
        assert all(result['di_balance_billions'] >= 0)

    def test_empty_dataframe_solvency(self):
        """Test solvency analysis with empty DataFrame."""
        model = SocialSecurityModel()
        empty_df = pd.DataFrame(columns=['year', 'iteration', 'oasi_balance_billions'])
        
        with pytest.raises((ValueError, KeyError)):
            model.estimate_solvency_dates(empty_df)

    def test_multiindex_solvency_aggregated(self):
        """Test that solvency handles aggregated mean data correctly."""
        model = SocialSecurityModel()
        result = model.project_trust_funds(years=10, iterations=100)
        
        # Create aggregated data by taking mean across iterations
        # This simulates what happens in the dashboard
        agg = result.groupby('year').mean(numeric_only=True).reset_index()
        
        # Remove iteration column since we're using mean values
        if 'iteration' in agg.columns:
            agg = agg.drop(columns=['iteration'])
        agg['iteration'] = 0  # Add back as dummy for compatibility
        
        # Should handle aggregated data without error
        # Note: We're testing with mean values, so this is like single-iteration data
        solvency = model.estimate_solvency_dates(agg)
        assert 'OASI' in solvency or 'Combined' in solvency


class TestDataValidation:
    """Test data validation and error handling."""

    def test_revenue_projection_with_negative_growth(self):
        """Test revenue projection with negative GDP growth (recession)."""
        model = FederalRevenueModel()
        gdp_growth = np.array([-0.03, -0.02, 0.01, 0.02, 0.03])  # Recession then recovery
        
        result = model.project_all_revenues(
            years=5, 
            gdp_growth=gdp_growth,
            iterations=100
        )
        
        assert len(result) == 500  # 5 years * 100 iterations
        # Revenue should still be positive even in recession
        assert all(result['total_revenues'] > 0)

    def test_extreme_demographic_uncertainty(self):
        """Test with extreme demographic uncertainty."""
        model = SocialSecurityModel()
        # Increase uncertainty parameters
        model.demographics.mortality_uncertainty_std = 0.5  # Very high uncertainty
        model.demographics.fertility_uncertainty_std = 0.5
        
        # Should still produce valid results
        result = model.project_trust_funds(years=10, iterations=50)
        assert len(result) == 500
        assert all(result['oasi_balance_billions'] >= 0)


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    def test_maximum_age_population(self):
        """Test population projection at age boundary (100+)."""
        model = SocialSecurityModel()
        pop_result = model.project_population(years=5, iterations=10)
        
        # Check that age 100+ (index 100) has positive population
        assert pop_result['population'].shape[1] == 101  # Ages 0-100
        assert np.all(pop_result['population'][:, 100, :] >= 0)

    def test_payroll_tax_cap_at_zero(self):
        """Test with zero payroll tax cap (no cap)."""
        model = FederalRevenueModel()
        model.payroll.social_security_wage_cap = None  # No cap
        
        result = model.project_payroll_taxes(
            years=5,
            wage_growth=np.full(5, 0.03),
            employment=np.ones(5),
            iterations=50
        )
        
        assert result['total_payroll_revenues'].shape == (5, 50)

    def test_zero_initial_trust_fund_balance(self):
        """Test with zero initial trust fund balance."""
        model = SocialSecurityModel()
        model.trust_fund.oasi_beginning_balance = 0
        model.trust_fund.di_beginning_balance = 0
        
        result = model.project_trust_funds(years=5, iterations=10)
        
        # Should still run without error
        assert len(result) == 50


class TestOutputConsistency:
    """Test output format and consistency."""

    def test_projection_column_names(self):
        """Test that projection outputs have expected column names."""
        model = SocialSecurityModel()
        result = model.project_trust_funds(years=5, iterations=10)
        
        expected_columns = [
            'year', 'iteration', 'oasi_balance_billions', 'di_balance_billions',
            'payroll_tax_income_billions', 'interest_income_billions',
            'benefit_payments_billions', 'admin_expenses_billions'
        ]
        
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"

    def test_solvency_output_format(self):
        """Test solvency analysis output format."""
        model = SocialSecurityModel()
        result = model.project_trust_funds(years=10, iterations=100)
        solvency = model.estimate_solvency_dates(result)
        
        # Should return dict with fund names as keys
        assert isinstance(solvency, dict)
        
        # Check for expected keys in output
        for fund_name in ['OASI', 'DI', 'Combined']:
            if fund_name in solvency:
                fund_data = solvency[fund_name]
                assert 'probability_depleted' in fund_data
                assert isinstance(fund_data['probability_depleted'], (int, float))

    def test_revenue_output_consistency(self):
        """Test that revenue projection output is consistent."""
        model = FederalRevenueModel()
        result = model.project_all_revenues(years=10, iterations=100)
        
        # Total should equal sum of components
        for idx in range(len(result)):
            row = result.iloc[idx]
            computed_total = (
                row['individual_income_tax'] +
                row['social_security_tax'] +
                row['medicare_tax'] +
                row['corporate_income_tax'] +
                row['excise_taxes'] +
                row['other_revenues']
            )
            assert abs(row['total_revenues'] - computed_total) < 0.01


class TestPerformance:
    """Test performance and resource usage."""

    def test_large_projection_completes(self):
        """Test that large projections complete in reasonable time."""
        model = SocialSecurityModel()
        
        # This should complete in under 30 seconds with our optimizations
        result = model.project_trust_funds(years=20, iterations=1000)
        
        assert len(result) == 20000
        assert result['year'].max() - result['year'].min() == 19

    def test_memory_efficiency(self):
        """Test that projections don't cause memory issues."""
        model = FederalRevenueModel()
        
        # Run multiple projections sequentially
        for _ in range(3):
            result = model.project_all_revenues(years=10, iterations=500)
            assert len(result) == 5000
            # Delete to free memory
            del result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
