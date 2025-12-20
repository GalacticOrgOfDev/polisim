"""
Phase 2 Integration Tests - Social Security + Revenue + Combined Analysis
Tests cross-module integration and combined fiscal projections.

Test Coverage:
- Social Security module with different scenarios
- Revenue module with different economic scenarios  
- Combined fiscal outlook (SS + Revenue)
- Policy reform impact analysis
- Baseline validation against SSA/CBO
"""

import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path

from core.social_security import (
    SocialSecurityModel,
    SocialSecurityReforms,
    DemographicAssumptions,
    BenefitFormula,
    TrustFundAssumptions,
)
from core.revenue_modeling import (
    FederalRevenueModel,
    TaxReforms,
    IndividualIncomeTaxAssumptions,
    PayrollTaxAssumptions,
    CorporateIncomeTaxAssumptions,
)


class TestPhase2ConfigurationLoading:
    """Test that Phase 2 policy configuration files load correctly."""

    def test_social_security_scenarios_load(self):
        """Load Social Security scenarios from JSON."""
        config_path = Path("policies/social_security_scenarios.json")
        assert config_path.exists(), "Social Security scenarios file not found"
        
        with open(config_path) as f:
            config = json.load(f)
        
        assert "baseline" in config
        assert "scenarios" in config
        assert config["baseline"]["expected_outcomes"]["oasi_depletion_year"] == 2034
        assert "raise_payroll_tax" in config["scenarios"]
        assert "remove_wage_cap" in config["scenarios"]
        assert "raise_full_retirement_age" in config["scenarios"]
        assert "reduce_benefits" in config["scenarios"]
        assert "combined_reform_package" in config["scenarios"]

    def test_tax_reform_scenarios_load(self):
        """Load tax reform scenarios from JSON."""
        config_path = Path("policies/tax_reform_scenarios.json")
        assert config_path.exists(), "Tax reform scenarios file not found"
        
        with open(config_path) as f:
            config = json.load(f)
        
        assert "baseline" in config
        assert "scenarios" in config
        assert "increase_top_individual_rate" in config["scenarios"]
        assert "increase_corporate_rate" in config["scenarios"]
        assert "increase_payroll_tax" in config["scenarios"]
        assert "remove_ss_wage_cap" in config["scenarios"]
        assert "carbon_tax" in config["scenarios"]

    def test_revenue_scenarios_load(self):
        """Load revenue scenarios from JSON."""
        config_path = Path("policies/revenue_scenarios.json")
        assert config_path.exists(), "Revenue scenarios file not found"
        
        with open(config_path) as f:
            config = json.load(f)
        
        assert "baseline_2025" in config
        assert "scenarios" in config
        assert "baseline_current_law" in config["scenarios"]
        assert "recession_2026" in config["scenarios"]
        assert "strong_growth" in config["scenarios"]
        assert "demographic_challenge" in config["scenarios"]


class TestSocialSecurityReformScenarios:
    """Test Social Security reform scenarios from configuration."""

    def test_raise_payroll_tax_reform(self):
        """Test raise payroll tax scenario."""
        with open("policies/social_security_scenarios.json") as f:
            config = json.load(f)
        
        reform_config = config["scenarios"]["raise_payroll_tax"]
        assert reform_config["parameters"]["combined_payroll_tax_rate"] == 0.1350
        assert reform_config["expected_outcomes"]["oasi_depletion_year"] == 2046
        
        # Test with model
        model = SocialSecurityModel()
        baseline = model.project_trust_funds(years=30, iterations=1000)
        
        reforms = SocialSecurityReforms.raise_payroll_tax_rate(
            new_rate=reform_config["parameters"]["combined_payroll_tax_rate"]
        )
        reformed = model.apply_policy_reform(reforms["reforms"], baseline)
        
        # Verify reform extends solvency
        reformed_solvency = model.estimate_solvency_dates(reformed)
        assert reformed_solvency["OASI_depletion_year"] > 2034 + 8  # Should extend by ~10+ years

    def test_remove_wage_cap_reform(self):
        """Test remove wage cap scenario."""
        with open("policies/social_security_scenarios.json") as f:
            config = json.load(f)
        
        reform_config = config["scenarios"]["remove_wage_cap"]
        assert reform_config["parameters"]["wage_cap"] is None
        
        model = SocialSecurityModel()
        baseline = model.project_trust_funds(years=30, iterations=1000)
        
        reforms = SocialSecurityReforms.remove_social_security_wage_cap()
        reformed = model.apply_policy_reform(reforms["reforms"], baseline)
        
        reformed_solvency = model.estimate_solvency_dates(reformed)
        assert reformed_solvency["OASI_depletion_year"] > 2034 + 5

    def test_raise_fra_reform(self):
        """Test raise full retirement age scenario."""
        with open("policies/social_security_scenarios.json") as f:
            config = json.load(f)
        
        reform_config = config["scenarios"]["raise_full_retirement_age"]
        assert reform_config["parameters"]["full_retirement_age"] == 70
        
        model = SocialSecurityModel()
        baseline = model.project_trust_funds(years=30, iterations=1000)
        
        reforms = SocialSecurityReforms.raise_full_retirement_age(new_fra=70)
        reformed = model.apply_policy_reform(reforms["reforms"], baseline)
        
        reformed_solvency = model.estimate_solvency_dates(reformed)
        assert reformed_solvency["OASI_depletion_year"] > 2034 + 4

    def test_combined_reform_package(self):
        """Test combined reform package scenario."""
        with open("policies/social_security_scenarios.json") as f:
            config = json.load(f)
        
        reform_config = config["scenarios"]["combined_reform_package"]
        assert reform_config["expected_outcomes"]["75_year_solvency"] == True
        
        model = SocialSecurityModel()
        baseline = model.project_trust_funds(years=75, iterations=2000)
        
        reforms = SocialSecurityReforms.combined_reform()
        reformed = model.apply_policy_reform(reforms["reforms"], baseline)
        
        reformed_solvency = model.estimate_solvency_dates(reformed)
        # Combined reform should extend solvency significantly
        assert reformed_solvency["OASI_depletion_year"] > 2050


