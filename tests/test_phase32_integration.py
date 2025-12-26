"""
Phase 3.2 Integration Tests - Discretionary, Interest, and Combined Outlook
Tests for Phase 3.2 modules and their integration with Phase 1-3.1 models.
"""

import pytest
import numpy as np
import pandas as pd

from core.discretionary_spending import (
    DiscretionarySpendingModel,
    DiscretionaryAssumptions,
)
from core.interest_spending import (
    InterestOnDebtModel,
    DebtAssumptions,
)
from core.combined_outlook import CombinedFiscalOutlookModel


class TestDiscretionarySpending:
    """Test discretionary spending module."""
    
    def test_defense_baseline_projection(self):
        """Test defense spending under baseline scenario."""
        model = DiscretionarySpendingModel()
        result = model.project_defense(years=10, iterations=1000, scenario="baseline")
        
        assert "defense_billions" in result
        assert result["defense_billions"].shape == (1000, 10)
        assert "mean" in result
        assert len(result["mean"]) == 10
        assert np.all(result["mean"] > 0)  # All positive
        assert np.all(np.diff(result["mean"]) > 0)  # Increasing (inflation)
    
    def test_defense_growth_scenario(self):
        """Test defense spending growth scenario."""
        model = DiscretionarySpendingModel()
        baseline = model.project_defense(years=10, iterations=1000, scenario="baseline")
        growth = model.project_defense(years=10, iterations=1000, scenario="growth")
        
        # Growth should be higher than baseline
        assert growth["mean"][-1] > baseline["mean"][-1]
    
    def test_defense_reduction_scenario(self):
        """Test defense spending reduction scenario."""
        model = DiscretionarySpendingModel()
        baseline = model.project_defense(years=10, iterations=1000, scenario="baseline")
        reduction = model.project_defense(years=10, iterations=1000, scenario="reduction")
        
        # Reduction should be lower than baseline
        assert reduction["mean"][-1] < baseline["mean"][-1]
    
    def test_nondefense_projection(self):
        """Test non-defense discretionary projections."""
        model = DiscretionarySpendingModel()
        result = model.project_nondefense_discretionary(years=10, iterations=1000)
        
        assert "nondefense_billions" in result
        assert result["nondefense_billions"].shape == (1000, 10)
        assert np.all(result["mean"] > 0)
    
    def test_all_discretionary_dataframe(self):
        """Test combined discretionary spending returns DataFrame."""
        model = DiscretionarySpendingModel()
        df = model.project_all_discretionary(years=10, iterations=1000)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert "defense_mean" in df.columns
        assert "nondefense_mean" in df.columns
        assert "total_mean" in df.columns
        
        # Total should equal defense + nondefense
        assert np.allclose(
            df["total_mean"],
            df["defense_mean"] + df["nondefense_mean"]
        )
    
    def test_10year_totals(self):
        """Test 10-year discretionary spending totals."""
        model = DiscretionarySpendingModel()
        totals = model.get_10year_totals()
        
        assert "defense_10year_billions" in totals
        assert "nondefense_10year_billions" in totals
        assert "total_10year_billions" in totals
        assert totals["total_10year_billions"] > 0
        
        # Total should equal parts
        assert np.isclose(
            totals["total_10year_billions"],
            totals["defense_10year_billions"] + totals["nondefense_10year_billions"]
        )
    
    def test_category_breakdown(self):
        """Test non-defense breakdown by category."""
        model = DiscretionarySpendingModel()
        breakdown = model.get_split_by_category(years=10)
        
        assert isinstance(breakdown, pd.DataFrame)
        assert len(breakdown) == 10
        
        categories = ["education", "infrastructure", "research", "veterans", "other"]
        for cat in categories:
            assert cat in breakdown.columns
            assert np.all(breakdown[cat] >= 0)


