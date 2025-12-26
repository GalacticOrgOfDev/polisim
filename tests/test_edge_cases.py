"""
Tests for Edge Case Handlers
Tests safeguards for extreme scenarios and edge cases.
"""

import pytest
import numpy as np
import warnings
from core.edge_case_handlers import (
    EdgeCaseHandler,
    EdgeCaseError,
    safe_percentage_of_gdp,
    safe_per_capita
)


class TestRecessionGDPGrowth:
    """Test Edge Case #1: Zero/negative GDP growth"""
    
    def test_normal_growth(self):
        """Normal growth should pass through unchanged"""
        growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(0.02)
        assert growth == 0.02
        assert adjusted is False
    
    def test_zero_growth(self):
        """Zero growth should be allowed"""
        growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(0.0)
        assert growth == 0.0
        assert adjusted is False
    
    def test_moderate_recession(self):
        """Moderate recession (-3%) should be allowed"""
        growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(-0.03)
        assert growth == -0.03
        assert adjusted is False
    
    def test_severe_recession(self):
        """Severe recession (-10%) should be allowed but within range"""
        growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(-0.10)
        assert growth == -0.10
        assert adjusted is False
    
    def test_extreme_contraction(self):
        """Extreme contraction worse than Great Depression should be capped"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(-0.20, year=2026)
            assert adjusted is True
            assert growth == EdgeCaseHandler.EXTREME_GDP_GROWTH_MIN
            assert len(w) > 0
            assert "Great Depression" in str(w[0].message)
    
    def test_extreme_positive_growth(self):
        """Unrealistic high growth should be capped"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(0.30, year=2026)
            assert adjusted is True
            assert growth == EdgeCaseHandler.EXTREME_GDP_GROWTH_MAX
            assert len(w) > 0
    
    def test_negative_not_allowed(self):
        """When negative not allowed, should floor at 0"""
        growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(
            -0.05, allow_negative=False
        )
        assert growth == 0.0
        assert adjusted is True


class TestSafeDivide:
    """Test safe division with zero handling"""
    
    def test_normal_division(self):
        """Normal division should work"""
        result = EdgeCaseHandler.safe_divide(10.0, 2.0)
        assert result == 5.0
    
    def test_divide_by_zero(self):
        """Division by zero should return default"""
        result = EdgeCaseHandler.safe_divide(10.0, 0.0, default=99.0)
        assert result == 99.0
    
    def test_divide_by_near_zero(self):
        """Division by very small number should return default"""
        result = EdgeCaseHandler.safe_divide(10.0, 1e-15, default=99.0)
        assert result == 99.0
    
    def test_negative_denominator(self):
        """Negative denominator should work"""
        result = EdgeCaseHandler.safe_divide(10.0, -2.0)
        assert result == -5.0
    
    def test_context_logging(self):
        """Context should be logged"""
        result = EdgeCaseHandler.safe_divide(
            10.0, 0.0, default=0.0, context="test division"
        )
        assert result == 0.0


class TestGDPValidation:
    """Test GDP validation to prevent division by zero"""
    
    def test_normal_gdp(self):
        """Normal GDP should pass through"""
        gdp = EdgeCaseHandler.validate_gdp(28.0)
        assert gdp == 28.0
    
    def test_zero_gdp(self):
        """Zero GDP should be raised to minimum"""
        gdp = EdgeCaseHandler.validate_gdp(0.0, year=2026)
        assert gdp == EdgeCaseHandler.MIN_GDP
    
    def test_negative_gdp(self):
        """Negative GDP should be raised to minimum"""
        gdp = EdgeCaseHandler.validate_gdp(-5.0, year=2026)
        assert gdp == EdgeCaseHandler.MIN_GDP
    
    def test_very_small_gdp(self):
        """Very small GDP should be raised to minimum"""
        gdp = EdgeCaseHandler.validate_gdp(0.001, year=2026)
        assert gdp == EdgeCaseHandler.MIN_GDP


class TestPopulationValidation:
    """Test population validation for per-capita calculations"""
    
    def test_normal_population(self):
        """Normal population should pass through"""
        pop = EdgeCaseHandler.validate_population(330_000_000)
        assert pop == 330_000_000
    
    def test_zero_population(self):
        """Zero population should be raised to minimum"""
        pop = EdgeCaseHandler.validate_population(0, year=2026)
        assert pop == EdgeCaseHandler.MIN_POPULATION
    
    def test_small_population(self):
        """Small population should be raised to minimum"""
        pop = EdgeCaseHandler.validate_population(100, year=2026)
        assert pop == EdgeCaseHandler.MIN_POPULATION


