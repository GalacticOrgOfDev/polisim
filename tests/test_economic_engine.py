"""
Unit tests for the economic simulation engine.

Tests cover:
- EconomicParameters validation
- PolicyScenario validation and serialization
- MonteCarloEngine simulation logic
- SimulationResult handling
- Parameter perturbation and uncertainty
"""

import pytest
import numpy as np
from dataclasses import dataclass

from core.economic_engine import (
    EconomicParameters,
    RevenueLine,
    SpendingCategory,
    PolicyScenario,
    MonteCarloEngine,
    SimulationResult,
    EconomicModel,
)


class TestEconomicParameters:
    """Tests for EconomicParameters validation."""
    
    def test_valid_parameters(self):
        """Test creation with valid parameters."""
        params = EconomicParameters(
            gdp=29.0,
            gdp_growth_rate=0.025,
            inflation_rate=0.03,
            national_debt=35.0,
            interest_rate=0.04,
            simulation_years=10,
        )
        params.validate()  # Should not raise
    
    def test_negative_gdp_raises_error(self):
        """Test that negative GDP raises ValueError."""
        params = EconomicParameters(
            gdp=-1.0,
            gdp_growth_rate=0.025,
            inflation_rate=0.03,
            national_debt=35.0,
            interest_rate=0.04,
        )
        with pytest.raises(ValueError, match="GDP must be positive"):
            params.validate()
    
    def test_zero_gdp_raises_error(self):
        """Test that zero GDP raises ValueError."""
        params = EconomicParameters(
            gdp=0.0,
            gdp_growth_rate=0.025,
            inflation_rate=0.03,
            national_debt=35.0,
            interest_rate=0.04,
        )
        with pytest.raises(ValueError, match="GDP must be positive"):
            params.validate()
    
    def test_negative_debt_raises_error(self):
        """Test that negative national debt raises ValueError."""
        params = EconomicParameters(
            gdp=29.0,
            gdp_growth_rate=0.025,
            inflation_rate=0.03,
            national_debt=-1.0,
            interest_rate=0.04,
        )
        with pytest.raises(ValueError, match="National debt cannot be negative"):
            params.validate()
    
    def test_invalid_surplus_redirect(self):
        """Test that surplus redirect >100% raises ValueError."""
        params = EconomicParameters(
            gdp=29.0,
            gdp_growth_rate=0.025,
            inflation_rate=0.03,
            national_debt=35.0,
            interest_rate=0.04,
            surplus_redirect_post_debt=150.0,
        )
        with pytest.raises(ValueError, match="Surplus redirect must be 0-100%"):
            params.validate()
    
    def test_simulation_years_bounds(self):
        """Test that simulation years must be 1-100."""
        # Too few years
        params = EconomicParameters(
            gdp=29.0, gdp_growth_rate=0.025, inflation_rate=0.03,
            national_debt=35.0, interest_rate=0.04, simulation_years=0
        )
        with pytest.raises(ValueError, match="Simulation years must be 1-100"):
            params.validate()
        
        # Too many years
        params = EconomicParameters(
            gdp=29.0, gdp_growth_rate=0.025, inflation_rate=0.03,
            national_debt=35.0, interest_rate=0.04, simulation_years=101
        )
        with pytest.raises(ValueError, match="Simulation years must be 1-100"):
            params.validate()


class TestRevenueLine:
    """Tests for RevenueLine validation."""
    
    def test_valid_revenue(self):
        """Test creation and validation of valid revenue."""
        revenue = RevenueLine(
            name="Income Tax",
            is_percent=True,
            value=15.0,
            description="Federal income tax",
        )
        revenue.validate()  # Should not raise
    
    def test_negative_value_raises_error(self):
        """Test that negative revenue value raises ValueError."""
        revenue = RevenueLine(
            name="Tax",
            is_percent=False,
            value=-1.0,
        )
        with pytest.raises(ValueError, match="Revenue value cannot be negative"):
            revenue.validate()


class TestSpendingCategory:
    """Tests for SpendingCategory validation."""
    
    def test_valid_spending(self):
        """Test creation and validation of valid spending category."""
        spending = SpendingCategory(
            name="Healthcare",
            is_percent=True,
            value=10.0,
            allocations=[{"source": "Income Tax", "percent": 50.0}],
        )
        spending.validate()  # Should not raise
    
    def test_negative_spending_raises_error(self):
        """Test that negative spending raises ValueError."""
        spending = SpendingCategory(
            name="Healthcare",
            is_percent=False,
            value=-1.0,
        )
        with pytest.raises(ValueError, match="Spending cannot be negative"):
            spending.validate()
    
    def test_invalid_allocation_percent_raises_error(self):
        """Test that allocation percent >100% raises ValueError."""
        spending = SpendingCategory(
            name="Healthcare",
            is_percent=True,
            value=10.0,
            allocations=[{"source": "Tax", "percent": 150.0}],
        )
        with pytest.raises(ValueError, match="Allocation percentage must be 0-100"):
            spending.validate()