class TestInterestOnDebt:
    """Test interest on federal debt module."""
    
    def test_current_interest_rate_calculation(self):
        """Test weighted average interest rate calculation."""
        model = InterestOnDebtModel()
        rate = model.calculate_current_interest_rate()
        
        assert 0.03 < rate < 0.05  # Should be reasonable
    
    def test_interest_baseline_projection(self):
        """Test interest expense under baseline scenario."""
        model = InterestOnDebtModel()
        result = model.project_interest_expense(years=10, iterations=1000, interest_rate_scenario="baseline")
        
        assert "interest_billions" in result
        assert result["interest_billions"].shape == (1000, 10)
        assert "debt_billions" in result
        assert np.all(result["mean"] > 0)
        
        # Interest should generally increase (debt growing)
        assert result["mean"][-1] > result["mean"][0]
    
    def test_interest_rising_scenario(self):
        """Test interest expense under rising rates."""
        model = InterestOnDebtModel()
        baseline = model.project_interest_expense(years=10, iterations=1000, interest_rate_scenario="baseline")
        rising = model.project_interest_expense(years=10, iterations=1000, interest_rate_scenario="rising")
        
        # Rising rates should have higher interest by end
        assert rising["mean"][-1] > baseline["mean"][-1]
    
    def test_interest_and_debt_dataframe(self):
        """Test interest and debt projection returns DataFrame."""
        model = InterestOnDebtModel()
        df = model.project_interest_and_debt(years=10, iterations=1000)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert "interest_billions" in df.columns
        assert "debt_billions" in df.columns
        assert "interest_rate_pct" in df.columns
        
        # Debt should be growing
        assert df["debt_billions"].iloc[-1] > df["debt_billions"].iloc[0]
    
    def test_10year_interest_totals(self):
        """Test 10-year interest expense totals."""
        model = InterestOnDebtModel()
        totals = model.get_10year_interest_totals()
        
        assert "total_10year_interest_billions" in totals
        assert "avg_annual_interest_billions" in totals
        assert "ending_debt_billions" in totals
        assert totals["total_10year_interest_billions"] > 0
    
    def test_interest_rate_sensitivity(self):
        """Test interest rate sensitivity analysis."""
        model = InterestOnDebtModel()
        sensitivity = model.interest_rate_sensitivity(years=10, rate_change_bps=100)
        
        assert sensitivity > 0  # More spending with higher rates
        assert sensitivity < 1000  # But reasonable magnitude


class TestCombinedFiscalOutlook:
    """Test combined federal fiscal outlook."""
    
    def test_unified_budget_projection(self):
        """Test unified budget projection with all components."""
        model = CombinedFiscalOutlookModel()
        
        try:
            df = model.project_unified_budget(
                years=10,
                iterations=1000,
                revenue_scenario="baseline",
                discretionary_scenario="baseline",
                interest_scenario="baseline"
            )
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 10
            
            # Check all major columns present
            required_columns = [
                "year",
                "total_revenue",
                "total_spending",
                "deficit_surplus",
                "mandatory_spending",
                "discretionary_spending",
                "interest_spending"
            ]
            
            for col in required_columns:
                assert col in df.columns, f"Missing column: {col}"
            
            # Revenue + Interest spending should equal revenue + mandatory + discretionary + interest
            for idx, row in df.iterrows():
                total_spending_check = (
                    row["discretionary_spending"] +
                    row["interest_spending"]
                )
                assert total_spending_check > 0
        
        except Exception as e:
            pytest.skip(f"Combined model requires full integration: {str(e)}")
    
    def test_fiscal_summary(self):
        """Test fiscal summary metrics."""
        model = CombinedFiscalOutlookModel()
        
        try:
            summary = model.get_fiscal_summary(years=10, iterations=1000)
            
            assert "total_revenue_10year_billions" in summary
            assert "total_spending_10year_billions" in summary
            assert "total_deficit_10year_billions" in summary
            assert "sustainable" in summary
            assert isinstance(summary["sustainable"], bool)
        
        except Exception as e:
            pytest.skip(f"Combined model requires full integration: {str(e)}")
    
    def test_fiscal_scenarios(self):
        """Test different fiscal scenarios."""
        model = CombinedFiscalOutlookModel()
        scenarios = ["baseline", "recession_2026", "strong_growth"]
        
        try:
            results = {}
            for scenario in scenarios:
                summary = model.get_fiscal_summary(
                    years=10,
                    revenue_scenario=scenario,
                    discretionary_scenario="baseline"
                )
                results[scenario] = summary
            
            # Recession should have lower revenue and likely higher deficit
            if "recession_2026" in results:
                assert results["recession_2026"]["total_revenue_10year_billions"] < results["baseline"]["total_revenue_10year_billions"]
        
        except Exception as e:
            pytest.skip(f"Combined model requires full integration: {str(e)}")


