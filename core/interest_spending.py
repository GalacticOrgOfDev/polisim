"""
Interest on Federal Debt Module - Phase 3.2
Automatic interest expense calculations based on debt dynamics.

Handles:
- Current debt level and composition
- Interest rate modeling (yield curve scenarios)
- Annual interest expense projections
- Sensitivity to interest rate changes
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict


@dataclass
class DebtAssumptions:
    """2025 baseline assumptions for federal debt."""
    
    # Debt levels (billions, FY 2025)
    public_debt_2025_billions: float = 28_000.0  # ~$28 trillion public debt
    intragovernmental_debt_billions: float = 7_100.0  # Social Security/Medicare trust funds
    
    # Debt composition
    bills_pct: float = 0.20  # 20% bills (< 1 year), 3.5% avg rate
    notes_pct: float = 0.45  # 45% notes (1-10 years), 4.0% avg rate
    bonds_pct: float = 0.25  # 25% bonds (20+ years), 4.2% avg rate
    tips_pct: float = 0.10  # 10% TIPS (inflation-indexed), 2.5% real rate
    
    # Interest rates (baseline scenario, per CBO)
    bills_rate_baseline: float = 0.035  # 3.5%
    notes_rate_baseline: float = 0.040  # 4.0%
    bonds_rate_baseline: float = 0.042  # 4.2%
    tips_rate_baseline: float = 0.025  # 2.5% real + inflation
    
    # Interest rate scenarios
    inflation_baseline: float = 0.025  # 2.5% baseline inflation
    
    # Debt growth assumptions
    primary_deficit_annual_billions: float = 500.0  # Deficit before interest
    gdp_growth_annual: float = 0.025  # 2.5% GDP growth


class InterestOnDebtModel:
    """Projects federal interest expenses under different scenarios."""
    
    def __init__(self, assumptions: DebtAssumptions = None):
        self.assumptions = assumptions or DebtAssumptions()
    
    def calculate_current_interest_rate(self) -> float:
        """Calculate weighted average current interest rate on debt."""
        weighted_rate = (
            self.assumptions.bills_pct * self.assumptions.bills_rate_baseline +
            self.assumptions.notes_pct * self.assumptions.notes_rate_baseline +
            self.assumptions.bonds_pct * self.assumptions.bonds_rate_baseline +
            self.assumptions.tips_pct * self.assumptions.tips_rate_baseline
        )
        return weighted_rate
    
    def project_interest_expense(
        self,
        years: int,
        iterations: int = 10000,
        interest_rate_scenario: str = "baseline"
    ) -> Dict[str, np.ndarray]:
        """
        Project annual interest expense on federal debt.
        
        Scenarios:
        - baseline: Rates hold at current levels
        - rising: Rates increase 25 bps per year (monetary tightening)
        - falling: Rates decrease 25 bps per year (recession/monetary easing)
        - spike: Rates jump 100 bps and hold (fiscal crisis)
        
        Returns:
            Dictionary with interest expense projections
        """
        starting_debt = self.assumptions.public_debt_2025_billions
        primary_deficit = self.assumptions.primary_deficit_annual_billions
        gdp_growth = self.assumptions.gdp_growth_annual
        base_rate = self.calculate_current_interest_rate()
        
        # Set rate adjustment scenario
        if interest_rate_scenario == "baseline":
            annual_rate_change = 0.0  # No change
        elif interest_rate_scenario == "rising":
            annual_rate_change = 0.0025  # +25 bps/year
        elif interest_rate_scenario == "falling":
            annual_rate_change = -0.0025  # -25 bps/year
        elif interest_rate_scenario == "spike":
            annual_rate_change = 0.0  # Jump to 5% and hold
        else:
            annual_rate_change = 0.0
        
        # Stochastic projections
        projections = np.zeros((iterations, years))
        debt_track = np.zeros((iterations, years))
        rate_track = np.zeros((iterations, years))
        
        for i in range(iterations):
            current_debt = starting_debt
            
            for t in range(years):
                # Set interest rate for this year
                if interest_rate_scenario == "spike":
                    current_rate = min(0.05, base_rate + 0.01 * (t > 0))  # Jump to 5% in year 1
                else:
                    current_rate = base_rate + (annual_rate_change * (t + 1))
                    # Add stochastic variation (±50 bps)
                    current_rate += np.random.normal(0, 0.005)
                    current_rate = np.clip(current_rate, 0.001, 0.10)  # Bound between 0.1% and 10%
                
                # Calculate interest expense for this year
                interest_expense = current_debt * current_rate
                projections[i, t] = interest_expense
                rate_track[i, t] = current_rate
                
                # Update debt for next year (interest + primary deficit)
                current_debt = current_debt + interest_expense + primary_deficit
                debt_track[i, t] = current_debt
        
        return {
            "interest_billions": projections,
            "debt_billions": debt_track,
            "interest_rate": rate_track,
            "mean": projections.mean(axis=0),
            "median": np.median(projections, axis=0),
            "p10": np.percentile(projections, 10, axis=0),
            "p90": np.percentile(projections, 90, axis=0),
            "debt_mean": debt_track.mean(axis=0),
            "debt_p90": np.percentile(debt_track, 90, axis=0),
        }
    
    def project_interest_and_debt(
        self,
        years: int,
        iterations: int = 10000,
        interest_rate_scenario: str = "baseline"
    ) -> pd.DataFrame:
        """
        Project interest expense and total debt over time.
        
        Returns:
            DataFrame with interest expense, debt levels, and interest rates
        """
        proj = self.project_interest_expense(years, iterations, interest_rate_scenario)
        
        year_array = np.arange(years) + 2026
        
        return pd.DataFrame({
            "year": year_array,
            "interest_billions": proj["mean"],
            "interest_p10": proj["p10"],
            "interest_p90": proj["p90"],
            "debt_billions": proj["debt_mean"],
            "debt_p90": proj["debt_p90"],
            "interest_rate_pct": proj["interest_rate"].mean(axis=0) * 100,
        })
    
    def get_10year_interest_totals(
        self,
        interest_rate_scenario: str = "baseline"
    ) -> Dict[str, float]:
        """Get 10-year interest expense totals."""
        df = self.project_interest_and_debt(10, 10000, interest_rate_scenario)
        
        total_interest = df["interest_billions"].sum()
        avg_annual_interest = df["interest_billions"].mean()
        ending_debt = df["debt_billions"].iloc[-1]
        
        return {
            "total_10year_interest_billions": total_interest,
            "avg_annual_interest_billions": avg_annual_interest,
            "ending_debt_billions": ending_debt,
            "starting_debt_billions": self.assumptions.public_debt_2025_billions,
            "debt_increase_billions": ending_debt - self.assumptions.public_debt_2025_billions,
        }
    
    def interest_rate_sensitivity(
        self,
        years: int = 10,
        rate_change_bps: float = 100.0  # 100 basis points
    ) -> float:
        """
        Calculate how much annual interest expense changes with 100 bps rate increase.
        
        Returns:
            Dollar amount (billions) of additional interest per year (end year basis)
        """
        baseline = self.project_interest_expense(years, 1000, "baseline")
        
        # Manually increase rates
        additional_rate = rate_change_bps / 10000  # Convert to decimal
        additional_interest = (
            self.assumptions.public_debt_2025_billions * additional_rate
        )
        
        return additional_interest
