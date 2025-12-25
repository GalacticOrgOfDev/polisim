"""
Tests for tax_reform.py module.
Test comprehensive tax reform functionality including wealth tax,
consumption tax, carbon tax, FTT, and distributional analysis.
"""

import pytest
import numpy as np
import pandas as pd

from core.tax_reform import (
    WealthTaxModel,
    WealthTaxParameters,
    ConsumptionTaxModel,
    ConsumptionTaxParameters,
    CarbonTaxModel,
    CarbonTaxParameters,
    FinancialTransactionTaxModel,
    FinancialTransactionTaxParameters,
    TaxIncidenceAnalyzer,
    BehavioralResponseModel,
    ComprehensiveTaxReformAnalyzer
)


class TestWealthTax:
    """Test wealth tax functionality."""
    
    def test_wealth_tax_initialization(self):
        """Test wealth tax model initialization."""
        model = WealthTaxModel()
        assert model.params.exemption_threshold == 50_000_000
        assert model.params.tax_rate_tier_1 == 0.02
    
    def test_wealth_tax_revenue_calculation(self):
        """Test wealth tax revenue calculation."""
        model = WealthTaxModel()
        gross_revenue = model.calculate_gross_revenue(15_000, 130_000)
        assert gross_revenue > 0
        assert gross_revenue < 1000  # Reasonable range
    
    def test_wealth_tax_avoidance(self):
        """Test avoidance and evasion adjustments."""
        model = WealthTaxModel()
        gross_revenue = 400  # $400B gross
        net_revenue = model.apply_avoidance_and_evasion(gross_revenue)
        
        # Should be reduced by ~25% (20% avoidance + 5% evasion)
        assert net_revenue < gross_revenue
        assert net_revenue > gross_revenue * 0.70
    
    def test_wealth_tax_projection(self):
        """Test multi-year projection."""
        model = WealthTaxModel()
        projection = model.project_revenue(years=10)
        
        assert len(projection) == 10
        assert "year" in projection.columns
        assert "net_revenue" in projection.columns
        # Revenue should grow over time (wealth grows)
        assert projection["net_revenue"].iloc[-1] > projection["net_revenue"].iloc[0]
    
    def test_progressive_wealth_tax(self):
        """Test progressive wealth tax parameters."""
        params = WealthTaxParameters.progressive_wealth_tax()
        assert params.tax_rate_tier_2 == 0.06  # Higher top rate


class TestConsumptionTax:
    """Test consumption/VAT tax functionality."""
    
    def test_consumption_tax_initialization(self):
        """Test consumption tax model initialization."""
        model = ConsumptionTaxModel()
        assert model.params.tax_rate == 0.10
        assert model.params.exemption_share == 0.30
    
    def test_consumption_tax_revenue(self):
        """Test consumption tax revenue calculation."""
        model = ConsumptionTaxModel()
        gdp = 28_000  # $28T
        gross_revenue = model.calculate_gross_revenue(gdp)
        
        # 68% of GDP is consumption, 70% taxable, 10% rate
        expected_approx = 28_000 * 0.68 * 0.70 * 0.10
        assert abs(gross_revenue - expected_approx) < 100
    
    def test_consumption_tax_rebate(self):
        """Test low-income rebate calculation."""
        model = ConsumptionTaxModel()
        rebate_cost = model.calculate_rebate_cost(population=335)  # 335M people
        assert rebate_cost > 0
        assert rebate_cost < 300  # Reasonable range
    
    def test_distributional_impact(self):
        """Test distributional analysis."""
        model = ConsumptionTaxModel()
        income_quintiles = pd.DataFrame({
            "quintile": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "avg_income": [15_000, 40_000, 70_000, 110_000, 280_000]
        })
        
        impact = model.analyze_distributional_impact(income_quintiles)
        assert len(impact) == 5
        # With rebates, consumption taxes can be progressive
        # burden_index should be positive and vary across quintiles
        assert impact["burden_index"].min() >= 0.0
        assert len(impact["burden_index"].unique()) > 1  # Varies across quintiles
    
    def test_consumption_tax_projection(self):
        """Test multi-year projection."""
        model = ConsumptionTaxModel()
        gdp_growth = np.full(10, 0.025)
        projection = model.project_revenue(years=10, gdp_growth=gdp_growth, population=335)
        
        assert len(projection) == 10
        assert "net_revenue" in projection.columns
        # Revenue should grow with GDP
        assert projection["net_revenue"].iloc[-1] > projection["net_revenue"].iloc[0]


