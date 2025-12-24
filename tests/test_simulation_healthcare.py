"""
Unit tests for healthcare simulation module.

Tests cover:
- Basic policy loading and simulation
- Edge cases (high debt, zero growth, etc.)
- Output validation and data integrity
- Multi-policy comparison
- Error handling
"""

import pytest
import pandas as pd
import logging

from core import get_policy_by_type, PolicyType, simulate_healthcare_years, list_available_policies

logger = logging.getLogger(__name__)


class TestPolicyLoading:
    """Test healthcare policy loading."""
    
    def test_get_usgha_policy(self):
        """Test loading USGHA policy."""
        policy = get_policy_by_type(PolicyType.USGHA)
        assert policy is not None
        assert policy.policy_name == "United States Galactic Health Act"
        assert policy.coverage_percentage == 0.99
        logger.info(f"Loaded policy: {policy.policy_name}")
    
    def test_get_current_us_policy(self):
        """Test loading Current US policy."""
        policy = get_policy_by_type(PolicyType.CURRENT_US)
        assert policy is not None
        assert policy.policy_name == "Current US Healthcare System"
        assert policy.coverage_percentage == 0.92
        logger.info(f"Loaded policy: {policy.policy_name}")
    
    def test_list_available_policies(self):
        """Test listing available policies."""
        policies = list_available_policies()
        assert len(policies) > 0
        assert "United States Galactic Health Act" in [p.policy_name for p in policies]
        logger.info(f"Found {len(policies)} available policies")
    
    def test_invalid_policy_type(self):
        """Test that invalid policy type raises error."""
        # This would require modifying PolicyType enum or handling in get_policy_by_type
        # For now, we test that accessing a policy works
        with pytest.raises((ValueError, AttributeError)):
            get_policy_by_type("INVALID_POLICY")