class TestPolicyScenario:
    """Tests for PolicyScenario creation and validation."""
    
    def test_valid_scenario(self):
        """Test creation and validation of complete scenario."""
        params = EconomicParameters(
            gdp=29.0, gdp_growth_rate=0.025, inflation_rate=0.03,
            national_debt=35.0, interest_rate=0.04, simulation_years=10,
        )
        revenues = [
            RevenueLine(name="Income Tax", is_percent=True, value=15.0),
            RevenueLine(name="Sales Tax", is_percent=False, value=2.0),
        ]
        spending = [
            SpendingCategory(name="Healthcare", is_percent=True, value=10.0),
            SpendingCategory(name="Defense", is_percent=True, value=3.0),
        ]
        
        scenario = PolicyScenario(
            name="USGHA",
            economic_params=params,
            revenues=revenues,
            spending=spending,
            description="United States Galactic Health Act",
        )
        scenario.validate()  # Should not raise
    
    def test_scenario_to_dict(self):
        """Test scenario serialization to dict."""
        params = EconomicParameters(
            gdp=29.0, gdp_growth_rate=0.025, inflation_rate=0.03,
            national_debt=35.0, interest_rate=0.04,
        )
        scenario = PolicyScenario(
            name="Test",
            economic_params=params,
            revenues=[RevenueLine(name="Tax", is_percent=True, value=10.0)],
            spending=[SpendingCategory(name="Healthcare", is_percent=True, value=9.0)],
        )
        
        d = scenario.to_dict()
        assert d["name"] == "Test"
        assert "economic_params" in d
        assert "revenues" in d
        assert "spending" in d


class TestMonteCarloEngine:
    """Tests for MonteCarloEngine simulation."""
    
    @pytest.fixture
    def simple_scenario(self):
        """Create a simple test scenario."""
        params = EconomicParameters(
            gdp=29.0,
            gdp_growth_rate=0.025,
            inflation_rate=0.03,
            national_debt=35.0,
            interest_rate=0.04,
            simulation_years=5,
        )
        return PolicyScenario(
            name="Test",
            economic_params=params,
            revenues=[RevenueLine(name="Tax", is_percent=True, value=18.0)],
            spending=[SpendingCategory(name="Spending", is_percent=True, value=19.0)],
        )
    
    def test_engine_initialization(self):
        """Test engine creation with seed."""
        engine = MonteCarloEngine(seed=42)
        assert engine.seed == 42
    
    def test_basic_simulation(self, simple_scenario):
        """Test that basic simulation runs without error."""
        engine = MonteCarloEngine(seed=42)
        result = engine.run_simulation(simple_scenario, iterations=100)
        
        assert result.scenario_name == "Test"
        assert len(result.years) == 6  # 0-5 inclusive
        assert len(result.gdp) == 6
        assert len(result.debt) == 6
        assert result.gdp[0] == 29.0  # Initial GDP
        assert result.debt[0] == 35.0  # Initial debt
    
    def test_gdp_growth(self, simple_scenario):
        """Test that GDP grows as expected."""
        engine = MonteCarloEngine(seed=42)
        result = engine.run_simulation(simple_scenario, iterations=10)
        
        # GDP should grow each year
        for i in range(1, len(result.gdp)):
            assert result.gdp[i] > result.gdp[i-1]
    
    def test_deficit_accumulates_debt(self, simple_scenario):
        """Test that deficits increase debt."""
        engine = MonteCarloEngine(seed=42)
        result = engine.run_simulation(simple_scenario, iterations=10)
        
        # Since spending > revenue (19% vs 18%), debt should increase
        assert result.deficit[-1] > 0  # Final deficit should be positive
        assert result.debt[-1] > result.debt[0]  # Debt should increase
    
    def test_percentiles_computed(self, simple_scenario):
        """Test that percentiles are properly computed."""
        engine = MonteCarloEngine(seed=42)
        result = engine.run_simulation(simple_scenario, iterations=100)
        
        assert "10th" in result.percentiles
        assert "50th" in result.percentiles
        assert "90th" in result.percentiles
        
        # 10th percentile should be < 50th < 90th
        for i in range(len(result.years)):
            assert result.percentiles["10th"][i] <= result.percentiles["50th"][i]
            assert result.percentiles["50th"][i] <= result.percentiles["90th"][i]
    
    def test_deterministic_with_seed(self, simple_scenario):
        """Test that same seed produces same results."""
        engine1 = MonteCarloEngine(seed=42)
        result1 = engine1.run_simulation(simple_scenario, iterations=50)
        
        engine2 = MonteCarloEngine(seed=42)
        result2 = engine2.run_simulation(simple_scenario, iterations=50)
        
        # Results should be identical with same seed
        np.testing.assert_array_almost_equal(result1.gdp, result2.gdp)
        np.testing.assert_array_almost_equal(result1.debt, result2.debt)
    
    def test_to_dataframe(self, simple_scenario):
        """Test conversion to pandas DataFrame."""
        engine = MonteCarloEngine(seed=42)
        result = engine.run_simulation(simple_scenario, iterations=10)
        
        df = result.to_dataframe()
        assert len(df) == 6  # 6 years (0-5)
        assert "Year" in df.columns
        assert "GDP" in df.columns
        assert "Debt" in df.columns
        assert df["Year"].iloc[0] == 0