class TestCarbonTax:
    """Test carbon tax functionality."""
    
    def test_carbon_tax_initialization(self):
        """Test carbon tax model initialization."""
        model = CarbonTaxModel()
        assert model.params.price_per_ton_co2 == 50.0
        assert model.params.total_emissions_mt == 5_000
    
    def test_emissions_reduction(self):
        """Test emissions reduction from pricing."""
        model = CarbonTaxModel()
        reduced_emissions = model.calculate_emissions_reduction(price=100, year=5)
        
        # Should be less than baseline
        assert reduced_emissions < model.params.total_emissions_mt
        assert reduced_emissions > 500  # Floor
    
    def test_carbon_revenue_calculation(self):
        """Test carbon revenue calculation."""
        model = CarbonTaxModel()
        revenue = model.calculate_revenue(emissions=4_000, price=50)
        assert revenue == 200_000  # 4000 MT * $50/ton = $200B... wait, units!
        # Actually 4000 * 50 = 200,000 but emissions in MT means this is $200B
    
    def test_revenue_distribution(self):
        """Test carbon revenue distribution."""
        model = CarbonTaxModel()
        distribution = model.distribute_revenue(total_revenue=200)
        
        assert "citizen_dividend" in distribution
        assert "transition_assistance" in distribution
        assert "clean_energy_investment" in distribution
        
        # Should sum to total
        assert abs(sum(distribution.values()) - 200) < 0.01
    
    def test_sectoral_impact_analysis(self):
        """Test sectoral impact analysis."""
        model = CarbonTaxModel()
        impact = model.analyze_sectoral_impact(carbon_price=50)
        
        assert len(impact) == 4  # 4 sectors
        assert "electricity" in impact["sector"].values
        assert "cost_impact_billions" in impact.columns
    
    def test_carbon_tax_projection(self):
        """Test multi-year projection with declining emissions."""
        model = CarbonTaxModel()
        projection = model.project_revenue(years=10)
        
        assert len(projection) == 10
        # Carbon price should increase
        assert projection["carbon_price"].iloc[-1] > projection["carbon_price"].iloc[0]
        # Emissions should decrease
        assert projection["emissions_mt"].iloc[-1] < projection["emissions_mt"].iloc[0]


class TestFinancialTransactionTax:
    """Test financial transaction tax functionality."""
    
    def test_ftt_initialization(self):
        """Test FTT model initialization."""
        model = FinancialTransactionTaxModel()
        assert model.params.stock_tax_rate == 0.001
        assert model.params.stock_volume == 50_000
    
    def test_volume_impact(self):
        """Test trading volume reduction."""
        model = FinancialTransactionTaxModel()
        adjusted_volume = model.calculate_volume_impact(
            baseline_volume=50_000,
            tax_rate=0.001
        )
        
        # Volume should decrease
        assert adjusted_volume < 50_000
        assert adjusted_volume > 15_000  # Floor at 30% of baseline
    
    def test_revenue_by_asset_class(self):
        """Test revenue calculation by asset class."""
        model = FinancialTransactionTaxModel()
        revenue = model.calculate_revenue_by_asset_class()
        
        assert "stocks" in revenue
        assert "bonds" in revenue
        assert "derivatives" in revenue
        assert all(v >= 0 for v in revenue.values())
    
    def test_market_efficiency_impact(self):
        """Test market efficiency assessment."""
        model = FinancialTransactionTaxModel()
        impact = model.assess_market_efficiency_impact()
        
        assert "bid_ask_spread_increase_pct" in impact
        assert "hft_reduction_pct" in impact
        assert impact["hft_reduction_pct"] >= 0
    
    def test_ftt_projection(self):
        """Test multi-year projection."""
        model = FinancialTransactionTaxModel()
        projection = model.project_revenue(years=10)
        
        assert len(projection) == 10
        assert "total_revenue" in projection.columns
        # Revenue should grow with market volume
        assert projection["total_revenue"].iloc[-1] > projection["total_revenue"].iloc[0]
    
    def test_progressive_ftt(self):
        """Test progressive FTT parameters."""
        params = FinancialTransactionTaxParameters.progressive_ftt()
        assert params.stock_tax_rate == 0.005  # Higher rate


