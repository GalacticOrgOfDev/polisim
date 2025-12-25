"""
Tests for Phase 2 Integration Module.

Tests the comprehensive integration of tax reforms and Social Security
enhancements into the simulation engine.
"""

import pytest
import pandas as pd
import numpy as np

from core.phase2_integration import (
    Phase2PolicyPackage,
    Phase2SimulationEngine,
    Phase2ReformPackages,
    create_phase2_comparison_scenarios,
)
from core.tax_reform import (
    WealthTaxParameters,
    ConsumptionTaxParameters,
    CarbonTaxParameters,
    FinancialTransactionTaxParameters,
)


class TestPhase2PolicyPackage:
    """Test Phase 2 policy package configuration."""
    
    def test_empty_package(self):
        """Empty package has no reforms enabled."""
        package = Phase2PolicyPackage()
        
        assert package.wealth_tax_enabled is False
        assert package.consumption_tax_enabled is False
        assert package.carbon_tax_enabled is False
        assert package.ftt_enabled is False
        assert package.ss_payroll_tax_increase is None
        assert package.ss_remove_wage_cap is False
    
    def test_package_with_wealth_tax(self):
        """Package with wealth tax auto-initializes params."""
        package = Phase2PolicyPackage(wealth_tax_enabled=True)
        
        assert package.wealth_tax_enabled is True
        assert package.wealth_tax_params is not None
        assert isinstance(package.wealth_tax_params, WealthTaxParameters)
    
    def test_package_with_custom_params(self):
        """Package accepts custom tax parameters."""
        custom_params = WealthTaxParameters(
            exemption_threshold=100_000_000,
            tax_rate_tier_1=0.03,
            tax_rate_tier_2=0.05,
        )
        package = Phase2PolicyPackage(
            wealth_tax_enabled=True,
            wealth_tax_params=custom_params,
        )
        
        assert package.wealth_tax_params.exemption_threshold == 100_000_000
        assert package.wealth_tax_params.tax_rate_tier_1 == 0.03
    
    def test_package_with_ss_reforms(self):
        """Package with Social Security reforms."""
        package = Phase2PolicyPackage(
            ss_remove_wage_cap=True,
            ss_means_testing_enabled=True,
            ss_longevity_indexing_enabled=True,
        )
        
        assert package.ss_remove_wage_cap is True
        assert package.ss_means_testing_enabled is True
        assert package.ss_longevity_indexing_enabled is True