class TestEconomicModel:
    """Tests for EconomicModel orchestration."""
    
    @pytest.fixture
    def baseline_and_policy(self):
        """Create baseline and policy scenarios."""
        params_base = EconomicParameters(
            gdp=29.0, gdp_growth_rate=0.025, inflation_rate=0.03,
            national_debt=35.0, interest_rate=0.04, simulation_years=5,
        )
        baseline = PolicyScenario(
            name="Baseline",
            economic_params=params_base,
            revenues=[RevenueLine(name="Tax", is_percent=True, value=18.0)],
            spending=[SpendingCategory(name="Spending", is_percent=True, value=19.0)],
        )
        
        params_policy = EconomicParameters(
            gdp=29.0, gdp_growth_rate=0.025, inflation_rate=0.03,
            national_debt=35.0, interest_rate=0.04, simulation_years=5,
        )
        policy = PolicyScenario(
            name="Policy",
            economic_params=params_policy,
            revenues=[RevenueLine(name="Tax", is_percent=True, value=20.0)],
            spending=[SpendingCategory(name="Spending", is_percent=True, value=19.0)],
        )
        
        return baseline, policy
    
    def test_baseline_run(self, baseline_and_policy):
        """Test running baseline scenario."""
        baseline, _ = baseline_and_policy
        model = EconomicModel()
        result = model.run_baseline(baseline, iterations=50)
        
        assert result is not None
        assert result.scenario_name == "Baseline"
    
    def test_policy_run(self, baseline_and_policy):
        """Test running policy scenario."""
        _, policy = baseline_and_policy
        model = EconomicModel()
        result = model.run_policy(policy, iterations=50)
        
        assert result is not None
        assert result.scenario_name == "Policy"
    
    def test_impact_calculation(self, baseline_and_policy):
        """Test impact calculation between baseline and policy."""
        baseline, policy = baseline_and_policy
        model = EconomicModel()
        
        model.run_baseline(baseline, iterations=50)
        model.run_policy(policy, iterations=50)
        
        impact = model.calculate_impact()
        
        assert len(impact) == 6  # 6 years
        assert "Year" in impact.columns
        assert "Revenue_Difference" in impact.columns
        
        # Policy has higher revenue (20% vs 18%), so difference should be positive
        assert impact["Revenue_Difference"].iloc[-1] > 0


class TestSimulationResult:
    """Tests for SimulationResult handling."""
    
    def test_to_dataframe_conversion(self):
        """Test conversion of SimulationResult to DataFrame."""
        years = np.array([0, 1, 2])
        gdp = np.array([29.0, 29.7, 30.5])
        revenues = np.array([5.0, 5.2, 5.4])
        spending = np.array([5.5, 5.7, 5.9])
        debt = np.array([35.0, 35.5, 36.1])
        deficit = np.array([0.5, 0.5, 0.5])
        
        result = SimulationResult(
            scenario_name="Test",
            years=years,
            gdp=gdp,
            revenues=revenues,
            spending=spending,
            debt=debt,
            deficit=deficit,
        )
        
        df = result.to_dataframe()
        assert len(df) == 3
        assert list(df["Year"]) == [0, 1, 2]
        assert list(df["GDP"]) == [29.0, 29.7, 30.5]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

