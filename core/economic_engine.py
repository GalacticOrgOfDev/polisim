"""
Economic modeling and simulation engine for polisim.

This module extracts core business logic from Economic_projector.py,
providing a clean, testable API for Monte Carlo simulations, economic
projections, and scenario analysis.

Classes:
    - PolicyScenario: Encapsulates a single policy configuration
    - MonteCarloEngine: Runs stochastic simulations
    - EconomicModel: Orchestrates projections
    - SensitivityAnalyzer: Performs sensitivity analysis
    - ScenarioComparator: Compares multiple scenarios
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


@dataclass
class EconomicParameters:
    """Base economic parameters for all simulations."""
    gdp: float  # Trillions
    gdp_growth_rate: float  # Annual %
    inflation_rate: float  # Annual %
    national_debt: float  # Trillions
    interest_rate: float  # Annual %
    simulation_years: int = 10
    transition_fund: float = 0.0  # Trillions
    surplus_redirect_post_debt: float = 0.0  # %
    surplus_redirect_target: str = "federal"
    stop_on_debt_explosion: bool = True
    debt_drag_factor: float = 0.1  # GDP drag per 10% debt/GDP

    def validate(self) -> None:
        """Validate parameter ranges."""
        if self.gdp <= 0:
            raise ValueError(f"GDP must be positive, got {self.gdp}")
        if self.national_debt < 0:
            raise ValueError(f"National debt cannot be negative, got {self.national_debt}")
        if not 0 <= self.surplus_redirect_post_debt <= 100:
            raise ValueError(f"Surplus redirect must be 0-100%, got {self.surplus_redirect_post_debt}")
        if self.inflation_rate > 0.5:
            logger.warning(f"High inflation rate: {self.inflation_rate*100}%. This may indicate unrealistic assumptions.")
        if self.simulation_years < 1 or self.simulation_years > 100:
            raise ValueError(f"Simulation years must be 1-100, got {self.simulation_years}")
        logger.info("Economic parameters validated successfully")


@dataclass
class RevenueLine:
    """A single revenue source or tax."""
    name: str
    is_percent: bool  # True if % of GDP, False if fixed $ amount
    value: float  # Trillions if fixed, % if percentage
    description: str = ""
    # Allocation breakdown
    alloc_health: float = 0.0  # %
    alloc_states: float = 0.0  # %
    alloc_federal: float = 0.0  # %

    def validate(self) -> None:
        """Validate revenue line."""
        if self.value < 0:
            raise ValueError(f"Revenue value cannot be negative: {self.name}")
        total_alloc = self.alloc_health + self.alloc_states + self.alloc_federal
        if total_alloc > 0 and abs(total_alloc - 100.0) > 0.1:
            logger.warning(f"Revenue allocation for {self.name} sums to {total_alloc}%, not 100%")


@dataclass
class SpendingCategory:
    """A major spending category."""
    name: str
    is_percent: bool  # True if % of GDP target
    value: float  # Trillions if fixed, % if percentage
    allocations: List[Dict[str, float]] = field(default_factory=list)  # [{source, percent}, ...]

    def validate(self) -> None:
        """Validate spending category."""
        if self.value < 0:
            raise ValueError(f"Spending cannot be negative: {self.name}")
        for alloc in self.allocations:
            if not 0 <= alloc.get("percent", 0) <= 100:
                raise ValueError(f"Allocation percentage must be 0-100: {self.name}")


@dataclass
class PolicyScenario:
    """Complete policy configuration for a scenario."""
    name: str
    economic_params: EconomicParameters
    revenues: List[RevenueLine]
    spending: List[SpendingCategory]
    location: Optional[Dict[str, str]] = None  # {country, region, subregion}
    description: str = ""
    metadata: Dict = field(default_factory=dict)

    def validate(self) -> None:
        """Validate entire scenario."""
        logger.info(f"Validating scenario: {self.name}")
        self.economic_params.validate()
        for rev in self.revenues:
            rev.validate()
        for spend in self.spending:
            spend.validate()
        logger.info(f"Scenario {self.name} validated")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "economic_params": self.economic_params.__dict__,
            "revenues": [r.__dict__ for r in self.revenues],
            "spending": [s.__dict__ for s in self.spending],
            "location": self.location or {},
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class SimulationResult:
    """Results from a single Monte Carlo run."""
    scenario_name: str
    years: np.ndarray  # Array of years [0, 1, 2, ...]
    gdp: np.ndarray  # GDP over time (trillions)
    revenues: np.ndarray  # Total revenue over time
    spending: np.ndarray  # Total spending over time
    debt: np.ndarray  # National debt over time
    deficit: np.ndarray  # Annual deficit/surplus
    percentiles: Dict[str, np.ndarray] = field(default_factory=dict)
    # E.g., {'10th': array(...), '50th': array(...), '90th': array(...)}
    metadata: Dict = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        df = pd.DataFrame({
            "Year": self.years,
            "GDP": self.gdp,
            "Revenue": self.revenues,
            "Spending": self.spending,
            "Debt": self.debt,
            "Deficit": self.deficit,
        })
        for percentile, values in self.percentiles.items():
            df[f"Debt_{percentile}"] = values
        return df


class MonteCarloEngine:
    """
    Runs stochastic Monte Carlo simulations over economic scenarios.
    
    Handles:
    - Parameter uncertainty
    - Sensitivity analysis
    - Distribution sampling
    - Convergence checking
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize engine with optional random seed for reproducibility."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def run_simulation(
        self,
        scenario: PolicyScenario,
        iterations: int = 100000,
        uncertainty_dict: Optional[Dict] = None,
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation with parameter uncertainty.
        
        Args:
            scenario: PolicyScenario to simulate
            iterations: Number of Monte Carlo iterations
            uncertainty_dict: Dict of parameter -> (mean, std_dev) for uncertainty
                             E.g., {'gdp_growth_rate': (0.02, 0.01)}
        
        Returns:
            SimulationResult with percentiles and full history
        """
        logger.info(f"Starting Monte Carlo simulation: {scenario.name} ({iterations} iterations)")
        scenario.validate()
        
        years = np.arange(scenario.economic_params.simulation_years + 1)
        
        # Initialize result arrays (mean trajectory)
        gdp_trajectories = np.zeros((iterations, len(years)))
        revenue_trajectories = np.zeros((iterations, len(years)))
        spending_trajectories = np.zeros((iterations, len(years)))
        debt_trajectories = np.zeros((iterations, len(years)))
        deficit_trajectories = np.zeros((iterations, len(years)))
        
        for i in range(iterations):
            if i % max(1, iterations // 10) == 0:
                logger.debug(f"  Iteration {i}/{iterations}")
            
            # Create perturbed parameters if uncertainty provided
            params = self._perturb_parameters(scenario.economic_params, uncertainty_dict)
            
            # Run projection
            gdp_traj, rev_traj, spend_traj, debt_traj, def_traj = self._project_single(
                scenario, params, years
            )
            
            gdp_trajectories[i] = gdp_traj
            revenue_trajectories[i] = rev_traj
            spending_trajectories[i] = spend_traj
            debt_trajectories[i] = debt_traj
            deficit_trajectories[i] = def_traj
        
        # Compute percentiles
        percentiles = {
            "10th": np.percentile(debt_trajectories, 10, axis=0),
            "25th": np.percentile(debt_trajectories, 25, axis=0),
            "50th": np.percentile(debt_trajectories, 50, axis=0),  # Median
            "75th": np.percentile(debt_trajectories, 75, axis=0),
            "90th": np.percentile(debt_trajectories, 90, axis=0),
        }
        
        # Mean trajectory
        mean_gdp = gdp_trajectories.mean(axis=0)
        mean_revenue = revenue_trajectories.mean(axis=0)
        mean_spending = spending_trajectories.mean(axis=0)
        mean_debt = debt_trajectories.mean(axis=0)
        mean_deficit = deficit_trajectories.mean(axis=0)
        
        result = SimulationResult(
            scenario_name=scenario.name,
            years=years,
            gdp=mean_gdp,
            revenues=mean_revenue,
            spending=mean_spending,
            debt=mean_debt,
            deficit=mean_deficit,
            percentiles=percentiles,
            metadata={
                "iterations": iterations,
                "seed": self.seed,
                "final_debt_gdp_ratio": mean_debt[-1] / mean_gdp[-1],
            },
        )
        
        logger.info(f"Simulation complete. Final debt/GDP: {result.metadata['final_debt_gdp_ratio']:.1%}")
        return result

    def _perturb_parameters(
        self, params: EconomicParameters, uncertainty_dict: Optional[Dict]
    ) -> EconomicParameters:
        """Create a perturbed copy of parameters for stochastic sampling."""
        if not uncertainty_dict:
            return params
        
        import copy
        perturbed = copy.deepcopy(params)
        
        for param_name, (mean, std_dev) in uncertainty_dict.items():
            if hasattr(perturbed, param_name):
                sampled_value = np.random.normal(mean, std_dev)
                # Clamp certain parameters to realistic ranges
                if param_name == "gdp_growth_rate":
                    sampled_value = np.clip(sampled_value, -0.1, 0.1)  # -10% to +10%
                elif param_name == "inflation_rate":
                    sampled_value = np.clip(sampled_value, -0.05, 0.5)  # -5% to +50%
                setattr(perturbed, param_name, sampled_value)
        
        return perturbed

    def _project_single(
        self,
        scenario: PolicyScenario,
        params: EconomicParameters,
        years: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Project a single trajectory year-by-year.
        
        Returns:
            (gdp, revenue, spending, debt, deficit) trajectories
        """
        n_years = len(years)
        gdp = np.zeros(n_years)
        revenue = np.zeros(n_years)
        spending = np.zeros(n_years)
        debt = np.zeros(n_years)
        deficit = np.zeros(n_years)
        
        # Initial conditions
        gdp[0] = params.gdp
        debt[0] = params.national_debt
        
        for year_idx in range(1, n_years):
            # GDP growth with debt drag
            debt_to_gdp = debt[year_idx - 1] / gdp[year_idx - 1] if gdp[year_idx - 1] > 0 else 0
            debt_drag = params.debt_drag_factor * max(0, (debt_to_gdp - 0.6) / 0.1)  # Drag if >60% debt/GDP
            adjusted_growth = params.gdp_growth_rate - debt_drag
            gdp[year_idx] = gdp[year_idx - 1] * (1 + adjusted_growth)
            
            # Calculate revenues (% of GDP or fixed)
            year_revenue = 0
            for rev in scenario.revenues:
                if rev.is_percent:
                    year_revenue += gdp[year_idx] * (rev.value / 100)
                else:
                    # Inflate fixed revenues
                    year_revenue += rev.value * ((1 + params.inflation_rate) ** (year_idx))
            revenue[year_idx] = year_revenue
            
            # Calculate spending (% of GDP or fixed)
            year_spending = 0
            for spend in scenario.spending:
                if spend.is_percent:
                    year_spending += gdp[year_idx] * (spend.value / 100)
                else:
                    year_spending += spend.value * ((1 + params.inflation_rate) ** (year_idx))
            spending[year_idx] = year_spending
            
            # Deficit and debt
            deficit[year_idx] = year_spending - year_revenue
            debt[year_idx] = debt[year_idx - 1] + deficit[year_idx]
            
            # Debt explosion check
            if params.stop_on_debt_explosion:
                if debt[year_idx] / gdp[year_idx] > 10.0:  # >1000% debt/GDP
                    logger.warning(f"Debt explosion detected at year {year_idx}; capping debt trajectory")
                    debt[year_idx:] = debt[year_idx]
                    deficit[year_idx:] = 0
                    break
        
        return gdp, revenue, spending, debt, deficit