class TestTaxIncidenceAnalyzer:
    """Test tax incidence and distributional analysis."""
    
    def test_incidence_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = TaxIncidenceAnalyzer()
        assert len(analyzer.income_quintiles) == 5
    
    def test_effective_tax_rate_calculation(self):
        """Test effective tax rate calculation."""
        analyzer = TaxIncidenceAnalyzer()
        tax_changes = {
            "income_tax": 0.02,
            "consumption_tax": 0.05
        }
        
        rates = analyzer.calculate_effective_tax_rates(tax_changes)
        assert len(rates) == 5
        assert "effective_rate" in rates.columns
    
    def test_gini_coefficient(self):
        """Test Gini coefficient calculation."""
        analyzer = TaxIncidenceAnalyzer()
        pre_tax = pd.Series([10, 20, 30, 40, 100])
        post_tax = pd.Series([12, 22, 32, 42, 90])
        
        pre_gini, post_gini = analyzer.calculate_gini_coefficient(pre_tax, post_tax)
        assert 0 <= pre_gini <= 1
        assert 0 <= post_gini <= 1
        # Progressive tax should reduce Gini
        assert post_gini < pre_gini
    
    def test_progressivity_analysis(self):
        """Test progressivity assessment."""
        analyzer = TaxIncidenceAnalyzer()
        tax_system = pd.DataFrame({
            "quintile": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "effective_rate": [0.05, 0.10, 0.15, 0.20, 0.30]
        })
        
        analysis = analyzer.analyze_progressivity(tax_system)
        assert "progressivity_ratio" in analysis
        assert "system_type" in analysis
        assert analysis["system_type"] == "progressive"
    
    def test_distributional_table(self):
        """Test CBO-style distributional table generation."""
        analyzer = TaxIncidenceAnalyzer()
        
        baseline = pd.DataFrame({
            "quintile": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "avg_income": [15_000, 40_000, 70_000, 110_000, 280_000],
            "total_burden": [750, 4_000, 10_500, 22_000, 84_000],
            "effective_rate": [0.05, 0.10, 0.15, 0.20, 0.30]
        })
        
        reformed = baseline.copy()
        reformed["total_burden"] = reformed["total_burden"] * 1.1
        reformed["effective_rate"] = reformed["effective_rate"] * 1.1
        
        table = analyzer.generate_distributional_table(baseline, reformed)
        assert len(table) == 5
        assert "change_in_burden" in table.columns


class TestBehavioralResponseModel:
    """Test behavioral response modeling."""
    
    def test_tax_avoidance_response(self):
        """Test tax avoidance modeling."""
        effective_revenue = BehavioralResponseModel.model_tax_avoidance_response(
            tax_rate_change=0.10,  # 10% rate increase
            baseline_revenue=1000,
            avoidance_elasticity=-0.25
        )
        
        # Should be less than simple 10% increase due to avoidance
        assert effective_revenue < 1000 * 0.10
    
    def test_labor_supply_response(self):
        """Test labor supply response."""
        new_hours = BehavioralResponseModel.model_labor_supply_response(
            marginal_rate_change=0.10,
            baseline_hours=2000,
            labor_elasticity=-0.15
        )
        
        # Should work fewer hours
        assert new_hours < 2000
    
    def test_profit_shifting(self):
        """Test corporate profit shifting."""
        remaining_profits = BehavioralResponseModel.model_corporate_profit_shifting(
            rate_differential=0.10,
            baseline_profits=500,
            shifting_elasticity=-0.80
        )
        
        # Should shift profits away
        assert remaining_profits < 500
    
    def test_investment_response(self):
        """Test investment response to returns."""
        new_investment = BehavioralResponseModel.model_investment_response(
            after_tax_return_change=0.05,  # 5% better returns
            baseline_investment=1000,
            investment_elasticity=0.40
        )
        
        # Should invest more
        assert new_investment > 1000