class TestExtremeDebt:
    """Test Edge Case #9: Extreme debt levels"""
    
    def test_normal_debt(self):
        """Normal debt level should not trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_debt(
            debt=30.0, gdp=28.0, year=2026
        )
        assert is_extreme is False
        assert msg is None
    
    def test_high_debt(self):
        """High debt (150% GDP) should not trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_debt(
            debt=42.0, gdp=28.0, year=2026
        )
        assert is_extreme is False
        assert msg is None
    
    def test_extreme_debt(self):
        """Extreme debt (>250% GDP) should trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_debt(
            debt=80.0, gdp=28.0, year=2026
        )
        assert is_extreme is True
        assert msg is not None
        assert "Japan" in msg
    
    def test_debt_with_zero_gdp(self):
        """Should handle zero GDP safely"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_debt(
            debt=30.0, gdp=0.0, year=2026
        )
        # Should not crash, returns default from safe_divide
        assert is_extreme is False


class TestExtremeInflation:
    """Test Edge Case #3: Extreme inflation"""
    
    def test_normal_inflation(self):
        """Normal inflation should not trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_inflation(0.02, year=2026)
        assert is_extreme is False
        assert msg is None
    
    def test_deflation(self):
        """Severe deflation should trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_inflation(-0.10, year=2026)
        assert is_extreme is True
        assert msg is not None
        assert "deflation" in msg.lower()
    
    def test_hyperinflation(self):
        """Hyperinflation should trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_inflation(0.30, year=2026)
        assert is_extreme is True
        assert msg is not None
        assert "hyperinflation" in msg.lower()


class TestExtremeInterestRate:
    """Test extreme interest rate detection"""
    
    def test_normal_interest_rate(self):
        """Normal interest rate should not trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_interest_rate(0.04, year=2026)
        assert is_extreme is False
        assert msg is None
    
    def test_high_interest_rate(self):
        """High interest rate (15%) should not trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_interest_rate(0.15, year=2026)
        assert is_extreme is False
        assert msg is None
    
    def test_extreme_interest_rate(self):
        """Extreme interest rate (>25%) should trigger warning"""
        is_extreme, msg = EdgeCaseHandler.check_extreme_interest_rate(0.30, year=2026)
        assert is_extreme is True
        assert msg is not None
        assert "Volcker" in msg


class TestMissingCBOData:
    """Test Edge Case #10: Missing CBO data"""
    
    def test_with_fallback_data(self):
        """Should use provided fallback data"""
        fallback = {'value': 99.0, 'source': 'fallback'}
        result = EdgeCaseHandler.handle_missing_cbo_data(
            'test_data',
            fallback_data=fallback
        )
        assert result == fallback
        assert result['source'] == 'fallback'
    
    def test_with_cached_data(self):
        """Should use cached data if no fallback"""
        cached = {'test_data': {'value': 88.0, 'source': 'cache'}}
        result = EdgeCaseHandler.handle_missing_cbo_data(
            'test_data',
            cached_data=cached
        )
        assert result['value'] == 88.0
        assert result['source'] == 'cache'
    
    def test_with_hardcoded_defaults(self):
        """Should use hardcoded defaults as last resort"""
        result = EdgeCaseHandler.handle_missing_cbo_data('gdp')
        assert 'value' in result
        assert result['source'] == 'hardcoded_default'
    
    def test_fallback_precedence(self):
        """Fallback should take precedence over cached"""
        fallback = {'value': 99.0, 'source': 'fallback'}
        cached = {'test_data': {'value': 88.0, 'source': 'cache'}}
        result = EdgeCaseHandler.handle_missing_cbo_data(
            'test_data',
            fallback_data=fallback,
            cached_data=cached
        )
        assert result == fallback
        assert result['source'] == 'fallback'
    
    def test_known_data_types(self):
        """Should have defaults for known data types"""
        for data_type in ['gdp', 'revenues', 'spending', 'debt', 'interest_rate']:
            result = EdgeCaseHandler.handle_missing_cbo_data(data_type)
            assert 'source' in result
            assert result['source'] == 'hardcoded_default'


class TestPercentageValidation:
    """Test percentage validation"""
    
    def test_valid_percentages(self):
        """Valid percentages should pass"""
        assert EdgeCaseHandler.validate_percentages(0.0, 0.5, 1.0) is True
    
    def test_negative_not_allowed(self):
        """Negative percentage should fail by default"""
        assert EdgeCaseHandler.validate_percentages(-0.1) is False
    
    def test_negative_allowed(self):
        """Negative percentage should pass when allowed"""
        assert EdgeCaseHandler.validate_percentages(-0.1, allow_negative=True) is True
    
    def test_over_100_not_allowed(self):
        """Over 100% should fail by default"""
        assert EdgeCaseHandler.validate_percentages(1.5) is False
    
    def test_over_100_allowed(self):
        """Over 100% should pass when allowed"""
        assert EdgeCaseHandler.validate_percentages(1.5, allow_over_100=True) is True


