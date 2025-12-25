"""
Tests for Social Security Enhanced Features (Phase 2A Day 3-4).

Tests means testing, longevity indexing, dynamic COLA,
progressive taxation, and benefit phaseouts.
"""

import pytest
import numpy as np
import pandas as pd
from core.social_security import (
    SocialSecurityModel,
    SocialSecurityReforms,
    DemographicAssumptions,
    BenefitFormula,
    TrustFundAssumptions,
)


class TestMeansTesting:
    """Test means testing functionality."""
    
    def test_means_testing_no_reduction_below_threshold(self):
        """Benefits unchanged below first threshold."""
        model = SocialSecurityModel()
        benefit = 2000.0
        income = 50_000.0
        
        adjusted = model.apply_means_testing(
            benefit, income, threshold_1=85_000, threshold_2=150_000
        )
        
        assert adjusted == benefit
    
    def test_means_testing_tier_1_reduction(self):
        """Partial reduction between thresholds."""
        model = SocialSecurityModel()
        benefit = 24000.0  # Annual benefit ($2k/month × 12)
        income = 100_000.0  # $15k over threshold_1
        
        adjusted = model.apply_means_testing(
            benefit,
            income,
            threshold_1=85_000,
            threshold_2=150_000,
            reduction_rate_1=0.25,
        )
        
        # Expected: $15k excess × 0.25 = $3,750 reduction
        expected_reduction = 15_000 * 0.25
        expected = benefit - expected_reduction
        assert adjusted == pytest.approx(expected, abs=1)
        assert adjusted > 0  # Should not be negative
    
    def test_means_testing_tier_2_reduction(self):
        """Higher reduction above second threshold."""
        model = SocialSecurityModel()
        benefit = 30_000.0  # Annual benefit
        income = 200_000.0
        
        adjusted = model.apply_means_testing(
            benefit,
            income,
            threshold_1=85_000,
            threshold_2=150_000,
            reduction_rate_1=0.25,
            reduction_rate_2=0.50,
        )
        
        # Tier 1: (150k - 85k) × 0.25 = $16,250
        # Tier 2: (200k - 150k) × 0.50 = $25,000
        # Total reduction: $41,250
        tier_1_reduction = (150_000 - 85_000) * 0.25
        tier_2_reduction = (200_000 - 150_000) * 0.50
        expected = benefit - (tier_1_reduction + tier_2_reduction)
        
        assert adjusted == pytest.approx(max(0, expected), abs=1)
    
    def test_means_testing_cannot_go_negative(self):
        """Benefits cannot be reduced below zero."""
        model = SocialSecurityModel()
        benefit = 1000.0
        income = 500_000.0  # Very high income
        
        adjusted = model.apply_means_testing(benefit, income)
        
        assert adjusted >= 0
    
    def test_means_testing_reform_method(self):
        """Test means testing reform factory method."""
        reform = SocialSecurityReforms.apply_means_testing_reform(
            threshold_1=100_000,
            threshold_2=200_000,
            reduction_rate_1=0.30,
            reduction_rate_2=0.60,
        )
        
        assert reform["name"] == "means_testing"
        assert reform["reforms"]["means_test_threshold_1"] == 100_000
        assert reform["reforms"]["means_test_reduction_rate_2"] == 0.60