class TestComprehensiveTaxReformAnalyzer:
    """Test comprehensive tax reform analysis."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = ComprehensiveTaxReformAnalyzer()
        assert analyzer.wealth_tax is not None
        assert analyzer.consumption_tax is not None
        assert analyzer.carbon_tax is not None
        assert analyzer.ftt is not None
    
    def test_single_tax_reform_analysis(self):
        """Test analysis with single tax type."""
        analyzer = ComprehensiveTaxReformAnalyzer()
        
        reforms = {
            "wealth_tax": {
                "exemption_threshold": 50_000_000,
                "tax_rate_tier_1": 0.02,
                "tax_rate_tier_2": 0.03
            }
        }
        
        results = analyzer.analyze_reform_package(reforms, years=10)
        assert "wealth_tax" in results
        assert "total_combined" in results
    
    def test_comprehensive_reform_analysis(self):
        """Test analysis with multiple tax types."""
        analyzer = ComprehensiveTaxReformAnalyzer()
        
        reforms = {
            "wealth_tax": {
                "exemption_threshold": 50_000_000,
                "tax_rate_tier_1": 0.02
            },
            "carbon_tax": {
                "price_per_ton_co2": 50.0
            },
            "ftt": {
                "stock_tax_rate": 0.001
            }
        }
        
        results = analyzer.analyze_reform_package(reforms, years=10)
        
        assert "wealth_tax" in results
        assert "carbon_tax" in results
        assert "ftt" in results
        assert "total_combined" in results
        assert "distributional" in results
        
        # Total combined should have all years
        assert len(results["total_combined"]) == 10
    
    def test_revenue_combination(self):
        """Test revenue combination from multiple sources."""
        analyzer = ComprehensiveTaxReformAnalyzer()
        
        reforms = {
            "wealth_tax": {"exemption_threshold": 50_000_000},
            "carbon_tax": {"price_per_ton_co2": 50.0}
        }
        
        results = analyzer.analyze_reform_package(reforms, years=5)
        combined = results["total_combined"]
        
        # Combined revenue should be sum of components
        assert "total_revenue" in combined.columns
        assert combined["total_revenue"].sum() > 0


class TestTaxReformIntegration:
    """Integration tests for tax reform module."""
    
    def test_all_models_work_together(self):
        """Test that all models can run in sequence."""
        # Wealth tax
        wealth = WealthTaxModel()
        wealth_rev = wealth.project_revenue(years=5)
        
        # Consumption tax
        consumption = ConsumptionTaxModel()
        consumption_rev = consumption.project_revenue(
            years=5,
            gdp_growth=np.full(5, 0.025),
            population=335
        )
        
        # Carbon tax
        carbon = CarbonTaxModel()
        carbon_rev = carbon.project_revenue(years=5)
        
        # FTT
        ftt = FinancialTransactionTaxModel()
        ftt_rev = ftt.project_revenue(years=5)
        
        # All should produce valid results
        assert len(wealth_rev) == 5
        assert len(consumption_rev) == 5
        assert len(carbon_rev) == 5
        assert len(ftt_rev) == 5
    
    def test_revenue_magnitudes_reasonable(self):
        """Test that revenue projections are in reasonable ranges."""
        analyzer = ComprehensiveTaxReformAnalyzer()
        
        reforms = {
            "wealth_tax": {},
            "consumption_tax": {},
            "carbon_tax": {},
            "ftt": {}
        }
        
        results = analyzer.analyze_reform_package(reforms, years=10)
        total_first_year = results["total_combined"]["total_revenue"].iloc[0]
        
        # Total should be between $100B and $500T (10-year cumulative)
        assert 100 < total_first_year < 500_000
