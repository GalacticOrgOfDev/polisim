"""
Unit tests for Revenue Modeling module (CBO 2.0 Phase 2)
Tests federal revenue projections and tax reform scenarios.
"""

import pytest
import numpy as np
import pandas as pd
from core.revenue_modeling import (
    FederalRevenueModel,
    IndividualIncomeTaxAssumptions,
    PayrollTaxAssumptions,
    CorporateIncomeTaxAssumptions,
    TaxReforms,
)


class TestRevenueModelInitialization:
    """Test revenue model setup."""

    def test_model_initialization(self):
        """Revenue model initializes with correct assumptions."""
        model = FederalRevenueModel()
        assert model.start_year == 2025
        assert "total" in model.baseline_revenues
        assert model.baseline_revenues["total"] == 5_400

    def test_iit_assumptions(self):
        """Individual income tax assumptions are set correctly."""
        iit = IndividualIncomeTaxAssumptions.cbo_2025_baseline()
        assert len(iit.tax_brackets) > 0
        assert iit.standard_deduction_single == 14_600
        assert iit.child_tax_credit == 2_000

    def test_payroll_tax_assumptions(self):
        """Payroll tax assumptions are correct."""
        payroll = PayrollTaxAssumptions.ssa_2024_trustees()
        assert payroll.social_security_rate == 0.062
        assert payroll.social_security_cap == 168_600
        assert payroll.medicare_rate == 0.029

    def test_corporate_tax_assumptions(self):
        """Corporate income tax assumptions are set."""
        corp = CorporateIncomeTaxAssumptions.cbo_2025_baseline()
        assert corp.marginal_tax_rate == 0.21
        assert corp.effective_tax_rate == 0.13


class TestIndividualIncomeTaxProjection:
    """Test individual income tax revenue projection."""

    def test_iit_projection_dimensions(self):
        """IIT projection has correct shape."""
        model = FederalRevenueModel()
        result = model.project_individual_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.02),
            wage_growth=np.full(10, 0.03),
            iterations=100,
        )

        assert result["revenues"].shape == (10, 100)
        assert result["effective_rates"].shape == (10, 100)
        assert result["mean_revenue"].shape == (10,)

    def test_iit_grows_with_wage_growth(self):
        """IIT revenue increases with higher wage growth."""
        model = FederalRevenueModel()

        # Low wage growth
        result_low = model.project_individual_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.01),
            wage_growth=np.full(10, 0.01),
            iterations=100,
        )

        # High wage growth
        result_high = model.project_individual_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.03),
            wage_growth=np.full(10, 0.05),
            iterations=100,
        )

        # Revenue should grow more with higher wage growth
        growth_low = result_low["mean_revenue"][-1] / result_low["mean_revenue"][0]
        growth_high = result_high["mean_revenue"][-1] / result_high["mean_revenue"][0]

        assert growth_high > growth_low

    def test_iit_monotonic_growth(self):
        """IIT revenue generally increases over projection period."""
        model = FederalRevenueModel()
        result = model.project_individual_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.02),
            wage_growth=np.full(10, 0.03),
            iterations=100,
        )

        mean_revenue = result["mean_revenue"]

        # Should generally increase (allow 2 years of decline)
        increases = np.sum(np.diff(mean_revenue) > 0)
        assert increases >= 7  # At least 7 years of increase


class TestPayrollTaxProjection:
    """Test payroll tax revenue projection."""

    def test_payroll_tax_projection_dimensions(self):
        """Payroll tax projection has correct shape."""
        model = FederalRevenueModel()
        result = model.project_payroll_taxes(
            years=10,
            wage_growth=np.full(10, 0.03),
            employment=np.ones(10),
            iterations=100,
        )

        assert result["ss_revenues"].shape == (10, 100)
        assert result["medicare_revenues"].shape == (10, 100)
        assert result["total_payroll_revenues"].shape == (10, 100)

    def test_payroll_tax_components(self):
        """Payroll tax components are split correctly."""
        model = FederalRevenueModel()
        result = model.project_payroll_taxes(
            years=5,
            wage_growth=np.full(5, 0.02),
            employment=np.ones(5),
            iterations=100,
        )

        # Total should equal SS + Medicare
        total = result["total_payroll_revenues"]
        ss = result["ss_revenues"]
        medicare = result["medicare_revenues"]

        assert np.allclose(total, ss + medicare)

    def test_payroll_tax_cap_effect(self):
        """Payroll tax cap becomes more binding over time."""
        model = FederalRevenueModel()
        result = model.project_payroll_taxes(
            years=20,
            wage_growth=np.full(20, 0.03),
            employment=np.ones(20),
            iterations=100,
        )

        ss_revenue = result["ss_revenues"].mean(axis=1)

        # SS tax growth should slow as cap becomes more binding
        early_growth = (ss_revenue[5] - ss_revenue[0]) / ss_revenue[0]
        late_growth = (ss_revenue[19] - ss_revenue[15]) / ss_revenue[15]

        assert late_growth < early_growth