class TestBenefitPhaseouts:
    """Test benefit phaseout functionality."""
    
    def test_phaseout_below_start(self):
        """No reduction below phaseout start."""
        model = SocialSecurityModel()
        benefit = 2000.0
        income = 50_000.0
        
        adjusted = model.calculate_benefit_phaseout(
            benefit, income, phaseout_start=75_000, phaseout_end=150_000
        )
        
        assert adjusted == benefit
    
    def test_phaseout_above_end(self):
        """Full phaseout above end threshold."""
        model = SocialSecurityModel()
        benefit = 2000.0
        income = 200_000.0
        
        adjusted = model.calculate_benefit_phaseout(
            benefit, income, phaseout_start=75_000, phaseout_end=150_000
        )
        
        assert adjusted == 0.0
    
    def test_phaseout_midpoint(self):
        """Partial phaseout in middle of range."""
        model = SocialSecurityModel()
        benefit = 2000.0
        income = 112_500.0  # Halfway between 75k and 150k
        
        adjusted = model.calculate_benefit_phaseout(
            benefit, income, phaseout_start=75_000, phaseout_end=150_000
        )
        
        # At midpoint, should be 50% phased out
        expected = benefit * 0.5
        assert adjusted == pytest.approx(expected, abs=1)
    
    def test_tiered_benefit_reduction(self):
        """Test income bracket-based reductions."""
        model = SocialSecurityModel()
        benefit = 2000.0
        
        reduction_schedule = {
            "Q1": 0.0,   # No reduction for lowest quintile
            "Q2": 0.05,  # 5% reduction
            "Q3": 0.10,  # 10% reduction
            "Q4": 0.15,  # 15% reduction
            "Q5": 0.25,  # 25% reduction for highest quintile
        }
        
        # Test Q1 (no reduction)
        q1_benefit = model.apply_tiered_benefit_reduction(benefit, "Q1", reduction_schedule)
        assert q1_benefit == benefit
        
        # Test Q5 (25% reduction)
        q5_benefit = model.apply_tiered_benefit_reduction(benefit, "Q5", reduction_schedule)
        assert q5_benefit == benefit * 0.75


class TestLongevityIndexing:
    """Test longevity indexing functionality."""
    
    def test_cohort_life_expectancy_tracking(self):
        """Life expectancy increases over time."""
        model = SocialSecurityModel()
        
        le_2025 = model.track_cohort_life_expectancy(1960, 2025)
        le_2035 = model.track_cohort_life_expectancy(1960, 2035)
        
        # Life expectancy should increase
        assert le_2035 > le_2025
    
    def test_longevity_indexing_disabled(self):
        """No adjustment when longevity indexing disabled."""
        model = SocialSecurityModel()
        model.benefit_formula.longevity_indexing_enabled = False
        
        benefit = 2000.0
        adjusted = model.apply_longevity_indexing(benefit, birth_year=1960, current_year=2035)
        
        assert adjusted == benefit
    
    def test_longevity_indexing_enabled(self):
        """Benefits reduced when longevity increases."""
        model = SocialSecurityModel()
        model.benefit_formula.longevity_indexing_enabled = True
        model.benefit_formula.baseline_life_expectancy_at_65 = 19.5
        
        benefit = 2000.0
        current_year = 2035  # 10 years after baseline
        
        adjusted = model.apply_longevity_indexing(benefit, birth_year=1960, current_year=current_year)
        
        # With increasing life expectancy, benefit should be reduced
        assert adjusted < benefit
    
    def test_actuarial_adjustment(self):
        """Actuarial adjustment maintains lifetime benefit neutrality."""
        model = SocialSecurityModel()
        benefit = 2000.0
        
        # If life expectancy doubles, monthly benefit halves
        adjusted = model.calculate_actuarial_adjustment(
            benefit, expected_years_receiving=39.0, baseline_years=19.5
        )
        
        expected = benefit * 0.5
        assert adjusted == pytest.approx(expected, abs=1)
    
    def test_longevity_indexing_reform_method(self):
        """Test longevity indexing reform factory method."""
        reform = SocialSecurityReforms.enable_longevity_indexing()
        
        assert reform["name"] == "longevity_indexing"
        assert reform["reforms"]["longevity_indexing_enabled"] is True


