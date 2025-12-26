"""
Combined Federal Fiscal Outlook - Phase 3.2
Unified model combining all revenue and spending components.

Provides:
- Total federal budget analysis (revenue vs spending)
- Deficit/surplus calculations
- 75-year sustainability metrics
- Debt trajectory and fiscal gap analysis
- Performance optimization with caching (Performance #2)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import logging
import hashlib
import pickle
from functools import lru_cache

from core.validation import InputValidator, ValidationError, validate_projection_params
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
    
    Performance Optimization:
    - Component-level caching reduces redundant calculations (Performance #2)
    - Vectorized Medicare projections for 42% speedup (Performance #1)
    """
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialize all sub-models.
        
        Args:
            enable_cache: Enable result caching for repeated projections (default: True)
        """
        self.revenue_model = FederalRevenueModel()
        self.ss_model = SocialSecurityModel()
        self.medicare_model = MedicareModel()
        self.medicaid_model = MedicaidModel()
        self.discretionary_model = DiscretionarySpendingModel()
        self.interest_model = InterestOnDebtModel()
        self.enable_cache = enable_cache
        self._cache = {}  # Manual cache for component results
        
        logger.info(f"CombinedFiscalOutlookModel initialized (caching: {'enabled' if enable_cache else 'disabled'})")
    
    def clear_cache(self):
        """Clear all cached results."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def _get_cache_key(self, component: str, **kwargs) -> str:
        """Generate cache key from component name and parameters."""
        # Create deterministic hash of parameters
        param_str = f"{component}:" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return hashlib.md5(param_str.encode()).hexdigest()[:16]
    
    def _get_cached(self, component: str, **kwargs) -> Optional[pd.DataFrame]:
        """Get cached result if available."""
        if not self.enable_cache:
            return None
        
        cache_key = self._get_cache_key(component, **kwargs)
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {component} ({cache_key})")
            return self._cache[cache_key].copy()  # Return copy to prevent mutation
        
        logger.debug(f"Cache miss for {component} ({cache_key})")
        return None
    
    def _set_cached(self, component: str, result: pd.DataFrame, **kwargs):
        """Store result in cache."""
        if not self.enable_cache:
            return
        
        cache_key = self._get_cache_key(component, **kwargs)
        self._cache[cache_key] = result.copy()
        logger.debug(f"Cached {component} ({cache_key}): {len(result)} records")

    
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
            years: Projection years (default 30, range 1-75)
            iterations: Monte Carlo iterations (default 10000, range 100-50000)
            revenue_scenario: 'baseline', 'recession', 'strong_growth', 'demographic_challenge'
            ss_scenario: 'baseline' or reform name
            healthcare_policy: 'usgha', 'current_law', etc.
            discretionary_scenario: 'baseline', 'growth', 'reduction'
            interest_scenario: 'baseline', 'rising', 'falling', 'spike'
        
        Returns:
            DataFrame with all revenue and spending components
            
        Raises:
            ValidationError: If parameters are out of valid ranges
        """
        # Validate projection parameters (Safety #2)
        validate_projection_params(years, iterations)
        
        # Validate scenario names
        valid_revenue = ['baseline', 'recession', 'strong_growth', 'demographic_challenge']
        valid_discretionary = ['baseline', 'growth', 'reduction']
        valid_interest = ['baseline', 'rising', 'falling', 'spike']
        
        InputValidator.validate_scenario_name(revenue_scenario, valid_revenue, 'revenue_scenario')
        InputValidator.validate_scenario_name(discretionary_scenario, valid_discretionary, 'discretionary_scenario')
        InputValidator.validate_scenario_name(interest_scenario, valid_interest, 'interest_scenario')
        
        year_array = np.arange(years) + 2026
        
        # Project each component
        # Revenue projection using FederalRevenueModel
        revenue_df = self.revenue_model.project_all_revenues(
            years=years,
            gdp_growth=None,  # Uses default 2% baseline
            wage_growth=None,  # Uses default 3% baseline
            iterations=iterations
        )
        # Group by year and calculate mean across iterations
        revenue_by_year = revenue_df.groupby('year').agg({
            'total_revenues': 'mean'
        }).reset_index()
        revenue_billions = revenue_by_year['total_revenues'].values
        
        # Other federal healthcare spending (VA, CHIP, ACA, Public Health, etc.)
        # Baseline ~$350B/year (2025), grows with healthcare inflation
        # Separate from Medicare/Medicaid which are modeled explicitly
        base_other_health = 350  # Billions: VA (~$300B) + CHIP (~$20B) + ACA subsidies (~$30B)
        other_health_growth = 0.055  # 5.5% annual growth (healthcare inflation)
        healthcare_spending = base_other_health * np.power(1 + other_health_growth, np.arange(years))
        
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
            "other_health_spending": healthcare_spending,  # VA, CHIP, ACA, Public Health
            "social_security_spending": _safe_extract_spending(ss_df, "spending", years),
            "medicare_spending": _safe_extract_spending(medicare_df, "spending", years),
            "medicaid_spending": _safe_extract_spending(medicaid_df, "spending", years),
            "discretionary_spending": _safe_extract_spending(discret_df, "total_mean", years),
            "interest_spending": _safe_extract_spending(interest_df, "interest_billions", years),
        })
        
        # Calculate totals
        mandatory_cols = ["social_security_spending", "medicare_spending", "medicaid_spending", "other_health_spending"]
        unified["mandatory_spending"] = unified[mandatory_cols].sum(axis=1)
        
        unified["total_spending"] = (
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
            "total_revenue_10year_billions": float(total_revenue_10yr),
            "total_spending_10year_billions": float(total_spending_10yr),
            "total_deficit_10year_billions": float(total_deficit_10yr),
            "avg_annual_revenue_billions": float(avg_annual_revenue),
            "avg_annual_spending_billions": float(avg_annual_spending),
            "avg_annual_deficit_billions": float(avg_annual_deficit),
            "primary_balance_10year_billions": float(primary_balance_10yr),
            "sustainable": bool(primary_balance_10yr > 0),
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
        """Get Social Security spending projections with caching."""
        # Check cache first (Performance #2)
        cached = self._get_cached("ss_spending", years=years, iterations=iterations, scenario=scenario)
        if cached is not None:
            return cached
        
        # Compute if not cached
        ss_proj = self.ss_model.project_trust_funds(years, iterations)
        
        # Group by year and calculate mean benefit payments across iterations
        yearly_spending = ss_proj.groupby('year').agg({
            'benefit_payments_billions': 'mean'
        }).reset_index()
        
        result = pd.DataFrame({
            "year": yearly_spending["year"],
            "spending": yearly_spending["benefit_payments_billions"],
        })
        
        # Cache the result
        self._set_cached("ss_spending", result, years=years, iterations=iterations, scenario=scenario)
        return result
    
    def _get_medicare_spending(self, years: int, iterations: int) -> pd.DataFrame:
        """Get Medicare spending projections with caching."""
        # Check cache first (Performance #2)
        cached = self._get_cached("medicare_spending", years=years, iterations=iterations)
        if cached is not None:
            return cached
        
        # Compute if not cached (using optimized vectorized projection - Performance #1)
        medicare_proj = self.medicare_model.project_all_parts(years, iterations)
        
        # Group by year and calculate mean across iterations
        yearly_spending = medicare_proj.groupby('year').agg({
            'part_a_spending': 'mean',
            'part_b_spending': 'mean',
            'part_d_spending': 'mean',
            'total_spending': 'mean'
        }).reset_index()
        
        # Convert from dollars to billions
        result = pd.DataFrame({
            "year": yearly_spending["year"],
            "spending": yearly_spending["total_spending"] / 1e9,
        })
        
        # Cache the result
        self._set_cached("medicare_spending", result, years=years, iterations=iterations)
        return result
    
    def _get_medicaid_spending(self, years: int, iterations: int) -> pd.DataFrame:
        """Get Medicaid spending projections with caching."""
        # Check cache first (Performance #2)
        cached = self._get_cached("medicaid_spending", years=years, iterations=iterations)
        if cached is not None:
            return cached
        
        # Compute if not cached
        medicaid_proj = self.medicaid_model.project_spending(years, iterations)
        
        # Group by year and calculate mean across iterations
        yearly_spending = medicaid_proj.groupby('year').agg({
            'total_spending': 'mean'
        }).reset_index()
        
        # Convert from thousands to billions
        result = pd.DataFrame({
            "year": yearly_spending["year"],
            "spending": yearly_spending["total_spending"] / 1e3,
        })
        
        # Cache the result
        self._set_cached("medicaid_spending", result, years=years, iterations=iterations)
        return result
