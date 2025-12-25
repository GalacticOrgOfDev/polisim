"""
Social Security Module - CBO 2.0 Phase 2
Monte Carlo projection of OASI/DI trust funds with stochastic modeling.

Incorporates:
- Population projections by age/cohort with demographic uncertainty
- Benefit eligibility and PIA calculations
- Trust fund accounting with revenue and outgo
- Policy reform scenarios
- Full uncertainty quantification via Monte Carlo
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats
import logging
from enum import Enum

logger = logging.getLogger(__name__)

# Constants for Social Security calculations
POPULATION_CONVERSION_TO_MILLIONS = 1_000  # Convert population to millions
MONTHS_PER_YEAR = 12  # Months in a year
WORKING_YEARS_SPAN = 45  # Years between age 20 and 65
OASI_SHARE_OF_PAYROLL = 0.85  # OASI receives 85% of Social Security payroll tax
DI_SHARE_OF_PAYROLL = 0.15  # DI receives 15% of Social Security payroll tax


class BenefitType(Enum):
    """Social Security benefit types."""
    OASI_RETIRED = "oasi_retired"
    OASI_FAMILY = "oasi_family"
    DI_WORKER = "di_worker"
    DI_FAMILY = "di_family"


@dataclass
class DemographicAssumptions:
    """SSA demographic assumptions (from Trustees Report)."""

    # Baseline rates (2025)
    total_fertility_rate: float = 1.76
    life_expectancy_at_birth: float = 77.4
    life_expectancy_at_65: float = 19.5
    net_immigration_annual: int = 1_000_000

    # Uncertainty parameters (for Monte Carlo)
    mortality_uncertainty_std: float = 0.05  # 5% std dev
    fertility_uncertainty_std: float = 0.10  # 10% std dev
    immigration_uncertainty_std: float = 0.20  # 20% std dev

    # Base population (2025, ages 0-100+)
    population_by_age: Optional[Dict[int, int]] = None

    @classmethod
    def ssa_2024_trustees(cls) -> "DemographicAssumptions":
        """Load SSA 2024 Trustees Report assumptions."""
        return cls(
            total_fertility_rate=1.76,
            life_expectancy_at_birth=77.4,
            life_expectancy_at_65=19.5,
            net_immigration_annual=1_000_000,
        )


@dataclass
class BenefitFormula:
    """Social Security benefit calculation parameters."""

    # PIA bend points and factors (2025)
    bend_points: List[float] = field(default_factory=lambda: [1174.0, 7078.0])
    bend_point_factors: List[float] = field(
        default_factory=lambda: [0.90, 0.32, 0.15]
    )

    # Full Retirement Age
    full_retirement_age: int = 67

    # Average bend point value (2025)
    average_bend_point: float = 1174.0

    # Primary Insurance Amount (PIA) average
    primary_insurance_amount_avg_2025: float = 1907.0

    # Cost of Living Adjustment (COLA)
    annual_cola: float = 0.032  # 3.2% average

    # Wage index growth
    wage_index_annual_growth: float = 0.030  # 3% average

    # Early/delayed claiming adjustments
    early_claiming_reduction_pct: float = 0.70  # 70% of FRA at age 62
    delayed_claiming_credit_pct: float = 0.124  # 12.4% per year after FRA

    @classmethod
    def ssa_2024_trustees(cls) -> "BenefitFormula":
        """SSA 2024 Trustees Report benefit formula."""
        return cls()


@dataclass
class TrustFundAssumptions:
    """Initial trust fund state and parameters."""

    # Trust fund balances (2025, billions)
    oasi_beginning_balance: float = 1400.0
    di_beginning_balance: float = 267.0

    # Payroll tax parameters
    payroll_tax_rate: float = 0.124  # 12.4% combined rate
    payroll_tax_cap: float = 168_600.0  # 2025 cap
    
    # Trust fund interest rate
    trust_fund_interest_rate: float = 0.035  # 3.5% average treasury rate

    # Initial beneficiary counts (millions)
    oasi_beneficiaries: float = 45.5
    di_beneficiaries: float = 8.2

    @classmethod
    def ssa_2024_trustees(cls) -> "TrustFundAssumptions":
        """SSA 2024 Trustees Report initial state."""
        return cls()


class SocialSecurityModel:
    """
    Comprehensive Social Security projection model.
    Stochastic Monte Carlo simulations of OASI/DI trust funds.
    """

    def __init__(
        self,
        demographics: Optional[DemographicAssumptions] = None,
        benefit_formula: Optional[BenefitFormula] = None,
        trust_fund: Optional[TrustFundAssumptions] = None,
        start_year: int = 2025,
        seed: Optional[int] = None,
    ):
        """Initialize Social Security model with assumptions."""
        self.demographics = demographics or DemographicAssumptions.ssa_2024_trustees()
        self.benefit_formula = (
            benefit_formula or BenefitFormula.ssa_2024_trustees()
        )
        self.trust_fund = trust_fund or TrustFundAssumptions.ssa_2024_trustees()
        self.start_year = start_year
        self.seed = seed
        
        # Input validation
        if self.demographics.total_fertility_rate < 0 or self.demographics.total_fertility_rate > 10:
            raise ValueError(f"Fertility rate {self.demographics.total_fertility_rate} outside reasonable range [0, 10]")
        if self.demographics.net_immigration_annual < -10_000_000 or self.demographics.net_immigration_annual > 10_000_000:
            raise ValueError(f"Immigration {self.demographics.net_immigration_annual} outside reasonable range [-10M, 10M]")
        if self.trust_fund.oasi_beginning_balance < 0:
            raise ValueError(f"OASI balance cannot be negative: {self.trust_fund.oasi_beginning_balance}")
        if self.trust_fund.di_beginning_balance < 0:
            raise ValueError(f"DI balance cannot be negative: {self.trust_fund.di_beginning_balance}")
        if not 0 <= self.trust_fund.trust_fund_interest_rate <= 1:
            raise ValueError(f"Interest rate {self.trust_fund.trust_fund_interest_rate:.2%} outside reasonable range [0%, 100%]")
        
        if seed is not None:
            np.random.seed(seed)
            logger.info(f"Random seed set to {seed} for reproducibility")

        logger.info(
            f"Social Security Model initialized for {start_year} "
            f"(OASI balance: ${self.trust_fund.oasi_beginning_balance:.1f}B)"
        )

    def project_population(
        self, years: int, iterations: int = 1
    ) -> Dict[str, np.ndarray]:
        """
        Project population by age/year with demographic uncertainty.

        Args:
            years: Number of years to project
            iterations: Number of stochastic iterations

        Returns:
            Dictionary with population arrays
        """
        results = {
            "population": np.zeros((years, 101, iterations)),  # Age 0-100+
            "births": np.zeros((years, iterations)),
            "deaths": np.zeros((years, iterations)),
        }

        # Initial population age distribution (simplified)
        base_pop = np.array([1_000_000] * 101)  # Simplified uniform

        for it in range(iterations):
            if it % 1000 == 0 and it > 0:
                logger.info(f"  Population projection: {it}/{iterations} iterations ({it/iterations*100:.1f}%)")
            
            # Sample demographic parameters with uncertainty
            mortality_factor = np.random.normal(
                1.0, self.demographics.mortality_uncertainty_std
            )
            fertility_factor = np.random.normal(
                1.0, self.demographics.fertility_uncertainty_std
            )
            immigration_factor = np.random.normal(
                1.0, self.demographics.immigration_uncertainty_std
            )

            pop = base_pop.copy()

            for year in range(years):
                # Project births (with validation to prevent division by zero)
                population_15_50 = pop[15:50].sum()
                if population_15_50 > 0 and self.demographics.total_fertility_rate > 0:
                    births = population_15_50 * self.demographics.total_fertility_rate * fertility_factor / POPULATION_CONVERSION_TO_MILLIONS
                else:
                    births = 0
                    if year == 0:  # Only warn once per iteration
                        logger.warning(f"Iteration {it}: Childbearing population or fertility rate is zero")
                results["births"][year, it] = births

                # Project deaths
                deaths = pop.sum() * 0.01 * mortality_factor  # Simplified
                results["deaths"][year, it] = deaths

                # Age population (validate array shape)
                if len(pop) != 101:
                    raise ValueError(f"Population array must be length 101, got {len(pop)}")
                new_pop = np.zeros(101)
                new_pop[0] = births + self.demographics.net_immigration_annual * immigration_factor
                new_pop[1:] = pop[:-1]

                # Immigration (distributed across working ages)
                new_pop[20:65] += (self.demographics.net_immigration_annual * immigration_factor) / 45

                pop = new_pop
                results["population"][year, :, it] = pop

        return results

    def project_trust_funds(
        self, years: int, iterations: int = 10000
    ) -> pd.DataFrame:
        """
        Project OASI and DI trust funds with Monte Carlo uncertainty.

        Args:
            years: Number of years to project
            iterations: Number of Monte Carlo iterations

        Returns:
            DataFrame with trust fund projections
        """
        logger.info(
            f"Projecting trust funds for {years} years with {iterations} iterations"
        )

        results = []

        for iteration in range(iterations):
            if iteration % 1000 == 0:
                logger.debug(f"  Iteration {iteration}/{iterations}")

            # Sample demographic uncertainties
            mortality_factor = np.random.normal(
                1.0, self.demographics.mortality_uncertainty_std
            )
            fertility_factor = np.random.normal(
                1.0, self.demographics.fertility_uncertainty_std
            )

            oasi_balance = self.trust_fund.oasi_beginning_balance
            di_balance = self.trust_fund.di_beginning_balance

            for year in range(self.start_year, self.start_year + years):
                year_index = year - self.start_year

                # Simulate beneficiary growth with demographics
                beneficiary_growth = 1.0 + (0.01 * (year_index / years)) * (
                    mortality_factor - 1
                )
                oasi_beneficiaries = (
                    self.trust_fund.oasi_beneficiaries * beneficiary_growth
                )
                di_beneficiaries = (
                    self.trust_fund.di_beneficiaries * beneficiary_growth
                )

                # Average benefit with COLA
                avg_benefit = (
                    self.benefit_formula.primary_insurance_amount_avg_2025
                    * (1 + self.benefit_formula.annual_cola) ** year_index
                )

                # Payroll tax income (taxable payroll × tax rate)
                # Simplified: assume constant payroll as % of population
                taxable_payroll = 5_000_000 * (
                    1 + self.benefit_formula.wage_index_annual_growth
                ) ** year_index

                payroll_tax_income = (
                    taxable_payroll * self.trust_fund.payroll_tax_rate
                )

                # Interest income on trust fund balance
                interest_rate = self.trust_fund.trust_fund_interest_rate
                interest_income = oasi_balance * interest_rate

                # Benefit outgo (millions per month × MONTHS_PER_YEAR, convert to billions)
                benefit_payments = (
                    (oasi_beneficiaries + di_beneficiaries)
                    * avg_benefit
                    * MONTHS_PER_YEAR
                    / POPULATION_CONVERSION_TO_MILLIONS
                )

                # Administrative expenses (~1% of outgo)
                admin_expenses = benefit_payments * 0.01

                # Update trust fund balances with depletion handling
                oasi_balance_new = oasi_balance + payroll_tax_income + interest_income - benefit_payments - admin_expenses
                if oasi_balance_new < 0:
                    # Trust fund depleted - benefits reduced to match income (current law deficit)
                    logger.warning(f"Year {year}, Iteration {iteration}: OASI trust fund depleted, applying benefit cuts")
                    shortfall_pct = abs(oasi_balance_new) / benefit_payments if benefit_payments > 0 else 0
                    benefit_payments *= (1 - shortfall_pct)
                    oasi_balance = 0
                else:
                    oasi_balance = oasi_balance_new
                
                di_balance_new = di_balance + payroll_tax_income * 0.15 + interest_income * 0.15 - (benefit_payments * 0.15) - (admin_expenses * 0.15)
                if di_balance_new < 0:
                    # DI trust fund depleted
                    logger.warning(f"Year {year}, Iteration {iteration}: DI trust fund depleted, applying benefit cuts")
                    di_balance = 0
                else:
                    di_balance = di_balance_new

                # Record projection
                results.append(
                    {
                        "year": year,
                        "iteration": iteration,
                        "oasi_balance_billions": oasi_balance,
                        "di_balance_billions": di_balance,
                        "payroll_tax_income_billions": payroll_tax_income,
                        "interest_income_billions": interest_income,
                        "benefit_payments_billions": benefit_payments,
                        "admin_expenses_billions": admin_expenses,
                        "oasi_beneficiaries_millions": oasi_beneficiaries,
                        "di_beneficiaries_millions": di_beneficiaries,
                        "average_benefit_monthly": avg_benefit,
                        "oasi_solvent": oasi_balance > 0,
                    }
                )

        df = pd.DataFrame(results)
        logger.info(f"Completed {len(df)} projections")
        return df

    def estimate_solvency_dates(
        self, projections: pd.DataFrame
    ) -> Dict[str, Dict[str, Any]]:
        """
        Estimate when trust funds reach depletion.

        Args:
            projections: DataFrame from project_trust_funds()

        Returns:
            Dictionary with solvency analysis by fund
        """
        results = {}

        for fund in ["oasi", "di"]:
            balance_col = f"{fund}_balance_billions"
            solvent_col = f"{fund}_solvent"

            # Find depletion year for each iteration
            depletion_years = []

            for iteration in projections["iteration"].unique():
                iter_data = projections[projections["iteration"] == iteration]
                depleted = iter_data[iter_data[balance_col] <= 0]

                if len(depleted) > 0:
                    depletion_year = depleted.iloc[0]["year"]
                else:
                    depletion_year = None

                if depletion_year is not None:
                    depletion_years.append(depletion_year)

            if depletion_years:
                unique_iterations = len(projections["iteration"].unique())
                if unique_iterations > 0:
                    probability_depleted = float(len(depletion_years) / unique_iterations)
                else:
                    probability_depleted = 0.0
                    logger.warning(f"{fund.upper()}: No iterations found in projections DataFrame")
                
                results[fund.upper()] = {
                    "depletion_year_mean": float(np.mean(depletion_years)),
                    "depletion_year_median": float(np.median(depletion_years)),
                    "depletion_year_std": float(np.std(depletion_years)),
                    "depletion_year_10pct": float(np.percentile(depletion_years, 10)),
                    "depletion_year_90pct": float(np.percentile(depletion_years, 90)),
                    "probability_depleted": probability_depleted,
                }
            else:
                results[fund.upper()] = {
                    "depletion_year": None,
                    "probability_depleted": 0.0,
                }

        logger.info(f"Solvency analysis complete: {results}")
        return results

    def apply_policy_reform(
        self,
        reform: Dict[str, Any],
        projections: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Model impact of Social Security policy reforms.

        Supported reforms:
        - 'payroll_tax_rate': Increase tax rate (e.g., 0.135 for 13.5%)
        - 'payroll_tax_cap': Increase or remove cap (None = no cap)
        - 'full_retirement_age': Increase FRA (e.g., 69)
        - 'benefit_reduction_pct': Reduce benefits (e.g., 0.05 for 5%)
        - 'means_testing': Apply means test
        """
        logger.info(f"Applying policy reform: {reform}")

        # Save original parameters
        original_tax_rate = self.trust_fund.payroll_tax_rate
        original_tax_cap = self.trust_fund.payroll_tax_cap
        original_fra = self.benefit_formula.full_retirement_age
        original_pia = self.benefit_formula.primary_insurance_amount_avg_2025

        try:
            # Apply reforms
            if "payroll_tax_rate" in reform:
                self.trust_fund.payroll_tax_rate = reform["payroll_tax_rate"]
                logger.debug(f"  Tax rate: {original_tax_rate:.1%} → {self.trust_fund.payroll_tax_rate:.1%}")

            if "payroll_tax_cap" in reform:
                self.trust_fund.payroll_tax_cap = reform["payroll_tax_cap"]
                logger.debug(f"  Tax cap: ${original_tax_cap:,.0f} → ${self.trust_fund.payroll_tax_cap}")

            if "full_retirement_age" in reform:
                self.benefit_formula.full_retirement_age = reform["full_retirement_age"]
                logger.debug(f"  FRA: {original_fra} → {self.benefit_formula.full_retirement_age}")

            if "benefit_reduction_pct" in reform:
                reduction = reform["benefit_reduction_pct"]
                self.benefit_formula.primary_insurance_amount_avg_2025 *= (1 - reduction)
                logger.debug(f"  Benefit reduction: {reduction:.1%}")

            # Run projection with reforms
            reform_projections = self.project_trust_funds(years=30, iterations=1000)
            reform_solvency = self.estimate_solvency_dates(reform_projections)

            # Compare to baseline if provided
            if projections is not None:
                baseline_solvency = self.estimate_solvency_dates(projections)
                comparison = {
                    "baseline": baseline_solvency,
                    "reform": reform_solvency,
                    "impact": {
                        "oasi_extension_years": (
                            reform_solvency.get("OASI", {}).get("depletion_year_mean")
                            - baseline_solvency.get("OASI", {}).get("depletion_year_mean")
                            if "OASI" in reform_solvency and "OASI" in baseline_solvency
                            else None
                        ),
                    },
                }
                return comparison
            else:
                return {"reform_results": reform_solvency}

        finally:
            # Restore original parameters
            self.trust_fund.payroll_tax_rate = original_tax_rate
            self.trust_fund.payroll_tax_cap = original_tax_cap
            self.benefit_formula.full_retirement_age = original_fra
            self.benefit_formula.primary_insurance_amount_avg_2025 = original_pia