class TestClampValue:
    """Test value clamping"""
    
    def test_value_in_range(self):
        """Value in range should not be clamped"""
        value, clamped = EdgeCaseHandler.clamp_value(5.0, 0.0, 10.0)
        assert value == 5.0
        assert clamped is False
    
    def test_value_below_min(self):
        """Value below min should be clamped"""
        value, clamped = EdgeCaseHandler.clamp_value(-5.0, 0.0, 10.0)
        assert value == 0.0
        assert clamped is True
    
    def test_value_above_max(self):
        """Value above max should be clamped"""
        value, clamped = EdgeCaseHandler.clamp_value(15.0, 0.0, 10.0)
        assert value == 10.0
        assert clamped is True
    
    def test_value_at_boundaries(self):
        """Value at boundaries should not be clamped"""
        value1, clamped1 = EdgeCaseHandler.clamp_value(0.0, 0.0, 10.0)
        assert value1 == 0.0
        assert clamped1 is False
        
        value2, clamped2 = EdgeCaseHandler.clamp_value(10.0, 0.0, 10.0)
        assert value2 == 10.0
        assert clamped2 is False


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_safe_percentage_of_gdp(self):
        """Safe percentage of GDP calculation"""
        pct = safe_percentage_of_gdp(5.0, 28.0)
        assert abs(pct - (5.0/28.0)) < 0.001
    
    def test_safe_percentage_of_gdp_zero_gdp(self):
        """Should handle zero GDP by using minimum"""
        pct = safe_percentage_of_gdp(5.0, 0.0)
        # Zero GDP gets replaced with MIN_GDP (1.0), so 5.0/1.0 = 5.0
        assert pct == 5.0
    
    def test_safe_per_capita(self):
        """Safe per-capita calculation"""
        per_cap = safe_per_capita(1_000_000, 330_000_000)
        assert abs(per_cap - (1_000_000/330_000_000)) < 0.0001
    
    def test_safe_per_capita_zero_population(self):
        """Should handle zero population by using minimum"""
        per_cap = safe_per_capita(1_000_000, 0)
        # Zero population gets replaced with MIN_POPULATION (1,000,000), so 1M/1M = 1.0
        assert per_cap == 1.0


class TestEdgeCaseIntegration:
    """Integration tests combining multiple edge cases"""
    
    def test_recession_with_deflation(self):
        """Recession with deflation (2008-like scenario)"""
        growth, _ = EdgeCaseHandler.handle_recession_gdp_growth(-0.05, year=2026)
        is_extreme_inflation, _ = EdgeCaseHandler.check_extreme_inflation(-0.01, year=2026)
        
        assert growth == -0.05  # Recession allowed
        assert is_extreme_inflation is False  # Mild deflation not extreme
    
    def test_extreme_scenario_all_warnings(self):
        """Extreme scenario triggering multiple warnings"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Extreme contraction (triggers UserWarning)
            growth, _ = EdgeCaseHandler.handle_recession_gdp_growth(-0.20, year=2026)
            
            # Hyperinflation (no warnings in check_extreme_inflation, just returns bool)
            is_extreme_inf, msg_inf = EdgeCaseHandler.check_extreme_inflation(0.30, year=2026)
            
            # Extreme debt (no warnings in check_extreme_debt, just returns bool)
            is_extreme_debt, msg_debt = EdgeCaseHandler.check_extreme_debt(80.0, 28.0, year=2026)
            
            # Should have at least 1 warning from GDP growth
            assert len(w) >= 1
            assert growth == EdgeCaseHandler.EXTREME_GDP_GROWTH_MIN
            assert is_extreme_inf is True
            assert msg_inf is not None
            assert is_extreme_debt is True
            assert msg_debt is not None
    
    def test_realistic_recession_scenario(self):
        """Realistic recession (2020 COVID-like)"""
        growth, adjusted = EdgeCaseHandler.handle_recession_gdp_growth(-0.032, year=2020)
        is_extreme, _ = EdgeCaseHandler.check_extreme_debt(30.0, 21.0, year=2020)
        
        assert growth == -0.032  # Actual 2020 contraction
        assert adjusted is False
        assert is_extreme is False