class EconomicModel:
    """
    Orchestrates economic modeling including baseline, policy, and comparative analysis.
    """

    def __init__(self, engine: Optional[MonteCarloEngine] = None):
        """Initialize with optional custom engine."""
        self.engine = engine or MonteCarloEngine()
        self.baseline_result: Optional[SimulationResult] = None
        self.policy_result: Optional[SimulationResult] = None

    def run_baseline(
        self, baseline_scenario: PolicyScenario, iterations: int = 100000
    ) -> SimulationResult:
        """Run baseline scenario simulation."""
        logger.info("Running baseline scenario simulation")
        self.baseline_result = self.engine.run_simulation(baseline_scenario, iterations)
        return self.baseline_result

    def run_policy(
        self, policy_scenario: PolicyScenario, iterations: int = 100000
    ) -> SimulationResult:
        """Run policy scenario simulation."""
        logger.info("Running policy scenario simulation")
        self.policy_result = self.engine.run_simulation(policy_scenario, iterations)
        return self.policy_result

    def calculate_impact(self) -> pd.DataFrame:
        """Calculate difference between baseline and policy (impact analysis)."""
        if not self.baseline_result or not self.policy_result:
            raise ValueError("Both baseline and policy simulations must be run first")
        
        baseline_df = self.baseline_result.to_dataframe()
        policy_df = self.policy_result.to_dataframe()
        
        impact = pd.DataFrame({
            "Year": baseline_df["Year"],
            "GDP_Difference": policy_df["GDP"] - baseline_df["GDP"],
            "Revenue_Difference": policy_df["Revenue"] - baseline_df["Revenue"],
            "Spending_Difference": policy_df["Spending"] - baseline_df["Spending"],
            "Debt_Difference": policy_df["Debt"] - baseline_df["Debt"],
            "Deficit_Difference": policy_df["Deficit"] - baseline_df["Deficit"],
        })
        
        return impact


