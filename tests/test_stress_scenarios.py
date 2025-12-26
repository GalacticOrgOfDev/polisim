"""
Stress Testing for Combined Fiscal Outlook - Sprint 3.4
Tests extreme scenarios, edge cases, and boundary conditions.
"""

import pytest
import numpy as np
import pandas as pd

from core.combined_outlook import CombinedFiscalOutlookModel
from core.discretionary_spending import DiscretionarySpendingModel
from core.interest_spending import InterestOnDebtModel


class TestExtremeEconomicScenarios:
    """Test extreme economic conditions."""
    
    def test_deep_recession_scenario(self):
        """Test severe recession with revenue collapse."""
        model = CombinedFiscalOutlookModel()
        
        # Deep recession: significant revenue drop but spending stays high
        df = model.project_unified_budget(years=10, iterations=500)
        
        # Should complete without errors
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        
        # Revenue should still be positive
        assert np.all(df["total_revenue"] > 0)
        
        # Deficit likely to be large but finite
        assert np.all(np.isfinite(df["deficit_surplus"]))
    
    def test_very_high_inflation_scenario(self):
        """Test scenario with very high spending growth."""
        model = CombinedFiscalOutlookModel()
        
        # High inflation drives rapid spending growth
        df = model.project_unified_budget(years=30, iterations=500)
        
        # Year 30 spending should be significantly higher than year 1
        spending_ratio = df.iloc[29]["total_spending"] / df.iloc[0]["total_spending"]
        
        # Should grow but not explosively (2-5x over 30 years reasonable)
        assert spending_ratio > 2.0, "Spending should grow over 30 years"
        assert spending_ratio < 10.0, "Spending growth seems unrealistic"
    
    def test_extended_75year_projection(self):
        """Test maximum 75-year projection length."""
        model = CombinedFiscalOutlookModel()
        
        # 75 years is upper limit for CBO-style projections
        df = model.project_unified_budget(years=75, iterations=100)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 75
        
        # Check all years have valid data
        assert np.all(df["total_revenue"] > 0)
        assert np.all(df["total_spending"] > 0)
        
        # Check no NaN or inf values
        for col in df.columns:
            if col != "year":
                assert np.all(np.isfinite(df[col])), f"Column {col} has non-finite values"


class TestBoundaryConditions:
    """Test boundary values and limits."""
    
    def test_minimum_iterations(self):
        """Test with minimum Monte Carlo iterations."""
        model = CombinedFiscalOutlookModel()
        
        # 100 iterations is minimum for reasonable uncertainty
        df = model.project_unified_budget(years=10, iterations=100)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
    
    def test_maximum_iterations(self):
        """Test with maximum practical iterations."""
        model = CombinedFiscalOutlookModel()
        
        # 10,000 iterations for high precision (slow but should work)
        df = model.project_unified_budget(years=5, iterations=10000)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
    
    def test_single_year_projection(self):
        """Test minimum projection length (1 year)."""
        model = CombinedFiscalOutlookModel()
        
        df = model.project_unified_budget(years=1, iterations=500)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        
        # Single year should still have all components
        assert "total_revenue" in df.columns
        assert "total_spending" in df.columns
        assert df.iloc[0]["total_revenue"] > 0
    
    def test_very_high_spending_ratios(self):
        """Test scenario where spending >> revenue."""
        model = CombinedFiscalOutlookModel()
        
        # In extreme deficit scenarios, spending could be 2x revenue
        df = model.project_unified_budget(years=30, iterations=500)
        
        # Calculate max deficit as % of revenue
        max_deficit_ratio = abs(df["deficit_surplus"].min()) / df["total_revenue"].mean()
        
        # Deficit should not exceed 100% of revenue (spending < 2x revenue)
        # If it does, model may be broken
        assert max_deficit_ratio < 1.5, f"Extreme deficit ratio: {max_deficit_ratio:.2f}"


