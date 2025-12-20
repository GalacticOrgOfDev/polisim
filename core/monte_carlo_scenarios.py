"""
Advanced Monte Carlo Scenarios Module
Integrates Monte Carlo uncertainty quantification with custom policies.

Features:
- Apply stochastic simulation to any custom policy
- Generate P10/P90 confidence bounds
- Sensitivity analysis for policy parameters
- Risk assessment and scenario stress testing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from scipy import stats


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    policy_name: str
    iterations: int
    mean_deficit: float
    median_deficit: float
    std_dev_deficit: float
    p10_deficit: float  # 10th percentile (best case)
    p90_deficit: float  # 90th percentile (worst case)
    confidence_bounds: Tuple[float, float]  # (P10, P90)
    best_case: float
    worst_case: float
    probability_balanced: float  # P(deficit < 0)
    simulation_results: np.ndarray  # All simulation paths


class MonteCarloPolicySimulator:
    """Run Monte Carlo simulations on custom policies."""
    
    def __init__(self, base_revenue: float = 5_980.0, base_spending: float = 6_911.0):
        """Initialize simulator with baseline values."""
        self.base_revenue = base_revenue
        self.base_spending = base_spending
        self.gdp = 29_360.0
        self.growth_mean = 0.025  # 2.5% mean growth
        self.growth_std = 0.015  # 1.5% std dev
        self.uncertainty_std = 0.05  # 5% general uncertainty
    
    def simulate_policy(
        self,
        policy_name: str,
        revenue_change_pct: float,
        spending_change_pct: float,
        revenue_uncertainty_pct: float = 5.0,  # Coefficient of variation
        spending_uncertainty_pct: float = 5.0,
        growth_scenarios: Optional[List[float]] = None,
        years: int = 10,
        iterations: int = 10_000,
        random_seed: Optional[int] = None,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation on a policy.
        
        Args:
            policy_name: Name of policy
            revenue_change_pct: Expected revenue change
            spending_change_pct: Expected spending change
            revenue_uncertainty_pct: Uncertainty in revenue change (CV%)
            spending_uncertainty_pct: Uncertainty in spending change (CV%)
            growth_scenarios: List of GDP growth rate assumptions (uses random if None)
            years: Projection years
            iterations: Number of Monte Carlo iterations
            random_seed: Random seed for reproducibility
        
        Returns:
            MonteCarloResult with statistics
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Initialize results array (iterations x years)
        deficit_paths = np.zeros((iterations, years))
        
        for i in range(iterations):
            # Draw random realizations
            if growth_scenarios:
                growth_rate = np.random.choice(growth_scenarios)
            else:
                growth_rate = np.random.normal(self.growth_mean, self.growth_std)
            
            # Revenue uncertainty (lognormal distribution)
            revenue_multiplier = np.random.normal(1.0, revenue_uncertainty_pct / 100)
            revenue_multiplier = np.maximum(revenue_multiplier, 0.5)  # Cap at -50%
            
            # Spending uncertainty (lognormal distribution)
            spending_multiplier = np.random.normal(1.0, spending_uncertainty_pct / 100)
            spending_multiplier = np.maximum(spending_multiplier, 0.5)  # Cap at -50%
            
            # Project each year
            current_revenue = self.base_revenue * (1 + revenue_change_pct / 100) * revenue_multiplier
            current_spending = self.base_spending * (1 + spending_change_pct / 100) * spending_multiplier
            
            for year in range(years):
                # Annual growth
                current_revenue *= (1 + growth_rate)
                current_spending *= (1 + growth_rate)
                
                # Store deficit
                deficit_paths[i, year] = current_spending - current_revenue
        
        # Calculate statistics
        annual_deficits = deficit_paths[:, -1]  # Final year deficits
        
        mean_deficit = np.mean(annual_deficits)
        median_deficit = np.median(annual_deficits)
        std_dev_deficit = np.std(annual_deficits)
        p10_deficit = np.percentile(annual_deficits, 10)
        p90_deficit = np.percentile(annual_deficits, 90)
        best_case = np.min(annual_deficits)
        worst_case = np.max(annual_deficits)
        
        # Probability of balanced budget (deficit < 0)
        probability_balanced = np.mean(annual_deficits < 0) * 100
        
        return MonteCarloResult(
            policy_name=policy_name,
            iterations=iterations,
            mean_deficit=mean_deficit,
            median_deficit=median_deficit,
            std_dev_deficit=std_dev_deficit,
            p10_deficit=p10_deficit,
            p90_deficit=p90_deficit,
            confidence_bounds=(p10_deficit, p90_deficit),
            best_case=best_case,
            worst_case=worst_case,
            probability_balanced=probability_balanced,
            simulation_results=deficit_paths,
        )
    
    def compare_policies(
        self,
        policies: Dict[str, Dict[str, float]],
        years: int = 10,
        iterations: int = 10_000,
    ) -> pd.DataFrame:
        """
        Compare multiple policies with Monte Carlo.
        
        Args:
            policies: Dict of policy_name -> {revenue_change_pct, spending_change_pct}
            years: Projection years
            iterations: Monte Carlo iterations
        
        Returns:
            DataFrame comparing policies
        """
        results = []
        
        for policy_name, params in policies.items():
            mc_result = self.simulate_policy(
                policy_name=policy_name,
                revenue_change_pct=params.get("revenue_change_pct", 0),
                spending_change_pct=params.get("spending_change_pct", 0),
                years=years,
                iterations=iterations,
            )
            
            results.append({
                "Policy": policy_name,
                "Mean Deficit": f"${mc_result.mean_deficit:,.0f}B",
                "Median Deficit": f"${mc_result.median_deficit:,.0f}B",
                "Std Dev": f"${mc_result.std_dev_deficit:,.0f}B",
                "P10 (Best)": f"${mc_result.p10_deficit:,.0f}B",
                "P90 (Worst)": f"${mc_result.p90_deficit:,.0f}B",
                "Balanced Budget %": f"{mc_result.probability_balanced:.1f}%",
            })
        
        return pd.DataFrame(results)


class PolicySensitivityAnalyzer:
    """Analyze sensitivity of policy outcomes to parameter changes."""
    
    @staticmethod
    def tornado_analysis(
        base_revenue: float,
        base_spending: float,
        parameter_ranges: Dict[str, Tuple[float, float]],
        years: int = 10,
    ) -> pd.DataFrame:
        """
        Create tornado chart data showing parameter sensitivity.
        
        Args:
            base_revenue: Baseline revenue
            base_spending: Baseline spending
            parameter_ranges: Dict of param_name -> (min%, max%)
            years: Projection years
        
        Returns:
            DataFrame for tornado chart
        """
        results = []
        baseline_deficit = (base_spending - base_revenue) * years
        
        for param_name, (min_val, max_val) in parameter_ranges.items():
            if "revenue" in param_name.lower():
                # Revenue parameter
                min_deficit = (base_spending - base_revenue * (1 + min_val / 100)) * years
                max_deficit = (base_spending - base_revenue * (1 + max_val / 100)) * years
                
                impact_low = min_deficit - baseline_deficit
                impact_high = max_deficit - baseline_deficit
            else:
                # Spending parameter
                min_deficit = (base_spending * (1 + min_val / 100) - base_revenue) * years
                max_deficit = (base_spending * (1 + max_val / 100) - base_revenue) * years
                
                impact_low = min_deficit - baseline_deficit
                impact_high = max_deficit - baseline_deficit
            
            # Use low end for negative range, high end for positive
            impact_range = max(abs(impact_low), abs(impact_high))
            
            results.append({
                "Parameter": param_name,
                "Negative Impact": min(impact_low, impact_high),
                "Positive Impact": max(impact_low, impact_high),
                "Total Range": impact_range,
            })
        
        # Sort by total range
        df = pd.DataFrame(results).sort_values("Total Range", ascending=True)
        return df
    
    @staticmethod
    def elasticity_analysis(
        base_value: float,
        parameter_value: float,
        outcome_sensitivity: float = 1.0,
    ) -> float:
        """
        Calculate elasticity (% change in outcome / % change in parameter).
        
        Args:
            base_value: Baseline value
            parameter_value: Parameter value
            outcome_sensitivity: How sensitive outcome is to this parameter
        
        Returns:
            Elasticity coefficient
        """
        if base_value == 0:
            return 0
        
        pct_change = (parameter_value / base_value - 1) * 100
        elasticity = outcome_sensitivity * pct_change
        return elasticity


class StressTestAnalyzer:
    """Stress test policies under adverse scenarios."""
    
    @staticmethod
    def run_stress_test(
        policy_params: Dict[str, float],
        base_revenue: float = 5_980.0,
        base_spending: float = 6_911.0,
        stress_scenarios: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> pd.DataFrame:
        """
        Run stress tests on a policy under adverse conditions.
        
        Args:
            policy_params: {revenue_change_pct, spending_change_pct}
            base_revenue: Baseline revenue
            base_spending: Baseline spending
            stress_scenarios: Dict of scenario_name -> adjustments
        
        Returns:
            DataFrame with stress test results
        """
        if stress_scenarios is None:
            stress_scenarios = {
                "Recession": {"revenue_reduction": -10, "spending_increase": 5},
                "Inflation": {"growth_reduction": -2, "rate_increase": 2},
                "Demographic Shock": {"beneficiaries_increase": 20, "coverage_reduction": -10},
                "Market Correction": {"deficit_increase": 20, "uncertainty": 30},
                "Perfect Storm": {"revenue_reduction": -15, "spending_increase": 10},
            }
        
        results = []
        baseline_deficit = base_spending - base_revenue
        
        # Apply policy
        stressed_revenue = base_revenue * (1 + policy_params.get("revenue_change_pct", 0) / 100)
        stressed_spending = base_spending * (1 + policy_params.get("spending_change_pct", 0) / 100)
        policy_deficit = stressed_spending - stressed_revenue
        
        for scenario_name, adjustments in stress_scenarios.items():
            scenario_revenue = stressed_revenue
            scenario_spending = stressed_spending
            
            # Apply scenario adjustments
            if "revenue_reduction" in adjustments:
                scenario_revenue *= (1 + adjustments["revenue_reduction"] / 100)
            
            if "spending_increase" in adjustments:
                scenario_spending *= (1 + adjustments["spending_increase"] / 100)
            
            # Additional adjustments
            if "deficit_increase" in adjustments:
                scenario_spending *= (1 + adjustments["deficit_increase"] / 100)
            
            scenario_deficit = scenario_spending - scenario_revenue
            deficit_impact = scenario_deficit - policy_deficit
            deficit_pct_change = (deficit_impact / policy_deficit * 100) if policy_deficit != 0 else 0
            
            results.append({
                "Stress Scenario": scenario_name,
                "Baseline Deficit": f"${policy_deficit:,.0f}B",
                "Stressed Deficit": f"${scenario_deficit:,.0f}B",
                "Deficit Impact": f"${deficit_impact:,.0f}B",
                "% Change": f"{deficit_pct_change:+.1f}%",
            })
        
        return pd.DataFrame(results)
