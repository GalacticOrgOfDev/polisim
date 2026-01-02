"""
Federal Revenue Modeling Module - CBO 2.0 Phase 2
Monte Carlo projection of federal revenues across all major sources.

Covers:
- Individual income tax
- Payroll taxes (Social Security & Medicare)
- Corporate income tax
- Excise taxes
- Other revenues
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Constants for revenue modeling calculations
STANDARD_DEVIATION_TAX_REVENUE = 0.02  # 2% standard deviation for tax revenue uncertainty
CORPORATE_PROFIT_GDP_ELASTICITY = 2.0  # Corporate profits grow 2x GDP growth rate
SOCIAL_SECURITY_SHARE_OF_PAYROLL = 0.55  # SS receives 55% of payroll taxes
MEDICARE_SHARE_OF_PAYROLL = 0.45  # Medicare receives 45% of payroll taxes

# Default growth assumptions
DEFAULT_GDP_GROWTH = 0.02  # 2% baseline GDP growth
DEFAULT_WAGE_GROWTH = 0.03  # 3% baseline wage growth
DEFAULT_INFLATION = 0.025  # 2.5% baseline inflation

# Uncertainty parameters
GDP_GROWTH_UNCERTAINTY = 0.02  # 2% std dev for GDP growth
WAGE_GROWTH_UNCERTAINTY = 0.02  # 2% std dev for wage growth
EXCISE_OTHER_REVENUE_UNCERTAINTY = 0.03  # 3% std dev for excise/other revenues

# Tax reform impact factors
CAP_REMOVAL_IMPACT_FACTOR = 0.15  # 15% revenue increase from removing SS cap
CORPORATE_RATE_BEHAVIORAL_RESPONSE = 0.8  # 80% static revenue estimate due to behavioral response

# Log thresholds
LOG_ITERATION_INTERVAL = 1000  # Log every N iterations


@dataclass
class IndividualIncomeTaxAssumptions:
    """Individual income tax parameters (2025 baseline)."""

    # Tax brackets (2025)
    tax_brackets: List[Tuple[float, float]] = field(
        default_factory=lambda: [
            (0, 0.10),
            (11_000, 0.12),
            (44_725, 0.22),
            (95_375, 0.24),
            (182_100, 0.32),
            (231_250, 0.35),
            (578_125, 0.37),
        ]
    )

    # Standard deductions by filing status (2025)
    standard_deduction_single: float = 14_600
    standard_deduction_married: float = 29_200
    standard_deduction_hoh: float = 21_900

    # Credits
    child_tax_credit: float = 2_000
    earned_income_tax_credit_max: float = 3_995

    # Effective rates by income percentile (for validation)
    effective_rate_by_percentile: Dict[str, float] = field(
        default_factory=lambda: {
            "p10": 0.00,
            "p50": 0.05,
            "p90": 0.15,
            "p99": 0.30,
        }
    )

    @classmethod
    def cbo_2025_baseline(cls) -> "IndividualIncomeTaxAssumptions":
        """CBO 2025 baseline assumptions."""
        return cls()


@dataclass
class PayrollTaxAssumptions:
    """Payroll tax parameters (Social Security & Medicare)."""

    # Social Security
    social_security_rate: float = 0.062  # Employee + employer = 12.4%
    social_security_cap: float = 168_600  # 2025 cap

    # Medicare
    medicare_rate: float = 0.029  # Employee + employer = 2.9%
    medicare_additional_rate: float = 0.009  # 0.9% above $200k
    medicare_cap: Optional[float] = None  # No cap for standard Medicare

    # Wage growth assumptions
    wage_growth_rate: float = 0.030  # 3% average annual growth

    @classmethod
    def ssa_2024_trustees(cls) -> "PayrollTaxAssumptions":
        """SSA 2024 Trustees Report assumptions."""
        return cls()


@dataclass
class CorporateIncomeTaxAssumptions:
    """Corporate income tax parameters."""

    # Tax rate (TCJA 2017)
    marginal_tax_rate: float = 0.21

    # Effective rate (includes adjustments)
    effective_tax_rate: float = 0.13

    # Corporate profit assumptions
    corporate_profit_share_of_gdp: float = 0.08  # ~8% of GDP

    # Tax avoidance & sheltering impact
    tax_avoidance_factor: float = 0.85  # Effective collection at 85% of nominal

    @classmethod
    def cbo_2025_baseline(cls) -> "CorporateIncomeTaxAssumptions":
        """CBO 2025 baseline assumptions."""
        return cls()


class FederalRevenueModel:
    """
    Comprehensive federal revenue projection system.

    Projects all major revenue sources with Monte Carlo uncertainty:
    - Individual income tax
    - Payroll taxes (Social Security + Medicare)
    - Corporate income tax
    - Excise taxes (simplified)
    - Other revenues (simplified)
    """

    def __init__(
        self,
        individual_income_tax: Optional[IndividualIncomeTaxAssumptions] = None,
        payroll_taxes: Optional[PayrollTaxAssumptions] = None,
        corporate_income_tax: Optional[CorporateIncomeTaxAssumptions] = None,
        start_year: int = 2025,
        baseline_revenues_billions: Optional[Dict[str, float]] = None,
        seed: Optional[int] = None,
    ):
        """Initialize revenue model."""
        self.iit = individual_income_tax or IndividualIncomeTaxAssumptions.cbo_2025_baseline()
        self.payroll = payroll_taxes or PayrollTaxAssumptions.ssa_2024_trustees()
        self.corporate = corporate_income_tax or CorporateIncomeTaxAssumptions.cbo_2025_baseline()
        self.start_year = start_year
        self.seed = seed
        
        # Input validation
        if self.iit.tax_brackets and len(self.iit.tax_brackets) > 0:
            top_rate = self.iit.tax_brackets[-1][1]  # Get rate from last bracket
            if not 0 <= top_rate <= 1:
                raise ValueError(f"Top marginal tax rate {top_rate:.1%} outside reasonable range [0%, 100%]")
        if not 0 <= self.payroll.wage_growth_rate <= 0.5:
            raise ValueError(f"Wage growth {self.payroll.wage_growth_rate:.1%} outside reasonable range [0%, 50%]")
        if not 0 <= self.corporate.marginal_tax_rate <= 1:
            raise ValueError(f"Corporate tax rate {self.corporate.marginal_tax_rate:.1%} outside reasonable range [0%, 100%]")
        
        if seed is not None:
            np.random.seed(seed)
            logger.info(f"Random seed set to {seed} for reproducibility")

        # 2025 baseline revenue estimates (billions)
        self.baseline_revenues = baseline_revenues_billions or {
            "individual_income_tax": 2_176,
            "payroll_taxes": 2_268,
            "corporate_income_tax": 420,
            "excise_taxes": 120,
            "other_revenues": 416,
            "total": 5_400,
        }

        logger.info(f"Revenue Model initialized for {start_year}")
        logger.info(f"  Baseline total revenues: ${self.baseline_revenues['total']:.0f}B")

    def project_individual_income_tax(
        self,
        years: int,
        gdp_growth: np.ndarray,
        wage_growth: np.ndarray,
        iterations: int = 10000,
    ) -> Dict[str, np.ndarray]:
        """
        Project individual income tax revenue.

        Args:
            years: Number of years to project
            gdp_growth: Annual GDP growth rates (years,)
            wage_growth: Annual wage growth rates (years,)
            iterations: Number of Monte Carlo iterations

        Returns:
            Dictionary with revenue projections
        """
        logger.info(f"Projecting IIT for {years} years with {iterations} iterations")

        revenues = np.zeros((years, iterations))
        effective_rates = np.zeros((years, iterations))

        for it in range(iterations):
            if it % 1000 == 0 and it > 0:
                logger.info(f"  Individual income tax projection: {it}/{iterations} iterations ({it/iterations*100:.1f}%)")

            revenue = self.baseline_revenues["individual_income_tax"]

            for year in range(years):
                # Wage growth impact (year-over-year, not cumulative)
                wage_factor = 1 + wage_growth[year]

                # Number of filers growth (~0.5% per year)
                filer_growth = 1.005

                # Tax base growth (year-over-year)
                tax_base_growth = wage_factor * filer_growth

                # Add Monte Carlo noise to growth
                growth_noise = np.random.normal(1.0, 0.03)  # 3% std dev

                # Adjusted revenue projection (simple compounding)
                revenue = revenue * tax_base_growth * growth_noise

                # Effective tax rate (for reference)
                # Protect against division by zero with nested division check
                baseline_iit = self.baseline_revenues.get("individual_income_tax", 0.0)
                if baseline_iit > 0:
                    tax_base = baseline_iit / 0.08
                    if tax_base > 0:
                        effective_rate = revenue / tax_base
                    else:
                        effective_rate = 0.08  # Fallback to default rate
                else:
                    effective_rate = 0.08  # Fallback to default rate

                revenues[year, it] = revenue
                effective_rates[year, it] = effective_rate

        return {
            "revenues": revenues,
            "effective_rates": effective_rates,
            "mean_revenue": np.mean(revenues, axis=1),
            "std_revenue": np.std(revenues, axis=1),
        }

    def project_payroll_taxes(
        self,
        years: int,
        wage_growth: np.ndarray,
        employment: np.ndarray,
        iterations: int = 10000,
    ) -> Dict[str, np.ndarray]:
        """
        Project payroll tax revenue (Social Security + Medicare).

        Args:
            years: Number of years to project
            wage_growth: Annual wage growth rates
            employment: Employment levels
            iterations: Number of Monte Carlo iterations

        Returns:
            Dictionary with revenue projections
        """
        logger.info(f"Projecting payroll taxes for {years} years with {iterations} iterations")

        ss_revenues = np.zeros((years, iterations))
        medicare_revenues = np.zeros((years, iterations))

        for it in range(iterations):
            if it % 1000 == 0 and it > 0:
                logger.info(f"  Payroll tax projection: {it}/{iterations} iterations ({it/iterations*100:.1f}%)")

            ss_revenue = self.baseline_revenues["payroll_taxes"] * SOCIAL_SECURITY_SHARE_OF_PAYROLL
            medicare_revenue = self.baseline_revenues["payroll_taxes"] * MEDICARE_SHARE_OF_PAYROLL

            for year in range(years):
                # Wage base growth (year-over-year, not cumulative)
                wage_factor = 1 + wage_growth[year]
                employment_factor = employment[year] if year < len(employment) else 1.0

                # Social Security cap becomes more binding over time as wages grow
                # Starts at 100% effective, decreases to 95% by end (5% of payroll escapes cap)
                ss_cap_effect = 1.0 - (0.05 * year / years)

                # Add Monte Carlo noise
                noise = np.random.normal(1.0, 0.025)  # 2.5% std dev

                # Project revenues (simple compounding)
                ss_revenue = ss_revenue * wage_factor * employment_factor * ss_cap_effect * noise
                medicare_revenue = medicare_revenue * wage_factor * employment_factor * noise

                ss_revenues[year, it] = ss_revenue
                medicare_revenues[year, it] = medicare_revenue

        total = ss_revenues + medicare_revenues

        return {
            "ss_revenues": ss_revenues,
            "medicare_revenues": medicare_revenues,
            "total_payroll_revenues": total,
            "mean_total": np.mean(total, axis=1),
            "std_total": np.std(total, axis=1),
        }

    def project_corporate_income_tax(
        self,
        years: int,
        gdp_growth: np.ndarray,
        iterations: int = 10000,
    ) -> Dict[str, np.ndarray]:
        """
        Project corporate income tax revenue.

        Highly cyclical and sensitive to profit volatility.

        Args:
            years: Number of years to project
            gdp_growth: Annual GDP growth rates
            iterations: Number of Monte Carlo iterations

        Returns:
            Dictionary with revenue projections
        """
        logger.info(f"Projecting CIT for {years} years with {iterations} iterations")
        
        # H2 Fix: Validate GDP growth rates
        if not isinstance(gdp_growth, np.ndarray):
            raise TypeError(f"GDP growth must be numpy array, got {type(gdp_growth)}")
        if len(gdp_growth) != years:
            raise ValueError(f"GDP growth array length ({len(gdp_growth)}) must match years ({years})")
        if np.any(gdp_growth < -0.10) or np.any(gdp_growth > 0.15):
            invalid_values = gdp_growth[(gdp_growth < -0.10) | (gdp_growth > 0.15)]
            raise ValueError(f"GDP growth rates outside reasonable bounds (-10% to +15%): {invalid_values}")

        revenues = np.zeros((years, iterations))

        for it in range(iterations):
            if it % 1000 == 0 and it > 0:
                logger.info(f"  Corporate income tax projection: {it}/{iterations} iterations ({it/iterations*100:.1f}%)")

            revenue = self.baseline_revenues["corporate_income_tax"]
            
            # M3 Enhancement: Track recession state for loss carryforward logic
            in_recession = False
            years_since_recession = 0

            for year in range(years):
                # Corporate profits highly sensitive to GDP growth
                # Elasticity ~2.0 (1% GDP growth → 2% profit growth)
                profit_growth = 1 + (gdp_growth[year] * CORPORATE_PROFIT_GDP_ELASTICITY)

                # M3 Enhancement: Improved recession handling with multi-year effects
                # Recession defined as GDP growth < -2%
                is_recession_year = gdp_growth[year] < -0.02
                
                if is_recession_year:
                    in_recession = True
                    years_since_recession = 0
                    # During recession: profit decline + loss carryforwards reduce tax revenue
                    recession_impact = 0.75  # 25% revenue reduction from losses
                    logger.debug(f"Iteration {it}, Year {year}: Recession detected (GDP: {gdp_growth[year]:.1%})")
                elif in_recession and years_since_recession < 3:
                    # Post-recession recovery: loss carryforwards still reducing revenue
                    years_since_recession += 1
                    # Gradual recovery: 15% -> 10% -> 5% reduction over 3 years
                    carryforward_reduction = 0.15 - (years_since_recession * 0.05)
                    recession_impact = 1.0 - carryforward_reduction
                    logger.debug(f"Iteration {it}, Year {year}: Post-recession year {years_since_recession}, carryforward reduction: {carryforward_reduction:.1%}")
                    if years_since_recession >= 3:
                        in_recession = False
                else:
                    # Normal years: mild profit volatility only
                    recession_impact = 1.0
                    if np.random.random() < 0.10:  # 10% chance of mild profit decline
                        recession_impact = 0.95  # 5% decline

                # Tax avoidance effects
                tax_avoidance = np.random.normal(
                    self.corporate.tax_avoidance_factor, 0.05
                )  # 5% std dev

                # Add cyclical noise
                noise = np.random.normal(1.0, 0.05)  # 5% std dev

                revenue = (
                    revenue
                    * profit_growth
                    * recession_impact
                    * tax_avoidance
                    * noise
                )

                revenues[year, it] = revenue

        return {
            "revenues": revenues,
            "mean_revenue": np.mean(revenues, axis=1),
            "std_revenue": np.std(revenues, axis=1),
        }

    def project_all_revenues(
        self,
        years: int,
        gdp_growth: Optional[np.ndarray] = None,
        wage_growth: Optional[np.ndarray] = None,
        iterations: int = 10000,
        scenario: str = "baseline",
    ) -> pd.DataFrame:
        """
        Project all federal revenues with scenario differentiation.

        Args:
            years: Number of years to project
            gdp_growth: Annual GDP growth rates (if None, use scenario-specific baseline)
            wage_growth: Annual wage growth rates (if None, use scenario-specific baseline)
            iterations: Number of Monte Carlo iterations
            scenario: Revenue scenario - "baseline", "recession", or "strong_growth"

        Returns:
            DataFrame with detailed revenue projections
        """
        # Scenario-specific growth assumptions
        scenario_params = {
            "baseline": {"gdp_multiplier": 1.0, "wage_multiplier": 1.0},
            "recession": {"gdp_multiplier": 0.5, "wage_multiplier": 0.6},  # Lower growth
            "strong_growth": {"gdp_multiplier": 1.5, "wage_multiplier": 1.4},  # Higher growth
            "demographic_challenge": {"gdp_multiplier": 0.8, "wage_multiplier": 0.9},  # Slower growth due to aging population
        }
        
        if scenario not in scenario_params:
            raise ValueError(f"Unknown scenario: {scenario}. Must be one of {list(scenario_params.keys())}")
        
        scenario_config = scenario_params[scenario]
        
        # Default growth assumptions if not provided - apply scenario multipliers
        if gdp_growth is None:
            gdp_growth = np.full(years, DEFAULT_GDP_GROWTH * scenario_config["gdp_multiplier"])
        else:
            gdp_growth = gdp_growth * scenario_config["gdp_multiplier"]
        
        # Type assertion to satisfy type checker
        assert isinstance(gdp_growth, np.ndarray), "gdp_growth must be numpy array"
            
        if wage_growth is None:
            wage_growth = np.full(years, DEFAULT_WAGE_GROWTH * scenario_config["wage_multiplier"])
        else:
            wage_growth = wage_growth * scenario_config["wage_multiplier"]
        
        # Type assertion to satisfy type checker
        assert isinstance(wage_growth, np.ndarray), "wage_growth must be numpy array"

        logger.info(f"Projecting all revenues for {years} years with {iterations} iterations (scenario: {scenario})")

        # Project individual sources
        iit_results = self.project_individual_income_tax(
            years, gdp_growth, wage_growth, iterations
        )
        payroll_results = self.project_payroll_taxes(
            years, wage_growth, np.ones(years), iterations
        )
        cit_results = self.project_corporate_income_tax(
            years, gdp_growth, iterations
        )

        # Simplified excise & other taxes (grow with GDP)
        excise_revenues = np.zeros((years, iterations))
        other_revenues = np.zeros((years, iterations))

        for it in range(iterations):
            excise_rev = self.baseline_revenues["excise_taxes"]
            other_rev = self.baseline_revenues["other_revenues"]

            for year in range(years):
                growth_factor = 1 + gdp_growth[year]
                noise = np.random.normal(1.0, EXCISE_OTHER_REVENUE_UNCERTAINTY)

                excise_rev = excise_rev * growth_factor * noise
                other_rev = other_rev * growth_factor * noise
                excise_revenues[year, it] = excise_rev
                other_revenues[year, it] = other_rev

        # Compile results
        results = []

        for it in range(iterations):
            for year in range(years):
                total_rev = (
                    iit_results["revenues"][year, it]
                    + payroll_results["total_payroll_revenues"][year, it]
                    + cit_results["revenues"][year, it]
                    + excise_revenues[year, it]
                    + other_revenues[year, it]
                )

                results.append(
                    {
                        "year": self.start_year + year,
                        "iteration": it,
                        "scenario": scenario,
                        "individual_income_tax": iit_results["revenues"][year, it],
                        "social_security_tax": payroll_results["ss_revenues"][year, it],
                        "medicare_tax": payroll_results["medicare_revenues"][year, it],
                        "corporate_income_tax": cit_results["revenues"][year, it],
                        "excise_taxes": excise_revenues[year, it],
                        "other_revenues": other_revenues[year, it],
                        "total_revenues": total_rev,
                    }
                )

        df = pd.DataFrame(results)
        logger.info(f"Revenue projections complete: {len(df)} records (scenario: {scenario})")
        return df

    def apply_tax_reform(
        self,
        reform: Dict[str, Any],
        projections: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Model impact of tax policy reforms.

        Supported reforms:
        - 'individual_income_tax_rate_increase': decimal increase (e.g., 0.05 for 5%)
        - 'corporate_tax_rate': new rate (e.g., 0.28)
        - 'payroll_tax_rate_increase': decimal increase
        - 'eliminate_cap': Remove Social Security cap

        Args:
            reform: Dictionary of reform parameters
            projections: Baseline projections to compare against

        Returns:
            Dictionary with reform impact analysis
        """
        logger.info(f"Applying tax reform: {reform}")

        impact = {}

        if "individual_income_tax_rate_increase" in reform:
            increase = reform["individual_income_tax_rate_increase"]
            additional_revenue = self.baseline_revenues["individual_income_tax"] * increase
            impact["iit_additional_revenue"] = additional_revenue
            logger.debug(f"  IIT rate increase: +${additional_revenue:.0f}B annually")

        if "corporate_tax_rate" in reform:
            new_rate = reform["corporate_tax_rate"]
            old_rate = self.corporate.marginal_tax_rate
            rate_change = (new_rate - old_rate) / old_rate
            additional_revenue = self.baseline_revenues["corporate_income_tax"] * rate_change * CORPORATE_RATE_BEHAVIORAL_RESPONSE
            impact["cit_additional_revenue"] = additional_revenue
            logger.debug(f"  CIT rate: {old_rate:.0%} → {new_rate:.0%}, +${additional_revenue:.0f}B")

        if "payroll_tax_rate_increase" in reform:
            increase = reform["payroll_tax_rate_increase"]
            additional_revenue = self.baseline_revenues["payroll_taxes"] * increase
            impact["payroll_additional_revenue"] = additional_revenue
            logger.debug(f"  Payroll tax increase: +${additional_revenue:.0f}B")

        if "eliminate_cap" in reform and reform["eliminate_cap"]:
            # Removing SS cap affects ~15% of workers above cap
            # Use payroll_taxes baseline since there's no separate social_security_tax key
            ss_baseline = self.baseline_revenues.get("social_security_tax") or self.baseline_revenues["payroll_taxes"] * SOCIAL_SECURITY_SHARE_OF_PAYROLL
            cap_effect_revenue = ss_baseline * CAP_REMOVAL_IMPACT_FACTOR
            impact["ss_cap_elimination_revenue"] = cap_effect_revenue
            logger.debug(f"  Remove SS cap: +${cap_effect_revenue:.0f}B")

        total_impact = sum(
            v for k, v in impact.items() if k.endswith("_revenue")
        )
        impact["total_additional_revenue"] = total_impact

        return impact