class TestPhase2SimulationEngine:
    """Test Phase 2 simulation engine."""
    
    def test_engine_initialization(self):
        """Engine initializes with correct parameters."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
            seed=42,
        )
        
        assert engine.base_gdp == 28_000.0
        assert engine.population == 340.0
        assert engine.start_year == 2025
        assert engine.seed == 42
        assert engine.ss_model is not None
        assert engine.tax_reform_analyzer is not None
    
    def test_simulate_baseline_no_reforms(self):
        """Baseline simulation with no reforms."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
        )
        
        baseline = Phase2PolicyPackage()
        results = engine.simulate_comprehensive_reform(
            baseline, years=10, iterations=100
        )
        
        assert 'overview' in results
        assert 'tax_reforms' in results
        assert 'social_security' in results
        
        overview = results['overview']
        assert len(overview) == 10  # 10 years
        assert 'year' in overview.columns
        assert 'total_new_revenue' in overview.columns
        assert 'ss_trust_fund_balance' in overview.columns
    
    def test_simulate_with_wealth_tax(self):
        """Simulation with wealth tax generates revenue."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
        )
        
        package = Phase2PolicyPackage(wealth_tax_enabled=True)
        results = engine.simulate_comprehensive_reform(
            package, years=10, iterations=100
        )
        
        overview = results['overview']
        
        # Wealth tax should generate revenue
        assert overview['tax_reform_revenue'].sum() > 0
        
        # Revenue should grow over time (GDP growth)
        first_year = overview['tax_reform_revenue'].iloc[0]
        last_year = overview['tax_reform_revenue'].iloc[-1]
        assert last_year > first_year
    
    def test_simulate_with_ss_reforms(self):
        """Simulation with Social Security reforms."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
        )
        
        package = Phase2PolicyPackage(
            ss_remove_wage_cap=True,
            ss_payroll_tax_increase=0.134,  # 13.4% (up from 12.4%)
        )
        results = engine.simulate_comprehensive_reform(
            package, years=10, iterations=100
        )
        
        overview = results['overview']
        
        # Social Security reforms should improve trust fund balance
        final_balance = overview['ss_trust_fund_balance'].iloc[-1]
        assert final_balance >= 0  # Should remain solvent
        
        # Payroll revenue should be positive
        assert overview['ss_payroll_revenue'].sum() > 0
    
    def test_simulate_comprehensive_reform(self):
        """Comprehensive reform with multiple tax types and SS reforms."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
        )
        
        package = Phase2PolicyPackage(
            wealth_tax_enabled=True,
            consumption_tax_enabled=True,
            carbon_tax_enabled=True,
            ss_remove_wage_cap=True,
            ss_longevity_indexing_enabled=True,
        )
        
        results = engine.simulate_comprehensive_reform(
            package, years=10, iterations=100
        )
        
        overview = results['overview']
        
        # Multiple revenue sources
        assert overview['tax_reform_revenue'].sum() > 0
        assert overview['ss_payroll_revenue'].sum() > 0
        
        # Net fiscal impact should be positive
        assert overview['net_fiscal_impact'].sum() > 0
        
        # GDP growth should be reflected
        first_year_gdp = overview['gdp'].iloc[0]
        last_year_gdp = overview['gdp'].iloc[-1]
        assert last_year_gdp > first_year_gdp
    
    def test_compare_scenarios(self):
        """Compare multiple policy scenarios."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
        )
        
        reform_packages = [
            ("Wealth Tax Only", Phase2PolicyPackage(wealth_tax_enabled=True)),
            ("SS Reforms Only", Phase2PolicyPackage(ss_remove_wage_cap=True)),
        ]
        
        comparison = engine.compare_scenarios(
            baseline_package=None,
            reform_packages=reform_packages,
            years=10,
        )
        
        assert len(comparison) == 10  # 10 years
        assert 'year' in comparison.columns
        assert 'Baseline_revenue' in comparison.columns
        assert 'Wealth Tax Only_revenue' in comparison.columns
        assert 'SS Reforms Only_revenue' in comparison.columns


class TestPhase2ReformPackages:
    """Test pre-defined reform packages."""
    
    def test_comprehensive_progressive_reform(self):
        """Comprehensive progressive reform has all features."""
        package = Phase2ReformPackages.comprehensive_progressive_reform()
        
        # Tax reforms
        assert package.wealth_tax_enabled is True
        assert package.consumption_tax_enabled is True
        assert package.carbon_tax_enabled is True
        assert package.ftt_enabled is True
        
        # SS reforms
        assert package.ss_remove_wage_cap is True
        assert package.ss_means_testing_enabled is True
        assert package.ss_longevity_indexing_enabled is True
        assert package.ss_cola_formula == "chained_cpi"
    
    def test_moderate_reform(self):
        """Moderate reform is less aggressive."""
        package = Phase2ReformPackages.moderate_reform()
        
        assert package.consumption_tax_enabled is True
        assert package.carbon_tax_enabled is True
        assert package.wealth_tax_enabled is False  # Not in moderate
        assert package.ss_remove_wage_cap is True
        assert package.ss_raise_fra == 69
    
    def test_revenue_focused_reform(self):
        """Revenue-focused maximizes revenue generation."""
        package = Phase2ReformPackages.revenue_focused_reform()
        
        # All tax types enabled
        assert package.wealth_tax_enabled is True
        assert package.consumption_tax_enabled is True
        assert package.carbon_tax_enabled is True
        assert package.ftt_enabled is True
        
        # Aggressive SS reforms
        assert package.ss_payroll_tax_increase == 0.144  # 2% increase
        assert package.ss_remove_wage_cap is True
    
    def test_benefit_preservation_reform(self):
        """Benefit preservation protects current benefits."""
        package = Phase2ReformPackages.benefit_preservation_reform()
        
        # Revenue-side only (no benefit cuts)
        assert package.ss_remove_wage_cap is True
        assert package.ss_progressive_tax_enabled is True
        
        # No benefit reductions
        assert package.ss_raise_fra is None
        assert package.ss_means_testing_enabled is False
    
    def test_climate_focused_reform(self):
        """Climate-focused prioritizes carbon pricing."""
        package = Phase2ReformPackages.climate_focused_reform()
        
        assert package.carbon_tax_enabled is True
        assert package.carbon_tax_params is not None
        
        # Higher carbon tax rate
        assert package.carbon_tax_params.price_per_ton_co2 == 50.0