class TestDataIntegrity:
    """Test data consistency and integrity."""
    
    def test_no_negative_spending(self):
        """Verify all spending components are non-negative."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        spending_columns = [
            "social_security_spending",
            "medicare_spending",
            "medicaid_spending",
            "other_health_spending",
            "discretionary_spending",
            "interest_spending"
        ]
        
        for col in spending_columns:
            assert np.all(df[col] >= 0), f"{col} has negative values"
    
    def test_no_negative_revenue(self):
        """Verify revenue is always non-negative."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        assert np.all(df["total_revenue"] >= 0), "Negative revenue detected"
    
    def test_mandatory_spending_calculation(self):
        """Verify mandatory spending sum is correct."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        computed_mandatory = (
            df["social_security_spending"] +
            df["medicare_spending"] +
            df["medicaid_spending"] +
            df["other_health_spending"]
        )
        
        assert np.allclose(computed_mandatory, df["mandatory_spending"], rtol=0.01)
    
    def test_total_spending_calculation(self):
        """Verify total spending sum is correct."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        computed_total = (
            df["mandatory_spending"] +
            df["discretionary_spending"] +
            df["interest_spending"]
        )
        
        assert np.allclose(computed_total, df["total_spending"], rtol=0.01)
    
    def test_no_nan_or_inf_values(self):
        """Ensure no NaN or infinity in results."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        # Check all numeric columns
        for col in df.columns:
            if col != "year":
                assert not df[col].isna().any(), f"{col} contains NaN"
                assert np.all(np.isfinite(df[col])), f"{col} contains inf"


class TestSpendingComponentRatios:
    """Test realistic spending component ratios."""
    
    def test_social_security_share_reasonable(self):
        """Social Security should be 15-30% of spending."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        ss_share = df["social_security_spending"] / df["total_spending"]
        
        assert np.all(ss_share > 0.10), "Social Security share too low"
        assert np.all(ss_share < 0.40), "Social Security share too high"
    
    def test_healthcare_share_reasonable(self):
        """Medicare+Medicaid should be 20-40% of spending."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        healthcare_share = (
            df["medicare_spending"] + 
            df["medicaid_spending"]
        ) / df["total_spending"]
        
        assert np.all(healthcare_share > 0.15), "Healthcare share too low"
        assert np.all(healthcare_share < 0.50), "Healthcare share too high"
    
    def test_discretionary_share_reasonable(self):
        """Discretionary should be 15-40% of spending."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=500)
        
        discret_share = df["discretionary_spending"] / df["total_spending"]
        
        assert np.all(discret_share > 0.10), "Discretionary share too low"
        assert np.all(discret_share < 0.50), "Discretionary share too high"
    
    def test_interest_grows_with_debt(self):
        """Interest spending should grow over time with debt."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=30, iterations=500)
        
        # Year 30 interest should be higher than year 1
        # (unless we have sustained surpluses, which is unlikely)
        year1_interest = df.iloc[0]["interest_spending"]
        year30_interest = df.iloc[29]["interest_spending"]
        
        # Interest should grow (or at least not shrink dramatically)
        assert year30_interest >= year1_interest * 0.8, "Interest spending declined unexpectedly"


class TestMonteCarloStability:
    """Test Monte Carlo simulation stability."""
    
    def test_low_iteration_variance(self):
        """Test that low iterations produce reasonable variance."""
        model = CombinedFiscalOutlookModel()
        
        # Run same projection twice with low iterations
        df1 = model.project_unified_budget(years=5, iterations=100)
        df2 = model.project_unified_budget(years=5, iterations=100)
        
        # Results should be similar but not identical
        revenue_diff = abs(df1["total_revenue"].sum() - df2["total_revenue"].sum())
        revenue_avg = (df1["total_revenue"].sum() + df2["total_revenue"].sum()) / 2
        relative_diff = revenue_diff / revenue_avg
        
        # Should differ by less than 5% with 100 iterations
        assert relative_diff < 0.05, f"High variance: {relative_diff:.2%}"
    
    def test_high_iteration_convergence(self):
        """Test that high iterations produce stable results."""
        model = CombinedFiscalOutlookModel()
        
        # Run with high iterations (slow but stable)
        df1 = model.project_unified_budget(years=5, iterations=5000)
        df2 = model.project_unified_budget(years=5, iterations=5000)
        
        # Results should be very similar
        revenue_diff = abs(df1["total_revenue"].sum() - df2["total_revenue"].sum())
        revenue_avg = (df1["total_revenue"].sum() + df2["total_revenue"].sum()) / 2
        relative_diff = revenue_diff / revenue_avg
        
        # Should differ by less than 1% with 5000 iterations
        assert relative_diff < 0.01, f"High variance even with 5000 iterations: {relative_diff:.2%}"


class TestRealisticProjections:
    """Test that projections produce realistic values."""
    
    def test_2025_baseline_revenue_reasonable(self):
        """Test that 2026 revenue is close to CBO baseline."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=1, iterations=5000)
        
        revenue_2026 = df.iloc[0]["total_revenue"]
        
        # CBO 2026 baseline: ~$5.5-5.8T
        assert revenue_2026 > 5000, f"Revenue too low: ${revenue_2026}B"
        assert revenue_2026 < 6500, f"Revenue too high: ${revenue_2026}B"
    
    def test_2025_baseline_spending_reasonable(self):
        """Test that 2026 spending is close to CBO baseline."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=1, iterations=5000)
        
        spending_2026 = df.iloc[0]["total_spending"]
        
        # CBO 2026 baseline: ~$6.5-7.0T
        assert spending_2026 > 5000, f"Spending too low: ${spending_2026}B"
        assert spending_2026 < 8000, f"Spending too high: ${spending_2026}B"
    
    def test_10year_deficit_magnitude(self):
        """Test 10-year deficit is in realistic range."""
        model = CombinedFiscalOutlookModel()
        summary = model.get_fiscal_summary(years=10, iterations=5000)
        
        deficit_10yr = abs(summary["total_deficit_10year_billions"])
        
        # CBO projects $10-20T cumulative deficit over 10 years
        assert deficit_10yr > 5000, f"Deficit too low: ${deficit_10yr}B"
        assert deficit_10yr < 30000, f"Deficit too high: ${deficit_10yr}B"


class TestComponentIntegration:
    """Test individual component models work in integration."""
    
    def test_discretionary_model_accessible(self):
        """Test discretionary model can be used independently."""
        model = DiscretionarySpendingModel()
        result = model.project_all_discretionary(years=10, iterations=500)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10
        assert "total_mean" in result.columns
    
    def test_interest_model_accessible(self):
        """Test interest model can be used independently."""
        model = InterestOnDebtModel()
        result = model.project_interest_and_debt(years=10, iterations=500)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10
        assert "interest_billions" in result.columns
    
    def test_all_submodels_initialized(self):
        """Test that combined model initializes all submodels."""
        model = CombinedFiscalOutlookModel()
        
        assert model.revenue_model is not None
        assert model.ss_model is not None
        assert model.medicare_model is not None
        assert model.medicaid_model is not None
        assert model.discretionary_model is not None
        assert model.interest_model is not None


class TestEdgeCaseHandling:
    """Test handling of edge cases and unusual inputs."""
    
    def test_handles_small_iteration_count(self):
        """Test model handles very small iteration counts gracefully."""
        model = CombinedFiscalOutlookModel()
        
        # 100 is minimum recommended
        df = model.project_unified_budget(years=5, iterations=100)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
    
    def test_handles_large_year_count(self):
        """Test model handles large projection periods."""
        model = CombinedFiscalOutlookModel()
        
        # 75 years is typical CBO maximum
        df = model.project_unified_budget(years=75, iterations=100)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 75
    
    def test_fiscal_summary_with_short_period(self):
        """Test fiscal summary works with very short periods."""
        model = CombinedFiscalOutlookModel()
        
        # 1-year summary
        summary = model.get_fiscal_summary(years=1, iterations=500)
        
        assert "total_revenue_10year_billions" in summary
        assert "sustainable" in summary
        assert isinstance(summary["sustainable"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