class TestBasicSimulation:
    """Tests for basic healthcare simulation."""
    
    def test_simulate_healthcare_basic(self):
        """Test basic healthcare simulation."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=29e12,
            initial_debt=35e12,
            years=5,
            population=335e6,
            gdp_growth=0.02,
            start_year=2027
        )
        
        assert isinstance(df, pd.DataFrame), "Result should be a DataFrame"
        assert len(df) == 5, "Should have 5 rows for 5 years"
        
        # Validate expected columns
        expected_columns = [
            'Year', 'GDP', 'Health Spending ($)', 'Health % GDP',
            'Per Capita Health ($)', 'Revenue ($)', 'Surplus ($)', 'Remaining Debt ($)'
        ]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        logger.info(f"Simulation generated {len(df)} rows with {len(df.columns)} columns")
    
    def test_output_data_integrity(self):
        """Test that simulation output has valid data."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=29e12,
            initial_debt=35e12,
            years=3,
            population=335e6,
            gdp_growth=0.025,
            start_year=2027
        )
        
        # No NaNs in critical columns
        critical_cols = ['Year', 'GDP', 'Health Spending ($)', 'Revenue ($)']
        for col in critical_cols:
            assert df[col].notna().all(), f"Column {col} has NaN values"
        
        # GDP should be positive
        assert (df['GDP'] > 0).all(), "GDP should be positive"
        
        # Health spending should be less than GDP (sanity check)
        assert (df['Health Spending ($)'] < df['GDP']).all(), "Health spending should be < GDP"
        
        logger.info("Output data integrity validated")
    
    def test_year_sequence(self):
        """Test that year sequence is correct."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=29e12,
            initial_debt=35e12,
            years=10,
            population=335e6,
            gdp_growth=0.02,
            start_year=2027
        )
        
        expected_years = list(range(2027, 2037))
        assert list(df['Year']) == expected_years, "Years should be sequential from start_year"
        logger.info(f"Year sequence validated: {expected_years[0]}-{expected_years[-1]}")


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_high_debt_scenario(self):
        """Test simulation with very high debt."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=1e12,
            initial_debt=100e12,  # Very high debt
            years=3,
            population=1e6,
            gdp_growth=0.0,
            start_year=2027
        )
        
        assert isinstance(df, pd.DataFrame), "Should handle high debt"
        assert (df['Remaining Debt ($)'] >= 0).all(), "Debt should be non-negative"
        assert all(df['Remaining Debt ($)'].apply(lambda x: x < float('inf'))), "Debt should not explode to infinity"
        logger.info("High debt scenario handled correctly")
    
    def test_zero_growth_scenario(self):
        """Test simulation with zero GDP growth."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=29e12,
            initial_debt=35e12,
            years=5,
            population=335e6,
            gdp_growth=0.0,  # Zero growth
            start_year=2027
        )
        
        assert isinstance(df, pd.DataFrame), "Should handle zero growth"
        assert len(df) == 5, "Should complete simulation"
        logger.info("Zero growth scenario handled correctly")
    
    def test_negative_growth_scenario(self):
        """Test simulation with negative growth (recession)."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=29e12,
            initial_debt=35e12,
            years=5,
            population=335e6,
            gdp_growth=-0.02,  # Recession
            start_year=2027
        )
        
        assert isinstance(df, pd.DataFrame), "Should handle recession"
        assert len(df) == 5, "Should complete simulation"
        assert (df['GDP'] > 0).all(), "GDP should remain positive (or decay gracefully)"
        logger.info("Negative growth (recession) scenario handled correctly")
    
    def test_single_year_simulation(self):
        """Test simulation with single year."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=29e12,
            initial_debt=35e12,
            years=1,
            population=335e6,
            gdp_growth=0.02,
            start_year=2027
        )
        
        assert len(df) == 1, "Should have 1 row"
        assert df.iloc[0]['Year'] == 2027, "Year should be start_year"
        logger.info("Single year simulation handled correctly")
    
    def test_very_high_years(self):
        """Test simulation with many years."""
        policy = get_policy_by_type(PolicyType.USGHA)
        df = simulate_healthcare_years(
            policy,
            base_gdp=29e12,
            initial_debt=35e12,
            years=50,  # Long projection
            population=335e6,
            gdp_growth=0.02,
            start_year=2027
        )
        
        assert len(df) == 50, "Should have 50 rows"
        assert df.iloc[-1]['Year'] == 2076, "Final year should be 2027 + 49"
        logger.info("Long-term (50 year) simulation handled correctly")


class TestPolicyComparison:
    """Tests for comparing multiple policies."""
    
    def test_baseline_vs_usgha_comparison(self):
        """Test comparing Current US vs USGHA."""
        baseline = get_policy_by_type(PolicyType.CURRENT_US)
        usgha = get_policy_by_type(PolicyType.USGHA)
        
        df_baseline = simulate_healthcare_years(
            baseline,
            base_gdp=29e12,
            initial_debt=35e12,
            years=10,
            population=335e6,
            gdp_growth=0.025,
            start_year=2027
        )
        
        df_usgha = simulate_healthcare_years(
            usgha,
            base_gdp=29e12,
            initial_debt=35e12,
            years=10,
            population=335e6,
            gdp_growth=0.025,
            start_year=2027
        )
        
        assert len(df_baseline) == len(df_usgha), "Should have same length"
        
        # USGHA should have lower health spending % GDP (9% target vs 18% baseline)
        avg_baseline_pct = df_baseline['Health % GDP'].mean()
        avg_usgha_pct = df_usgha['Health % GDP'].mean()
        
        logger.info(f"Baseline health spending: {avg_baseline_pct:.1%}, USGHA: {avg_usgha_pct:.1%}")
        assert avg_usgha_pct < avg_baseline_pct, "USGHA should reduce healthcare spending"


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_negative_population(self):
        """Test that negative population raises error."""
        policy = get_policy_by_type(PolicyType.USGHA)
        
        with pytest.raises((ValueError, RuntimeError, AssertionError)):
            simulate_healthcare_years(
                policy,
                base_gdp=29e12,
                initial_debt=35e12,
                years=5,
                population=-335e6,  # Invalid negative population
                gdp_growth=0.02,
                start_year=2027
            )
        logger.info("Negative population error caught correctly")
    
    def test_negative_gdp(self):
        """Test that negative GDP raises error."""
        policy = get_policy_by_type(PolicyType.USGHA)
        
        with pytest.raises((ValueError, RuntimeError, AssertionError)):
            simulate_healthcare_years(
                policy,
                base_gdp=-29e12,  # Invalid negative GDP
                initial_debt=35e12,
                years=5,
                population=335e6,
                gdp_growth=0.02,
                start_year=2027
            )
        logger.info("Negative GDP error caught correctly")
    
    def test_negative_initial_debt(self):
        """Test that negative initial debt raises error."""
        policy = get_policy_by_type(PolicyType.USGHA)
        
        with pytest.raises((ValueError, RuntimeError, AssertionError)):
            simulate_healthcare_years(
                policy,
                base_gdp=29e12,
                initial_debt=-35e12,  # Invalid negative debt
                years=5,
                population=335e6,
                gdp_growth=0.02,
                start_year=2027
            )
        logger.info("Negative initial debt error caught correctly")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