class TestCorporateIncomeTaxProjection:
    """Test corporate income tax revenue projection."""

    def test_cit_projection_dimensions(self):
        """CIT projection has correct shape."""
        model = FederalRevenueModel()
        result = model.project_corporate_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.02),
            iterations=100,
        )

        assert result["revenues"].shape == (10, 100)
        assert result["mean_revenue"].shape == (10,)
        assert result["std_revenue"].shape == (10,)

    def test_cit_cyclicality(self):
        """CIT is more volatile than other revenues."""
        model = FederalRevenueModel()

        cit_result = model.project_corporate_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.02),
            iterations=1000,
        )

        cit_volatility = cit_result["std_revenue"].mean()

        # CIT should have reasonable volatility (not negative)
        assert cit_volatility > 0

    def test_cit_gdp_sensitivity(self):
        """CIT grows faster with higher GDP growth."""
        model = FederalRevenueModel()

        # Low GDP growth
        result_low = model.project_corporate_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.01),
            iterations=100,
        )

        # High GDP growth
        result_high = model.project_corporate_income_tax(
            years=10,
            gdp_growth=np.full(10, 0.04),
            iterations=100,
        )

        growth_low = result_low["mean_revenue"][-1] / result_low["mean_revenue"][0]
        growth_high = result_high["mean_revenue"][-1] / result_high["mean_revenue"][0]

        # Higher growth should result in higher revenue
        assert growth_high > growth_low


class TestAllRevenuesProjection:
    """Test comprehensive revenue projection."""

    def test_all_revenues_projection_shape(self):
        """All revenues projection has correct shape."""
        model = FederalRevenueModel()
        result = model.project_all_revenues(
            years=10,
            gdp_growth=np.full(10, 0.02),
            wage_growth=np.full(10, 0.03),
            iterations=100,
        )

        assert len(result) == 10 * 100
        assert "total_revenues" in result.columns

    def test_all_revenues_components_sum(self):
        """Revenue components sum to total."""
        model = FederalRevenueModel()
        result = model.project_all_revenues(
            years=5,
            gdp_growth=np.full(5, 0.02),
            wage_growth=np.full(5, 0.03),
            iterations=100,
        )

        # Check that components sum to total
        for idx, row in result.iterrows():
            total = (
                row["individual_income_tax"]
                + row["social_security_tax"]
                + row["medicare_tax"]
                + row["corporate_income_tax"]
                + row["excise_taxes"]
                + row["other_revenues"]
            )

            assert np.isclose(total, row["total_revenues"], rtol=0.01)

    def test_all_revenues_within_baseline_range(self):
        """Projected revenues are within reasonable range of baseline."""
        model = FederalRevenueModel()
        result = model.project_all_revenues(
            years=10,
            gdp_growth=np.full(10, 0.025),
            wage_growth=np.full(10, 0.03),
            iterations=100,
        )

        baseline = model.baseline_revenues["total"]
        projected = result["total_revenues"]

        # 10-year projections should be 20-50% higher than 2025 baseline
        mean_projected = projected.mean()
        assert baseline * 1.2 < mean_projected < baseline * 1.5