class TestTaxReformScenarios:
    """Test tax reform scenarios from configuration."""

    def test_increase_top_rate_reform(self):
        """Test increase top individual rate scenario."""
        with open("policies/tax_reform_scenarios.json") as f:
            config = json.load(f)
        
        reform_config = config["scenarios"]["increase_top_individual_rate"]
        assert reform_config["parameters"]["individual_income_tax_rate_top"] == 0.42
        
        model = FederalRevenueModel()
        baseline = model.project_all_revenues(years=10, iterations=1000)
        
        reforms = TaxReforms.increase_individual_income_tax_rate(new_rate=0.42)
        reformed = model.apply_tax_reform(reforms["reforms"], baseline)
        
        # Verify increased revenue
        assert reformed["total_revenues"].sum() > baseline["total_revenues"].sum()

    def test_increase_corporate_rate_reform(self):
        """Test increase corporate rate scenario."""
        with open("policies/tax_reform_scenarios.json") as f:
            config = json.load(f)
        
        reform_config = config["scenarios"]["increase_corporate_rate"]
        assert reform_config["parameters"]["corporate_tax_rate"] == 0.25
        
        model = FederalRevenueModel()
        baseline = model.project_all_revenues(years=10, iterations=1000)
        
        reforms = TaxReforms.increase_corporate_income_tax_rate(new_rate=0.25)
        reformed = model.apply_tax_reform(reforms["reforms"], baseline)
        
        assert reformed["total_revenues"].sum() > baseline["total_revenues"].sum()

    def test_remove_ss_cap_reform(self):
        """Test remove Social Security wage cap tax reform."""
        with open("policies/tax_reform_scenarios.json") as f:
            config = json.load(f)
        
        reform_config = config["scenarios"]["remove_ss_wage_cap"]
        assert reform_config["parameters"]["payroll_tax_cap_ss"] is None
        
        model = FederalRevenueModel()
        baseline = model.project_all_revenues(years=10, iterations=1000)
        
        reforms = TaxReforms.remove_social_security_wage_cap()
        reformed = model.apply_tax_reform(reforms["reforms"], baseline)
        
        # Revenue increase should be substantial (~$220B/year)
        revenue_increase = (reformed["total_revenues"].sum() - baseline["total_revenues"].sum()) / 10
        assert revenue_increase > 100  # At least $100B/year


class TestRevenueScenarios:
    """Test revenue projections under different economic scenarios."""

    def test_baseline_current_law(self):
        """Test baseline current law scenario."""
        with open("policies/revenue_scenarios.json") as f:
            config = json.load(f)
        
        scenario = config["scenarios"]["baseline_current_law"]
        assert scenario["economic_assumptions"]["gdp_real_growth_annual"][0] == 0.025
        assert scenario["revenue_projections"]["total_10yr_billions"] == 52000
        
        # Test projection
        model = FederalRevenueModel()
        gdp_growth = np.array(scenario["economic_assumptions"]["gdp_real_growth_annual"])
        wage_growth = np.array(scenario["economic_assumptions"]["wage_growth_annual"])
        
        revenues = model.project_all_revenues(years=10, gdp_growth=gdp_growth, wage_growth=wage_growth, iterations=1000)
        total = revenues["total_revenues"].sum()
        
        # Should be within 10% of baseline
        assert abs(total - scenario["revenue_projections"]["total_10yr_billions"]) < 5000

    def test_recession_scenario(self):
        """Test recession scenario."""
        with open("policies/revenue_scenarios.json") as f:
            config = json.load(f)
        
        scenario = config["scenarios"]["recession_2026"]
        assert scenario["economic_assumptions"]["gdp_real_growth_annual"][1] == 0.015  # Recovery
        assert scenario["economic_assumptions"]["gdp_real_growth_annual"][0] == -0.015  # Contraction
        
        model = FederalRevenueModel()
        gdp_growth = np.array(scenario["economic_assumptions"]["gdp_real_growth_annual"])
        wage_growth = np.array(scenario["economic_assumptions"]["wage_growth_annual"])
        
        revenues = model.project_all_revenues(years=10, gdp_growth=gdp_growth, wage_growth=wage_growth, iterations=1000)
        total = revenues["total_revenues"].sum()
        
        # Recession should produce lower revenues than baseline
        baseline_total = 52000  # From baseline scenario
        assert total < baseline_total

    def test_strong_growth_scenario(self):
        """Test strong growth scenario."""
        with open("policies/revenue_scenarios.json") as f:
            config = json.load(f)
        
        scenario = config["scenarios"]["strong_growth"]
        assert all(g >= 0.026 for g in scenario["economic_assumptions"]["gdp_real_growth_annual"])
        
        model = FederalRevenueModel()
        gdp_growth = np.array(scenario["economic_assumptions"]["gdp_real_growth_annual"])
        wage_growth = np.array(scenario["economic_assumptions"]["wage_growth_annual"])
        
        revenues = model.project_all_revenues(years=10, gdp_growth=gdp_growth, wage_growth=wage_growth, iterations=1000)
        total = revenues["total_revenues"].sum()
        
        # Strong growth should produce higher revenues
        baseline_total = 52000
        assert total > baseline_total