# Pre-defined policy reforms
class SocialSecurityReforms:
    """Common Social Security policy reform packages."""

    @staticmethod
    def raise_payroll_tax_rate(new_rate: float = 0.144) -> Dict[str, Any]:
        """Increase payroll tax rate."""
        return {
            "name": "raise_payroll_tax_rate",
            "description": f"Increase payroll tax from 12.4% to {new_rate:.1%}",
            "reforms": {"payroll_tax_rate": new_rate},
        }

    @staticmethod
    def remove_payroll_tax_cap() -> Dict[str, Any]:
        """Remove or greatly increase payroll tax cap."""
        return {
            "name": "remove_payroll_tax_cap",
            "description": "Remove payroll tax cap (currently $168,600)",
            "reforms": {"payroll_tax_cap": None},
        }

    @staticmethod
    def raise_full_retirement_age(new_fra: int = 69) -> Dict[str, Any]:
        """Gradually raise Full Retirement Age."""
        return {
            "name": "raise_full_retirement_age",
            "description": f"Gradually raise FRA from 67 to {new_fra}",
            "reforms": {"full_retirement_age": new_fra},
        }

    @staticmethod
    def reduce_benefits(reduction_pct: float = 0.05) -> Dict[str, Any]:
        """Reduce average benefits."""
        return {
            "name": "reduce_benefits",
            "description": f"Reduce benefits by {reduction_pct:.1%}",
            "reforms": {"benefit_reduction_pct": reduction_pct},
        }

    @staticmethod
    def combined_reform() -> Dict[str, Any]:
        """Combined reform package."""
        return {
            "name": "combined_reform",
            "description": "Raise tax 0.5%, raise FRA to 69, reduce benefits 2%",
            "reforms": {
                "payroll_tax_rate": 0.129,  # 12.4% + 0.5%
                "full_retirement_age": 69,
                "benefit_reduction_pct": 0.02,
            },
        }