class TestDynamicCOLA:
    """Test dynamic COLA adjustments."""
    
    def test_cola_cpi_w(self):
        """Standard CPI-W COLA (current law)."""
        model = SocialSecurityModel()
        benefit = 2000.0
        cpi_change = 0.03  # 3% inflation
        
        new_benefit = model.calculate_dynamic_cola(
            benefit, cpi_change, wage_growth=0.025, cola_formula="cpi_w"
        )
        
        # Should apply 3% increase
        expected = benefit * 1.03
        assert new_benefit == pytest.approx(expected, abs=1)
    
    def test_cola_cpi_e(self):
        """CPI-E COLA (elderly inflation, higher)."""
        model = SocialSecurityModel()
        benefit = 2000.0
        cpi_change = 0.03
        
        new_benefit = model.calculate_dynamic_cola(
            benefit, cpi_change, wage_growth=0.025, cola_formula="cpi_e"
        )
        
        # CPI-E is ~20% higher
        # 3% × 1.2 = 3.6%
        expected = benefit * 1.036
        assert new_benefit == pytest.approx(expected, abs=1)
    
    def test_cola_chained_cpi(self):
        """Chained CPI COLA (lower, accounts for substitution)."""
        model = SocialSecurityModel()
        benefit = 2000.0
        cpi_change = 0.03
        
        new_benefit = model.calculate_dynamic_cola(
            benefit, cpi_change, wage_growth=0.025, cola_formula="chained_cpi"
        )
        
        # Chained CPI is ~10% lower
        # 3% × 0.9 = 2.7%
        expected = benefit * 1.027
        assert new_benefit == pytest.approx(expected, abs=1)
    
    def test_cola_with_floor(self):
        """COLA cannot go below minimum."""
        model = SocialSecurityModel()
        model.benefit_formula.cola_min = 0.01  # 1% floor
        model.benefit_formula.cola_max = 0.05  # 5% cap
        
        benefit = 2000.0
        inflation = -0.02  # Deflation
        
        new_benefit = model.apply_cola_with_limits(benefit, inflation)
        
        # Should apply 1% floor
        expected = benefit * 1.01
        assert new_benefit == pytest.approx(expected, abs=1)
    
    def test_cola_with_cap(self):
        """COLA cannot exceed maximum."""
        model = SocialSecurityModel()
        model.benefit_formula.cola_min = 0.0
        model.benefit_formula.cola_max = 0.03  # 3% cap
        
        benefit = 2000.0
        inflation = 0.10  # High inflation
        
        new_benefit = model.apply_cola_with_limits(benefit, inflation)
        
        # Should apply 3% cap
        expected = benefit * 1.03
        assert new_benefit == pytest.approx(expected, abs=1)
    
    def test_cola_formula_reform_method(self):
        """Test COLA formula reform factory method."""
        reform = SocialSecurityReforms.change_cola_formula("chained_cpi")
        
        assert reform["name"] == "change_cola_formula"
        assert reform["reforms"]["cola_formula"] == "chained_cpi"
    
    def test_cola_limits_reform_method(self):
        """Test COLA limits reform factory method."""
        reform = SocialSecurityReforms.apply_cola_limits(min_cola=0.01, max_cola=0.04)
        
        assert reform["name"] == "cola_limits"
        assert reform["reforms"]["cola_min"] == 0.01
        assert reform["reforms"]["cola_max"] == 0.04


