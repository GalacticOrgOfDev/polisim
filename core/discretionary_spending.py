"""
Discretionary Spending Module - Phase 3.2
Federal discretionary budget analysis with scenario modeling.

Components:
- Defense spending projections
- Non-defense discretionary (infrastructure, education, R&D, etc.)
- Historical baseline + CBO projections
- Inflation adjustment and growth scenarios
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Tuple, List


@dataclass
class DiscretionaryAssumptions:
    """2025 baseline assumptions for discretionary spending."""
    
    # 2025 Baseline (FY 2025)
    defense_2025_billions: float = 821.5  # DoD budget authority
    nondefense_discretionary_2025_billions: float = 773.0  # Non-defense discretionary
    
    # Growth rates
    inflation_annual: float = 0.025  # 2.5% inflation baseline
    population_growth_annual: float = 0.007  # 0.7% population growth
    gdp_growth_annual: float = 0.025  # 2.5% GDP growth baseline
    
    # Defense-specific
    force_structure_multiplier: float = 1.0  # 1.0 = current, 1.2 = 20% expansion
    modernization_acceleration: float = 0.0  # Additional spend on modernization
    
    # Non-defense discretionary breakdown (rough percentages of total)
    ndd_education_pct: float = 0.15  # 15% - Education/training/employment
    ndd_infrastructure_pct: float = 0.12  # 12% - Transportation/infrastructure
    ndd_research_pct: float = 0.10  # 10% - Scientific research
    ndd_veterans_pct: float = 0.08  # 8% - Veterans benefits
    ndd_other_pct: float = 0.55  # 55% - Other (justice, agencies, etc.)


class DiscretionarySpendingModel:
    """Projects federal discretionary spending under different scenarios."""
    
    def __init__(self, assumptions: DiscretionaryAssumptions = None):
        self.assumptions = assumptions or DiscretionaryAssumptions()
    
    def project_defense(
        self,
        years: int,
        iterations: int = 10000,
        scenario: str = "baseline"
    ) -> Dict[str, np.ndarray]:
        """
        Project defense spending under specified scenario.
        
        Scenarios:
        - baseline: Inflation only (2.5% annually)
        - growth: Force structure expansion (3.5% annually)
        - reduction: Drawdown (1.5% annually)
        - custom: Use force_structure_multiplier
        
        Returns:
            Dictionary with arrays of shape (iterations, years)
        """
        base = self.assumptions.defense_2025_billions
        
        # Set annual growth rate by scenario
        if scenario == "baseline":
            growth_rate = self.assumptions.inflation_annual
        elif scenario == "growth":
            growth_rate = 0.035  # 3.5%
        elif scenario == "reduction":
            growth_rate = 0.015  # 1.5%
        else:
            # Custom based on force structure multiplier
            growth_rate = self.assumptions.inflation_annual
        
        # Stochastic modeling - add uncertainty
        year_array = np.arange(years)
        
        # Create stochastic paths
        projections = np.zeros((iterations, years))
        
        for i in range(iterations):
            # Add stochastic variation to growth rates (±1%)
            stochastic_rate = growth_rate + np.random.normal(0, 0.01)
            
            for t in range(years):
                projections[i, t] = base * (1 + stochastic_rate) ** (t + 1)
        
        return {
            "defense_billions": projections,
            "mean": projections.mean(axis=0),
            "median": np.median(projections, axis=0),
            "p10": np.percentile(projections, 10, axis=0),
            "p90": np.percentile(projections, 90, axis=0),
        }
    
    def project_nondefense_discretionary(
        self,
        years: int,
        iterations: int = 10000,
        scenario: str = "baseline"
    ) -> Dict[str, np.ndarray]:
        """
        Project non-defense discretionary spending.
        
        Scenarios:
        - baseline: Inflation only
        - growth: Increase by 2.5% above inflation (hiring, programs)
        - reduction: Reduce by 1% annually (efficiency)
        - infrastructure: 4% annual increase (infrastructure focus)
        """
        base = self.assumptions.nondefense_discretionary_2025_billions
        
        if scenario == "baseline":
            growth_rate = self.assumptions.inflation_annual
        elif scenario == "growth":
            growth_rate = 0.05  # 5% growth
        elif scenario == "reduction":
            growth_rate = 0.015  # 1.5%
        elif scenario == "infrastructure":
            growth_rate = 0.04  # 4% (infrastructure focus)
        else:
            growth_rate = self.assumptions.inflation_annual
        
        # Stochastic paths
        projections = np.zeros((iterations, years))
        
        for i in range(iterations):
            stochastic_rate = growth_rate + np.random.normal(0, 0.01)
            
            for t in range(years):
                projections[i, t] = base * (1 + stochastic_rate) ** (t + 1)
        
        return {
            "nondefense_billions": projections,
            "mean": projections.mean(axis=0),
            "median": np.median(projections, axis=0),
            "p10": np.percentile(projections, 10, axis=0),
            "p90": np.percentile(projections, 90, axis=0),
        }
    
    def project_all_discretionary(
        self,
        years: int,
        iterations: int = 10000,
        defense_scenario: str = "baseline",
        nondefense_scenario: str = "baseline"
    ) -> pd.DataFrame:
        """
        Project all discretionary spending and return DataFrame.
        
        Returns:
            DataFrame with columns:
            - year
            - defense_mean, defense_p10, defense_p90
            - nondefense_mean, nondefense_p10, nondefense_p90
            - total_mean, total_p10, total_p90
        """
        defense = self.project_defense(years, iterations, defense_scenario)
        nondefense = self.project_nondefense_discretionary(years, iterations, nondefense_scenario)
        
        total_mean = defense["mean"] + nondefense["mean"]
        total_p10 = defense["p10"] + nondefense["p10"]
        total_p90 = defense["p90"] + nondefense["p90"]
        
        year_array = np.arange(years) + 2026  # Start from 2026
        
        return pd.DataFrame({
            "year": year_array,
            "defense_mean": defense["mean"],
            "defense_p10": defense["p10"],
            "defense_p90": defense["p90"],
            "nondefense_mean": nondefense["mean"],
            "nondefense_p10": nondefense["p10"],
            "nondefense_p90": nondefense["p90"],
            "total_mean": total_mean,
            "total_p10": total_p10,
            "total_p90": total_p90,
        })
    
    def get_10year_totals(
        self,
        defense_scenario: str = "baseline",
        nondefense_scenario: str = "baseline"
    ) -> Dict[str, float]:
        """Get 10-year discretionary spending totals."""
        df = self.project_all_discretionary(10, 10000, defense_scenario, nondefense_scenario)
        
        return {
            "defense_10year_billions": df["defense_mean"].sum(),
            "nondefense_10year_billions": df["nondefense_mean"].sum(),
            "total_10year_billions": df["total_mean"].sum(),
            "defense_avg_annual_billions": df["defense_mean"].mean(),
            "nondefense_avg_annual_billions": df["nondefense_mean"].mean(),
        }
    
    def get_split_by_category(
        self,
        years: int,
        iterations: int = 10000,
        nondefense_scenario: str = "baseline"
    ) -> pd.DataFrame:
        """
        Break down non-defense discretionary by category.
        
        Returns:
            DataFrame with education, infrastructure, research, veterans, other columns
        """
        ndd_proj = self.project_nondefense_discretionary(years, iterations, nondefense_scenario)
        ndd_mean = ndd_proj["mean"]
        
        # Apply percentage breakdown
        education = ndd_mean * self.assumptions.ndd_education_pct
        infrastructure = ndd_mean * self.assumptions.ndd_infrastructure_pct
        research = ndd_mean * self.assumptions.ndd_research_pct
        veterans = ndd_mean * self.assumptions.ndd_veterans_pct
        other = ndd_mean * self.assumptions.ndd_other_pct
        
        year_array = np.arange(years) + 2026
        
        return pd.DataFrame({
            "year": year_array,
            "education": education,
            "infrastructure": infrastructure,
            "research": research,
            "veterans": veterans,
            "other": other,
        })