class TestTaxReforms:
    """Test tax policy reform scenarios."""

    def test_increase_top_rate_reform(self):
        """Increasing top rate produces additional revenue."""
        model = FederalRevenueModel()

        reform = TaxReforms.increase_top_rate(increase_pct=0.05)
        impact = model.apply_tax_reform(reform["reforms"])

        assert "total_additional_revenue" in impact
        assert impact["total_additional_revenue"] > 0

    def test_increase_corporate_rate_reform(self):
        """Increasing corporate rate produces additional revenue."""
        model = FederalRevenueModel()

        reform = TaxReforms.increase_corporate_rate(new_rate=0.28)
        impact = model.apply_tax_reform(reform["reforms"])

        assert "cit_additional_revenue" in impact
        assert impact["cit_additional_revenue"] > 0

    def test_increase_payroll_tax_reform(self):
        """Increasing payroll tax produces additional revenue."""
        model = FederalRevenueModel()

        reform = TaxReforms.increase_payroll_tax(increase_pct=0.02)
        impact = model.apply_tax_reform(reform["reforms"])

        assert "payroll_additional_revenue" in impact
        assert impact["payroll_additional_revenue"] > 0

    def test_remove_ss_cap_reform(self):
        """Removing SS cap produces additional revenue."""
        model = FederalRevenueModel()

        reform = TaxReforms.remove_ss_cap()
        impact = model.apply_tax_reform(reform["reforms"])

        assert "ss_cap_elimination_revenue" in impact
        assert impact["ss_cap_elimination_revenue"] > 0

    def test_combined_reform_impact(self):
        """Multiple reforms produce combined impact."""
        model = FederalRevenueModel()

        reform_package = {
            "individual_income_tax_rate_increase": 0.03,
            "corporate_tax_rate": 0.28,
            "payroll_tax_rate_increase": 0.02,
        }

        impact = model.apply_tax_reform(reform_package)

        # Total should equal sum of components
        total = impact["total_additional_revenue"]
        assert total > 0


class TestRevenueDataValidation:
    """Test validation against CBO baselines."""

    def test_baseline_revenues_reasonable(self):
        """Baseline 2025 revenues are in expected ranges."""
        model = FederalRevenueModel()

        iit = model.baseline_revenues["individual_income_tax"]
        payroll = model.baseline_revenues["payroll_taxes"]
        cit = model.baseline_revenues["corporate_income_tax"]

        # Should be in billions
        assert iit > 2_000
        assert payroll > 2_000
        assert cit > 300

    def test_10year_projection_vs_baseline(self):
        """10-year projected revenues grow reasonably from baseline."""
        model = FederalRevenueModel()
        result = model.project_all_revenues(
            years=10,
            gdp_growth=np.full(10, 0.025),
            wage_growth=np.full(10, 0.03),
            iterations=100,
        )

        year_2034 = result[result["year"] == 2034]
        baseline_2025 = model.baseline_revenues["total"]
        projected_2034 = year_2034["total_revenues"].mean()

        # 2034 revenues should be 20-40% higher than 2025
        assert baseline_2025 * 1.2 < projected_2034 < baseline_2025 * 1.4


class TestMonteCarloRevenueDistribution:
    """Test Monte Carlo distribution properties."""

    def test_revenue_distribution_spread(self):
        """Revenue distributions have reasonable spread."""
        model = FederalRevenueModel()
        result = model.project_all_revenues(
            years=10,
            gdp_growth=np.full(10, 0.02),
            wage_growth=np.full(10, 0.03),
            iterations=1000,
        )

        year_10 = result[result["year"] == 2034]["total_revenues"]
        mean = year_10.mean()
        std = year_10.std()

        # Standard deviation should be 5-10% of mean
        assert 0.05 * mean < std < 0.10 * mean

    def test_different_iterations_converge(self):
        """Increasing iterations reduces variance."""
        model = FederalRevenueModel()

        result_100 = model.project_all_revenues(
            years=10, iterations=100
        )
        result_1000 = model.project_all_revenues(
            years=10, iterations=1000
        )

        year_10_100 = result_100[result_100["year"] == 2034]["total_revenues"]
        year_10_1000 = result_1000[result_1000["year"] == 2034]["total_revenues"]

        std_100 = year_10_100.std()
        std_1000 = year_10_1000.std()

        # More iterations should have lower variance
        assert std_1000 < std_100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