class TestProgressiveTaxation:
    """Test progressive payroll tax functionality."""
    
    def test_progressive_tax_below_threshold(self):
        """Only base rate applies below threshold."""
        model = SocialSecurityModel()
        earnings = 100_000.0
        
        tax = model.apply_progressive_payroll_tax(
            earnings, base_rate=0.062, threshold=250_000, additional_rate=0.05
        )
        
        expected = earnings * 0.062
        assert tax == pytest.approx(expected, abs=1)
    
    def test_progressive_tax_above_threshold(self):
        """Additional rate applies above threshold."""
        model = SocialSecurityModel()
        earnings = 300_000.0
        
        tax = model.apply_progressive_payroll_tax(
            earnings, base_rate=0.062, threshold=250_000, additional_rate=0.05
        )
        
        # Base: $250k × 6.2% = $15,500
        # Additional: $50k × (6.2% + 5%) = $50k × 11.2% = $5,600
        # Total: $21,100
        expected = (250_000 * 0.062) + (50_000 * 0.112)
        assert tax == pytest.approx(expected, abs=1)
    
    def test_self_employment_tax(self):
        """Self-employment tax with special rules."""
        model = SocialSecurityModel()
        net_earnings = 100_000.0
        
        se_tax = model.calculate_self_employment_tax(net_earnings)
        
        # 92.35% of earnings subject to tax
        # 15.3% rate (12.4% SS + 2.9% Medicare)
        expected = net_earnings * 0.9235 * 0.153
        assert se_tax == pytest.approx(expected, abs=1)
    
    def test_self_employment_tax_with_cap(self):
        """SE tax respects wage base cap."""
        model = SocialSecurityModel()
        net_earnings = 200_000.0
        wage_base = 168_600.0
        
        se_tax = model.calculate_self_employment_tax(net_earnings, wage_base)
        
        # Only up to wage_base is taxed
        expected = wage_base * 0.153
        assert se_tax == pytest.approx(expected, abs=10)
    
    def test_gradual_tax_increase_before_start(self):
        """Rate unchanged before phase-in starts."""
        model = SocialSecurityModel()
        
        rate = model.apply_gradual_tax_increase(
            current_year=2024,
            start_year=2026,
            end_year=2036,
            initial_rate=0.124,
            target_rate=0.150,
        )
        
        assert rate == 0.124
    
    def test_gradual_tax_increase_after_end(self):
        """Target rate after phase-in completes."""
        model = SocialSecurityModel()
        
        rate = model.apply_gradual_tax_increase(
            current_year=2040,
            start_year=2026,
            end_year=2036,
            initial_rate=0.124,
            target_rate=0.150,
        )
        
        assert rate == 0.150
    
    def test_gradual_tax_increase_midpoint(self):
        """Halfway through phase-in."""
        model = SocialSecurityModel()
        
        rate = model.apply_gradual_tax_increase(
            current_year=2031,  # 5 years into 10-year phase-in
            start_year=2026,
            end_year=2036,
            initial_rate=0.124,
            target_rate=0.150,
        )
        
        # At midpoint: 12.4% + 50% of (15.0% - 12.4%)
        expected = 0.124 + 0.5 * (0.150 - 0.124)
        assert rate == pytest.approx(expected, abs=0.001)
    
    def test_progressive_tax_reform_method(self):
        """Test progressive tax reform factory method."""
        reform = SocialSecurityReforms.progressive_payroll_tax(
            threshold=300_000, additional_rate=0.06
        )
        
        assert reform["name"] == "progressive_payroll_tax"
        assert reform["reforms"]["progressive_tax_threshold"] == 300_000
        assert reform["reforms"]["progressive_additional_rate"] == 0.06


class TestEnhancedIntegration:
    """Test integration of enhanced features."""
    
    def test_benefit_formula_with_enhancements(self):
        """BenefitFormula includes enhancement parameters."""
        formula = BenefitFormula()
        
        assert hasattr(formula, "means_test_threshold_1")
        assert hasattr(formula, "longevity_indexing_enabled")
        assert hasattr(formula, "cola_formula")
        assert hasattr(formula, "cola_min")
        assert hasattr(formula, "cola_max")
    
    def test_combined_enhancements(self):
        """Multiple enhancements work together."""
        model = SocialSecurityModel()
        model.benefit_formula.longevity_indexing_enabled = True
        
        # Start with base benefit (annual)
        benefit = 24000.0  # $2k/month × 12
        
        # Apply longevity indexing
        benefit = model.apply_longevity_indexing(benefit, birth_year=1960, current_year=2035)
        
        # Apply means testing with moderate income
        benefit = model.apply_means_testing(benefit, total_income=75_000)  # Below threshold
        
        # Apply COLA
        benefit = model.calculate_dynamic_cola(benefit, cpi_change=0.03, wage_growth=0.025)
        
        # Should still be positive
        assert benefit > 0
        
        # Longevity indexing reduces, but COLA increases
        # Net effect depends on parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