# Pre-defined tax reform packages
class TaxReforms:
    """Common federal tax reform scenarios."""

    @staticmethod
    def increase_top_rate(increase_pct: float = 0.05) -> Dict[str, Any]:
        """Increase top individual income tax rate."""
        return {
            "name": "increase_top_rate",
            "description": f"Increase top rate by {increase_pct:.1%}",
            "reforms": {"individual_income_tax_rate_increase": increase_pct},
        }

    @staticmethod
    def increase_corporate_rate(new_rate: float = 0.28) -> Dict[str, Any]:
        """Increase corporate income tax rate."""
        return {
            "name": "increase_corporate_rate",
            "description": f"Increase corporate rate to {new_rate:.0%}",
            "reforms": {"corporate_tax_rate": new_rate},
        }

    @staticmethod
    def increase_payroll_tax(increase_pct: float = 0.02) -> Dict[str, Any]:
        """Increase payroll tax rate."""
        return {
            "name": "increase_payroll_tax",
            "description": f"Increase payroll tax by {increase_pct:.1%}",
            "reforms": {"payroll_tax_rate_increase": increase_pct},
        }

    @staticmethod
    def remove_ss_cap() -> Dict[str, Any]:
        """Remove Social Security payroll tax cap."""
        return {
            "name": "remove_ss_cap",
            "description": "Remove Social Security payroll tax cap",
            "reforms": {"eliminate_cap": True},
        }
    
    # Aliases for test compatibility
    @staticmethod
    def increase_individual_income_tax_rate(new_rate: float = 0.42) -> Dict[str, Any]:
        """Alias for increase_top_rate() for test compatibility."""
        return TaxReforms.increase_top_rate(increase_pct=new_rate - 0.37)  # Current top rate is 37%
    
    @staticmethod
    def increase_corporate_income_tax_rate(new_rate: float = 0.25) -> Dict[str, Any]:
        """Alias for increase_corporate_rate() for test compatibility."""
        return TaxReforms.increase_corporate_rate(new_rate=new_rate)
    
    @staticmethod
    def remove_social_security_wage_cap() -> Dict[str, Any]:
        """Alias for remove_ss_cap() for test compatibility."""
        return TaxReforms.remove_ss_cap()
    
    @staticmethod
    def increase_payroll_tax_rate(new_rate: float = 0.145) -> Dict[str, Any]:
        """Alias for increase_payroll_tax() calculating increase from current rate."""
        current_rate = 0.124  # Current combined SS+Medicare rate
        increase = new_rate - current_rate
        return TaxReforms.increase_payroll_tax(increase_pct=increase)