class TestCombinedFiscalOutlook:
    """Test combined fiscal projections (SS + Revenue + Healthcare)."""

    def test_combined_projections(self):
        """Test running SS and Revenue projections together."""
        ss_model = SocialSecurityModel()
        revenue_model = FederalRevenueModel()
        
        # Run both models
        ss_projections = ss_model.project_trust_funds(years=10, iterations=1000)
        revenue_projections = revenue_model.project_all_revenues(years=10, iterations=1000)
        
        # Verify both have data
        assert len(ss_projections) > 0
        assert len(revenue_projections) > 0
        assert ss_projections["year"].max() == 2034  # 2025 + 10 - 1
        assert revenue_projections["year"].max() == 2034

    def test_ss_revenue_integration(self):
        """Test that SS reform impacts on payroll tax are reflected in revenue."""
        ss_model = SocialSecurityModel()
        revenue_model = FederalRevenueModel()
        
        # Baseline
        baseline_ss = ss_model.project_trust_funds(years=10, iterations=500)
        baseline_revenue = revenue_model.project_all_revenues(years=10, iterations=500)
        
        # Extract payroll tax component from baseline
        baseline_payroll = baseline_revenue["social_security_tax"].sum()
        
        # Now apply SS reform (raise payroll tax)
        reforms = SocialSecurityReforms.raise_payroll_tax_rate(new_rate=0.145)
        reformed_ss = ss_model.apply_policy_reform(reforms["reforms"], baseline_ss)
        
        # Reformed payroll tax should increase revenue
        reformed_revenue = revenue_model.apply_tax_reform(
            TaxReforms.increase_payroll_tax_rate(new_rate=0.145)["reforms"],
            baseline_revenue
        )
        reformed_payroll = reformed_revenue["social_security_tax"].sum()
        
        assert reformed_payroll > baseline_payroll

    def test_fiscal_balance(self):
        """Test that revenues can be compared against spending (conceptual)."""
        revenue_model = FederalRevenueModel()
        
        revenues = revenue_model.project_all_revenues(years=10, iterations=500)
        
        # In a full fiscal model, revenues would be compared to:
        # Healthcare + SS + Medicare + Medicaid + Discretionary + Interest
        # For now, just verify revenue data is available
        assert "total_revenues" in revenues.columns
        assert revenues["total_revenues"].sum() > 0
        assert len(revenues) == 10  # 10 years of projections


class TestPhase2Validation:
    """Validation against official baselines."""

    def test_ss_baseline_validation(self):
        """Validate SS projections against SSA Trustees baseline."""
        model = SocialSecurityModel()
        projections = model.project_trust_funds(years=30, iterations=10000)
        solvency = model.estimate_solvency_dates(projections)
        
        # SSA 2024 Trustees baseline: OASI depletion 2034 ±1 year
        oasi_year = solvency["OASI_depletion_year"]
        assert 2033 <= oasi_year <= 2035, f"OASI depletion year {oasi_year} outside SSA baseline ±1 year"

    def test_revenue_baseline_validation(self):
        """Validate revenue projections against CBO baseline."""
        model = FederalRevenueModel()
        
        # Use baseline economic assumptions
        gdp_growth = np.full(10, 0.025)
        wage_growth = np.full(10, 0.03)
        
        revenues = model.project_all_revenues(years=10, gdp_growth=gdp_growth, wage_growth=wage_growth, iterations=5000)
        total = revenues["total_revenues"].mean()
        
        # CBO baseline: ~$52 trillion over 10 years
        # Allow ±15% margin
        assert 44000 < total < 60000, f"10-year total {total} outside reasonable range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