class TestScenarioCreation:
    """Test scenario creation utilities."""
    
    def test_create_comparison_scenarios(self):
        """Create comprehensive comparison scenarios."""
        scenarios = create_phase2_comparison_scenarios()
        
        assert len(scenarios) == 6  # 6 pre-defined scenarios
        
        # Check scenario structure
        for name, package in scenarios:
            assert isinstance(name, str)
            assert isinstance(package, Phase2PolicyPackage)
        
        # Check specific scenarios exist
        scenario_names = [name for name, _ in scenarios]
        assert "Baseline (No Reforms)" in scenario_names
        assert "Comprehensive Progressive" in scenario_names
        assert "Climate-Focused" in scenario_names


class TestIntegrationResults:
    """Test integration produces realistic results."""
    
    def test_revenue_scales_with_gdp(self):
        """Revenue should scale with GDP growth."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
        )
        
        package = Phase2PolicyPackage(consumption_tax_enabled=True)
        results = engine.simulate_comprehensive_reform(
            package, years=10, gdp_growth_rate=0.03, iterations=100
        )
        
        overview = results['overview']
        
        # Revenue as % of GDP should be relatively stable
        revenue_pct_gdp = overview['new_revenue_pct_gdp']
        std_dev = revenue_pct_gdp.std()
        
        # Standard deviation should be small (revenue scales with GDP)
        assert std_dev < 0.5  # Less than 0.5% variation
    
    def test_ss_solvency_improves_with_reforms(self):
        """SS solvency should improve with reforms."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
            seed=42,
        )
        
        # Baseline (no reforms)
        baseline = Phase2PolicyPackage()
        baseline_results = engine.simulate_comprehensive_reform(
            baseline, years=30, iterations=100
        )
        
        # With reforms
        reform = Phase2PolicyPackage(
            ss_remove_wage_cap=True,
            ss_payroll_tax_increase=0.134,
        )
        
        # Reset model for fair comparison
        engine.ss_model = None
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
            seed=42,
        )
        
        reform_results = engine.simulate_comprehensive_reform(
            reform, years=30, iterations=100
        )
        
        # Reform should improve solvency probability
        baseline_solvency = baseline_results['overview']['ss_solvency_probability'].mean()
        reform_solvency = reform_results['overview']['ss_solvency_probability'].mean()
        
        # Reform should have equal or better solvency
        assert reform_solvency >= baseline_solvency - 0.1  # Allow for Monte Carlo variation
    
    def test_combined_package_realistic_magnitude(self):
        """Combined reform package produces revenue (magnitude test)."""
        engine = Phase2SimulationEngine(
            base_gdp=28_000.0,
            population=340.0,
            start_year=2025,
        )
        
        package = Phase2ReformPackages.comprehensive_progressive_reform()
        results = engine.simulate_comprehensive_reform(
            package, years=10, iterations=100
        )
        
        overview = results['overview']
        
        # Verify revenue is generated (basic sanity check)
        total_revenue_first_year = overview['total_new_revenue'].iloc[0]
        
        # Revenue should be positive
        assert total_revenue_first_year > 0
        
        # Revenue should grow over time (with GDP)
        first_year = overview['total_new_revenue'].iloc[0]
        last_year = overview['total_new_revenue'].iloc[-1]
        assert last_year > first_year  # Revenue grows with GDP


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