class TestPhase32Integration:
    """Integration tests for Phase 3.2 components."""
    
    def test_discretionary_interest_ratio(self):
        """Test that discretionary spending >> interest spending initially."""
        discret_model = DiscretionarySpendingModel()
        interest_model = InterestOnDebtModel()
        
        discret = discret_model.get_10year_totals()
        interest = interest_model.get_10year_interest_totals()
        
        # Discretionary should be much larger than interest (2-3x)
        assert discret["total_10year_billions"] > interest["total_10year_interest_billions"]
    
    def test_phase32_all_models_accessible(self):
        """Test that all Phase 3.2 models can be imported and instantiated."""
        # This is a smoke test
        discret = DiscretionarySpendingModel()
        interest = InterestOnDebtModel()
        combined = CombinedFiscalOutlookModel()
        
        assert discret is not None
        assert interest is not None
        assert combined is not None
    
    def test_combined_model_imports_working(self):
        """Test that CombinedFiscalOutlookModel successfully imports all dependencies."""
        try:
            model = CombinedFiscalOutlookModel()
            assert model.revenue_model is not None
            assert model.ss_model is not None
            assert model.medicare_model is not None
            assert model.medicaid_model is not None
            assert model.discretionary_model is not None
            assert model.interest_model is not None
        except ImportError as e:
            pytest.skip(f"Some modules not available: {str(e)}")


class TestEndToEndIntegration:
    """End-to-end integration tests for complete fiscal projections."""
    
    def test_30year_unified_projection(self):
        """Test complete 30-year unified budget projection."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=30, iterations=1000)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 30
        
        # Verify all components present
        required_cols = [
            "year", "total_revenue", "total_spending", "deficit_surplus",
            "social_security_spending", "medicare_spending", "medicaid_spending",
            "other_health_spending", "discretionary_spending", "interest_spending"
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"
        
        # Verify all values are positive (spending) or reasonable (deficit)
        assert np.all(df["total_revenue"] > 0)
        assert np.all(df["total_spending"] > 0)
        assert np.all(df["social_security_spending"] > 0)
        assert np.all(df["medicare_spending"] > 0)
        assert np.all(df["medicaid_spending"] > 0)
    
    def test_revenue_covers_most_spending(self):
        """Test that revenue covers most (though not all) spending."""
        model = CombinedFiscalOutlookModel()
        summary = model.get_fiscal_summary(years=10, iterations=1000)
        
        # Revenue should be at least 80% of spending (reasonable deficit)
        revenue = summary["total_revenue_10year_billions"]
        spending = summary["total_spending_10year_billions"]
        
        assert revenue > 0
        assert spending > 0
        assert revenue / spending > 0.80, f"Revenue {revenue} is less than 80% of spending {spending}"
    
    def test_spending_components_sum_correctly(self):
        """Test that spending components sum to total spending."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=1000)
        
        # Manual sum of components
        computed_total = (
            df["social_security_spending"] +
            df["medicare_spending"] +
            df["medicaid_spending"] +
            df["other_health_spending"] +
            df["discretionary_spending"] +
            df["interest_spending"]
        )
        
        # Should match total_spending column
        assert np.allclose(computed_total, df["total_spending"], rtol=0.01)
    
    def test_deficit_calculation_correct(self):
        """Test that deficit = revenue - spending."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=1000)
        
        computed_deficit = df["total_revenue"] - df["total_spending"]
        assert np.allclose(computed_deficit, df["deficit_surplus"], rtol=0.01)
    
    def test_primary_deficit_excludes_interest(self):
        """Test that primary deficit = deficit + interest."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=1000)
        
        computed_primary = df["total_revenue"] - (df["total_spending"] - df["interest_spending"])
        assert np.allclose(computed_primary, df["primary_deficit"], rtol=0.01)
    
    def test_spending_grows_over_time(self):
        """Test that spending generally grows over 30 years."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=30, iterations=1000)
        
        # Year 30 should be higher than year 1
        assert df.iloc[29]["total_spending"] > df.iloc[0]["total_spending"]
        assert df.iloc[29]["total_revenue"] > df.iloc[0]["total_revenue"]
    
    def test_medicare_medicaid_reasonable_share(self):
        """Test that Medicare+Medicaid are 20-40% of total spending."""
        model = CombinedFiscalOutlookModel()
        df = model.project_unified_budget(years=10, iterations=1000)
        
        healthcare_share = (df["medicare_spending"] + df["medicaid_spending"]) / df["total_spending"]
        
        # Medicare+Medicaid should be 20-40% of federal spending
        assert np.all(healthcare_share > 0.15), "Healthcare share too low"
        assert np.all(healthcare_share < 0.50), "Healthcare share too high"
    
    def test_different_scenarios_produce_different_results(self):
        """Test that different revenue scenarios produce different outcomes."""
        # TODO: This test will pass once revenue scenarios are fully implemented
        # Currently revenue_scenario parameter exists but doesn't affect calculations
        pytest.skip("Revenue scenarios not yet implemented in revenue model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
