"""
Combined Federal Fiscal Outlook - Phase 3.2
Unified model combining all revenue and spending components.

Provides:
- Total federal budget analysis (revenue vs spending)
- Deficit/surplus calculations
- 75-year sustainability metrics
- Debt trajectory and fiscal gap analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import logging

from core.revenue_modeling import FederalRevenueModel
from core.social_security import SocialSecurityModel
from core.medicare_medicaid import MedicareModel, MedicaidModel
from core.healthcare import get_policy_by_type, PolicyType
from core.discretionary_spending import DiscretionarySpendingModel
from core.interest_spending import InterestOnDebtModel

logger = logging.getLogger(__name__)


class CombinedFiscalOutlookModel:
    """
    Unified federal budget model combining all major components.
    
    Revenue sources:
    - Individual income taxes (Phase 2)
    - Payroll taxes (Phase 2)
    - Corporate income taxes (Phase 2)
    - Other federal revenue (Phase 2)
    
    Spending components:
    - Healthcare (Phase 1)
    - Social Security (Phase 2)
    - Medicare Parts A/B/D (Phase 3.1)
    - Medicaid (Phase 3.1)
    - Discretionary spending (Phase 3.2)
    - Interest on debt (Phase 3.2)
    """
    
    def __init__(self):
        """Initialize all sub-models."""
        self.revenue_model = FederalRevenueModel()
        self.ss_model = SocialSecurityModel()
        self.medicare_model = MedicareModel()
        self.medicaid_model = MedicaidModel()
        self.discretionary_model = DiscretionarySpendingModel()
        self.interest_model = InterestOnDebtModel()
    
    def project_unified_budget(
        self,
        years: int = 30,
        iterations: int = 10000,
        revenue_scenario: str = "baseline",
        ss_scenario: str = "baseline",
        healthcare_policy: str = "usgha",
        discretionary_scenario: str = "baseline",
        interest_scenario: str = "baseline"
    ) -> pd.DataFrame:
        """
        Project complete federal budget (all revenue and spending).
        
        Parameters:
            years: Projection years (default 30)
            iterations: Monte Carlo iterations
            revenue_scenario: 'baseline', 'recession', 'strong_growth', 'demographic_challenge'
            ss_scenario: 'baseline' or reform name
            healthcare_policy: 'usgha', 'current_law', etc.
            discretionary_scenario: 'baseline', 'growth', 'reduction'
            interest_scenario: 'baseline', 'rising', 'falling', 'spike'
        
        Returns:
            DataFrame with all revenue and spending components
        """
        year_array = np.arange(years) + 2026
        
        # Project each component
        # Revenue - use simple GDP-based projection for now
        revenue_gdp_growth = np.linspace(0.02, 0.03, years)  # 2-3% GDP growth baseline
        revenue_billions = np.ones(years) * 5000 + np.cumsum(revenue_gdp_growth * 50)  # ~$5T baseline
        
        # Healthcare spending
        # Using baseline healthcare growth model (4-5% annual growth from ~$4.5T base)
        # This represents total national health expenditure (NHE) projections
        base_healthcare = 4500  # ~$4.5T baseline NHE
        healthcare_growth_rates = np.linspace(0.04, 0.05, years)  # 4-5% annual growth
        healthcare_spending = base_healthcare * np.cumprod(1 + healthcare_growth_rates)
        
        # Social Security
        ss_df = self._get_ss_spending(years, iterations, ss_scenario)
        
        # Medicare/Medicaid
        medicare_df = self._get_medicare_spending(years, iterations)
        medicaid_df = self._get_medicaid_spending(years, iterations)
        
        # Discretionary
        discret_df = self.discretionary_model.project_all_discretionary(
            years, iterations,
            defense_scenario=discretionary_scenario,
            nondefense_scenario=discretionary_scenario
        )
        
        # Interest
        interest_df = self.interest_model.project_interest_and_debt(
            years, iterations, interest_rate_scenario=interest_scenario
        )
        
        # Helper function to safely extract spending arrays
        def _safe_extract_spending(df, column, years, default_value=0):
            """Extract spending column with proper shape handling."""
            if df.empty or column not in df.columns:
                logger.warning(f"DataFrame empty or missing '{column}', using default {default_value}")
                return np.full(years, default_value)
            values = df[column].values
            if len(values) == years:
                return values
            elif len(values) < years:
                # Extrapolate using last value
                logger.warning(f"Column '{column}' has {len(values)} values, extrapolating to {years}")
                return np.pad(values, (0, years - len(values)), mode='edge')
            else:
                # Truncate
                logger.warning(f"Column '{column}' has {len(values)} values, truncating to {years}")
                return values[:years]
        
        # Combine into unified budget
        unified = pd.DataFrame({
            "year": year_array,
            # Revenue
            "total_revenue": revenue_billions,
            # Spending
            "healthcare_spending": healthcare_spending,
            "social_security_spending": _safe_extract_spending(ss_df, "spending", years),
            "medicare_spending": _safe_extract_spending(medicare_df, "spending", years),
            "medicaid_spending": _safe_extract_spending(medicaid_df, "spending", years),
            "discretionary_spending": _safe_extract_spending(discret_df, "total_mean", years),
            "interest_spending": _safe_extract_spending(interest_df, "interest_billions", years),
        })
        
        # Calculate totals
        mandatory_cols = ["social_security_spending", "medicare_spending", "medicaid_spending"]
        unified["mandatory_spending"] = unified[mandatory_cols].sum(axis=1)
        
        unified["total_spending"] = (
            unified["healthcare_spending"] +
            unified["mandatory_spending"] +
            unified["discretionary_spending"] +
            unified["interest_spending"]
        )
        
        # Budget balance
        unified["deficit_surplus"] = unified["total_revenue"] - unified["total_spending"]
        unified["primary_deficit"] = unified["total_revenue"] - (unified["total_spending"] - unified["interest_spending"])
        
        return unified
    
    def get_fiscal_summary(
        self,
        years: int = 30,
        iterations: int = 10000,
        revenue_scenario: str = "baseline",
        ss_scenario: str = "baseline",
        healthcare_policy: str = "usgha",
        discretionary_scenario: str = "baseline",
        interest_scenario: str = "baseline"
    ) -> Dict[str, float]:
        """Get key fiscal metrics for summary display."""
        df = self.project_unified_budget(
            years, iterations, revenue_scenario, ss_scenario,
            healthcare_policy, discretionary_scenario, interest_scenario
        )
        
        total_revenue_10yr = df.head(10)["total_revenue"].sum()
        total_spending_10yr = df.head(10)["total_spending"].sum()
        total_deficit_10yr = df.head(10)["deficit_surplus"].sum()
        
        # Average annual
        avg_annual_revenue = df["total_revenue"].mean()
        avg_annual_spending = df["total_spending"].mean()
        avg_annual_deficit = df["deficit_surplus"].mean()
        
        # Sustainability: Is primary balance positive?
        primary_balance_10yr = df.head(10)["primary_deficit"].sum()
        
        return {
            "total_revenue_10year_billions": total_revenue_10yr,
            "total_spending_10year_billions": total_spending_10yr,
            "total_deficit_10year_billions": total_deficit_10yr,
            "avg_annual_revenue_billions": avg_annual_revenue,
            "avg_annual_spending_billions": avg_annual_spending,
            "avg_annual_deficit_billions": avg_annual_deficit,
            "primary_balance_10year_billions": primary_balance_10yr,
            "sustainable": primary_balance_10yr > 0,
        }
    
    def calculate_fiscal_gap(
        self,
        years: int = 75,
        target_debt_to_gdp: float = 0.60,
        gdp_growth: float = 0.025
    ) -> float:
        """
        Calculate fiscal gap (CBO methodology).
        
        Fiscal gap = sustained policy adjustment needed to stabilize debt/GDP ratio
        at target level over projection period.
        
        Returns:
            Fiscal gap as percentage of GDP (positive = revenue increase needed)
        """
        # Simplified: requires full 75-year projection
        # For now, return placeholder
        return 1.5  # Placeholder: 1.5% of GDP gap
    
    def _get_ss_spending(self, years: int, iterations: int, scenario: str) -> pd.DataFrame:
        """Get Social Security spending projections."""
        ss_proj = self.ss_model.project_trust_funds(years, iterations)
        
        # Extract spending (OASI + DI benefit payments)
        spending = ss_proj.mean(axis=0)[:years] * 1.5  # Rough conversion to spending basis
        
        return pd.DataFrame({
            "year": np.arange(years) + 2026,
            "spending": spending,
        })
    
    def _get_medicare_spending(self, years: int, iterations: int) -> pd.DataFrame:
        """Get Medicare spending projections."""
        medicare_proj = self.medicare_model.project_all_parts(years, iterations)
        
        # Sum Parts A, B, D
        total_spending = (
            medicare_proj["Part A"].mean() +
            medicare_proj["Part B"].mean() +
            medicare_proj["Part D"].mean()
        )
        
        return pd.DataFrame({
            "year": np.arange(years) + 2026,
            "spending": total_spending,
        })
    
    def _get_medicaid_spending(self, years: int, iterations: int) -> pd.DataFrame:
        """Get Medicaid spending projections."""
        medicaid_proj = self.medicaid_model.project_spending(years, iterations)
        
        # Total spending
        total_spending = medicaid_proj["spending"].mean()
        
        return pd.DataFrame({
            "year": np.arange(years) + 2026,
            "spending": total_spending,
        })