class SensitivityAnalyzer:
    """
    Analyzes how model outputs respond to parameter variations.
    """

    def __init__(self, engine: Optional[MonteCarloEngine] = None):
        """Initialize with optional custom engine."""
        self.engine = engine or MonteCarloEngine()

    def tornado_analysis(
        self,
        base_scenario: PolicyScenario,
        parameter_ranges: Dict[str, Tuple[float, float]],
        output_metric: str = "final_debt",
    ) -> pd.DataFrame:
        """
        Perform tornado (one-at-a-time) sensitivity analysis.
        
        Args:
            base_scenario: Base scenario to vary
            parameter_ranges: Dict of param_name -> (min_val, max_val)
            output_metric: Which output to track ('final_debt', 'final_deficit', etc.)
        
        Returns:
            DataFrame with sensitivity results
        """
        logger.info(f"Starting tornado analysis for {len(parameter_ranges)} parameters")
        results = []
        
        for param_name, (low, high) in parameter_ranges.items():
            # Run low
            scenario_low = self._create_variant(base_scenario, {param_name: low})
            result_low = self.engine.run_simulation(scenario_low, iterations=1000)
            
            # Run high
            scenario_high = self._create_variant(base_scenario, {param_name: high})
            result_high = self.engine.run_simulation(scenario_high, iterations=1000)
            
            # Compute impact
            impact = result_high.debt[-1] - result_low.debt[-1]
            results.append({
                "Parameter": param_name,
                "Low": low,
                "High": high,
                "Impact": impact,
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values("Impact", ascending=False, key=abs)
        logger.info(f"Tornado analysis complete")
        return df

    def _create_variant(self, scenario: PolicyScenario, changes: Dict) -> PolicyScenario:
        """Create a scenario variant with specified parameter changes."""
        import copy
        variant = copy.deepcopy(scenario)
        for param_name, value in changes.items():
            if hasattr(variant.economic_params, param_name):
                setattr(variant.economic_params, param_name, value)
        return variant


class ScenarioComparator:
    """
    Compares multiple scenarios across key dimensions.
    """

    def __init__(self, scenarios: Dict[str, PolicyScenario]):
        """Initialize with dict of name -> scenario."""
        self.scenarios = scenarios
        self.results: Dict[str, SimulationResult] = {}

    def run_all(self, iterations: int = 100000) -> None:
        """Run all scenarios and store results."""
        engine = MonteCarloEngine()
        for name, scenario in self.scenarios.items():
            logger.info(f"Running scenario: {name}")
            self.results[name] = engine.run_simulation(scenario, iterations)

    def comparison_table(self) -> pd.DataFrame:
        """Generate summary comparison table."""
        if not self.results:
            raise ValueError("Must run_all() before comparison_table()")
        
        rows = []
        for name, result in self.results.items():
            rows.append({
                "Scenario": name,
                "Final GDP": result.gdp[-1],
                "Final Revenue": result.revenues[-1],
                "Final Spending": result.spending[-1],
                "Final Debt": result.debt[-1],
                "Final Debt/GDP": result.debt[-1] / result.gdp[-1],
                "Total Deficit": result.deficit.sum(),
            })
        
        return pd.DataFrame(rows)

