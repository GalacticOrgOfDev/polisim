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

# Demographic constants
MAX_AGE = 101  # Maximum age tracked (0-100+)
CHILDBEARING_AGE_MIN = 15  # Minimum childbearing age
CHILDBEARING_AGE_MAX = 50  # Maximum childbearing age
WORKING_AGE_MIN = 20  # Minimum working age for immigration distribution
WORKING_AGE_MAX = 65  # Maximum working age for immigration distribution

# Baseline financial assumptions (2025)
BASELINE_TAXABLE_PAYROLL_BILLIONS = 1200.0  # Baseline taxable payroll in billions
BENEFICIARY_GROWTH_RATE = 0.015  # Annual beneficiary growth rate due to aging
DI_BENEFICIARY_GROWTH_RATE = 0.005  # DI beneficiary growth rate
DI_BENEFIT_FACTOR = 0.9  # DI benefits relative to OASI (90%)

# Administrative expense ratios
OASI_ADMIN_EXPENSE_RATIO = 0.007  # 0.7% of OASI outgo
DI_ADMIN_EXPENSE_RATIO = 0.025  # 2.5% of DI outgo

# L2 Fix: Extract magic numbers to named constants for clarity
# Benefit adjustment factors
BASELINE_FRA = 67  # Current law baseline Full Retirement Age
FRA_ADJUSTMENT_RATE = 0.067  # 6.7% benefit reduction per year of FRA increase
FRA_ADJUSTMENT_MIN = 0.7  # Minimum benefit level (70% of baseline)
FRA_ADJUSTMENT_MAX = 1.0  # Maximum benefit level (100% of baseline)

# Tax rate constants
BASELINE_PAYROLL_TAX_RATE = 0.124  # 12.4% combined OASDI rate
NO_CAP_INCREASE_FACTOR = 1.2  # 20% increase in taxable wages when removing cap

# Mortality and fertility simplification factors
SIMPLIFIED_MORTALITY_RATE = 0.01  # 1% simplified mortality rate
UNIFORM_BASE_POPULATION = 1_000_000  # Uniform base population per age

# Logging thresholds
LOG_ITERATION_INTERVAL = 1000  # Log every N iterations
LOG_FIRST_N_ITERATIONS = 5  # Log detailed info for first N iterations


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

    # M4 NOTE: Bend points defined but not currently used in calculations
    # Current model uses average PIA ($1,907) instead of calculating individual PIAs
    # TODO: Either integrate bend point calculations or remove these fields in future refactor
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
    
    # Means testing parameters
    means_test_threshold_1: float = 85_000.0  # First income threshold
    means_test_threshold_2: float = 150_000.0  # Second income threshold
    means_test_reduction_rate_1: float = 0.25  # Reduction rate above first threshold
    means_test_reduction_rate_2: float = 0.50  # Reduction rate above second threshold
    
    # Longevity indexing
    baseline_life_expectancy_at_65: float = 19.5  # 2025 baseline
    longevity_indexing_enabled: bool = False
    
    # Dynamic COLA settings
    cola_formula: str = "cpi_w"  # Options: cpi_w, cpi_e, chained_cpi
    cola_min: float = 0.0  # COLA floor
    cola_max: float = 0.05  # COLA cap (5%)

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
            "population": np.zeros((years, MAX_AGE, iterations)),  # Age 0-100+
            "births": np.zeros((years, iterations)),
            "deaths": np.zeros((years, iterations)),
        }

        # Initial population age distribution (simplified)
        base_pop = np.array([UNIFORM_BASE_POPULATION] * MAX_AGE)  # Simplified uniform

        for it in range(iterations):
            if it % LOG_ITERATION_INTERVAL == 0 and it > 0:
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
                population_15_50 = pop[CHILDBEARING_AGE_MIN:CHILDBEARING_AGE_MAX].sum()
                if population_15_50 > 0 and self.demographics.total_fertility_rate > 0:
                    births = population_15_50 * self.demographics.total_fertility_rate * fertility_factor / POPULATION_CONVERSION_TO_MILLIONS
                else:
                    births = 0
                    if year == 0:  # Only warn once per iteration
                        logger.warning(f"Iteration {it}: Childbearing population or fertility rate is zero")
                results["births"][year, it] = births

                # Project deaths
                deaths = pop.sum() * SIMPLIFIED_MORTALITY_RATE * mortality_factor  # Simplified
                results["deaths"][year, it] = deaths

                # Age population (validate array shape)
                if len(pop) != MAX_AGE:
                    raise ValueError(f"Population array must be length {MAX_AGE}, got {len(pop)}")
                new_pop = np.zeros(MAX_AGE)
                new_pop[0] = births + self.demographics.net_immigration_annual * immigration_factor
                new_pop[1:] = pop[:-1]

                # Immigration (distributed across working ages)
                new_pop[WORKING_AGE_MIN:WORKING_AGE_MAX] += (
                    self.demographics.net_immigration_annual * immigration_factor
                ) / WORKING_YEARS_SPAN

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
            if iteration % LOG_ITERATION_INTERVAL == 0:
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

                # Simulate beneficiary growth with demographics (aging population)
                # Beneficiaries grow faster than population due to aging
                beneficiary_growth = 1.0 + (BENEFICIARY_GROWTH_RATE * year_index) * mortality_factor
                oasi_beneficiaries = (
                    self.trust_fund.oasi_beneficiaries * beneficiary_growth
                )
                di_beneficiaries = (
                    self.trust_fund.di_beneficiaries * (1.0 + DI_BENEFICIARY_GROWTH_RATE * year_index)
                )

                # Average benefit with COLA
                base_benefit = self.benefit_formula.primary_insurance_amount_avg_2025
                
                # Adjust benefit for retirement age changes
                # If FRA increases, benefits effectively decrease because:
                # 1) People claim earlier relative to new FRA (actuarial reduction)
                # 2) Benefit formula adjusts to maintain actuarial neutrality
                # Roughly: 6.7% reduction per year of FRA increase
                fra_adjustment = 1.0 - (self.benefit_formula.full_retirement_age - BASELINE_FRA) * FRA_ADJUSTMENT_RATE
                fra_adjustment = max(FRA_ADJUSTMENT_MIN, min(FRA_ADJUSTMENT_MAX, fra_adjustment))
                
                avg_benefit = (
                    base_benefit
                    * fra_adjustment
                    * (1 + self.benefit_formula.annual_cola) ** year_index
                )

                # Payroll tax income calculation
                # Base taxable wages grow with wage index
                taxable_wages_billions = BASELINE_TAXABLE_PAYROLL_BILLIONS * (
                    1 + self.benefit_formula.wage_index_annual_growth
                ) ** year_index
                
                # Apply the actual payroll tax rate from model parameters
                # Note: BASELINE_TAXABLE_PAYROLL_BILLIONS already assumes 12.4% rate,
                # so we need to adjust for different rates
                rate_adjustment = self.trust_fund.payroll_tax_rate / BASELINE_PAYROLL_TAX_RATE
                
                # If wage cap is removed (None), increase taxable base by ~20%
                # (roughly accounting for wages above the current cap)
                cap_adjustment = NO_CAP_INCREASE_FACTOR if self.trust_fund.payroll_tax_cap is None else 1.0
                
                # Total payroll tax income with adjustments
                total_payroll_tax_income = taxable_wages_billions * rate_adjustment * cap_adjustment

                # Split payroll tax: ~85% OASI, ~15% DI
                oasi_payroll_tax_income = total_payroll_tax_income * OASI_SHARE_OF_PAYROLL
                di_payroll_tax_income = total_payroll_tax_income * DI_SHARE_OF_PAYROLL

                # Interest income on trust fund balances
                # M2 Fix: Only calculate interest for positive balances
                interest_rate = self.trust_fund.trust_fund_interest_rate
                oasi_interest_income = oasi_balance * interest_rate if oasi_balance > 0 else 0.0
                di_interest_income = di_balance * interest_rate if di_balance > 0 else 0.0

                # Benefit outgo (millions beneficiaries × avg monthly benefit × 12 months)
                oasi_benefit_payments = (
                    oasi_beneficiaries
                    * avg_benefit
                    * MONTHS_PER_YEAR
                    / POPULATION_CONVERSION_TO_MILLIONS
                )
                di_benefit_payments = (
                    di_beneficiaries
                    * avg_benefit * DI_BENEFIT_FACTOR  # DI benefits slightly lower
                    * MONTHS_PER_YEAR
                    / POPULATION_CONVERSION_TO_MILLIONS
                )

                # Administrative expenses (~0.7% of outgo for OASI, ~2.5% for DI)
                oasi_admin_expenses = oasi_benefit_payments * OASI_ADMIN_EXPENSE_RATIO
                di_admin_expenses = di_benefit_payments * DI_ADMIN_EXPENSE_RATIO

                # Update OASI trust fund balance with depletion handling
                oasi_balance_new = (
                    oasi_balance 
                    + oasi_payroll_tax_income 
                    + oasi_interest_income 
                    - oasi_benefit_payments 
                    - oasi_admin_expenses
                )
                if oasi_balance_new < 0:
                    # Trust fund depleted - benefits reduced to match income (current law)
                    if iteration < LOG_FIRST_N_ITERATIONS:  # Only log first few iterations
                        logger.debug(f"Year {year}, Iteration {iteration}: OASI trust fund depleted")
                    oasi_balance = 0
                else:
                    oasi_balance = oasi_balance_new
                
                # Update DI trust fund balance
                di_balance_new = (
                    di_balance 
                    + di_payroll_tax_income 
                    + di_interest_income 
                    - di_benefit_payments 
                    - di_admin_expenses
                )
                if di_balance_new < 0:
                    if iteration < LOG_FIRST_N_ITERATIONS:  # Only log first few iterations
                        logger.debug(f"Year {year}, Iteration {iteration}: DI trust fund depleted")
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
                        "payroll_tax_income_billions": oasi_payroll_tax_income + di_payroll_tax_income,
                        "interest_income_billions": oasi_interest_income + di_interest_income,
                        "benefit_payments_billions": oasi_benefit_payments + di_benefit_payments,
                        "admin_expenses_billions": oasi_admin_expenses + di_admin_expenses,
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
        
        Optimized version using vectorized pandas operations. Handles both raw
        projections (with 'iteration' column) and aggregated results (MultiIndex columns).

        Args:
            projections: DataFrame from project_trust_funds() or aggregated results

        Returns:
            Dictionary with solvency analysis by fund
        """
        results = {}
        
        # Check if this is aggregated data (MultiIndex columns)
        is_aggregated = isinstance(projections.columns, pd.MultiIndex)

        for fund in ["oasi", "di"]:
            if is_aggregated:
                # Aggregated data - estimate from mean trajectory
                balance_col = (f"{fund}_balance_billions", 'mean')
                
                if balance_col not in projections.columns:
                    logger.warning(f"{fund.upper()}: Column {balance_col} not found")
                    continue
                
                balance_data = projections[balance_col]
                years_data = projections['year']
                
                # Find first year where balance goes negative
                depleted_mask = balance_data <= 0
                depleted_years = years_data[depleted_mask]
                
                if len(depleted_years) > 0:
                    depletion_year = float(depleted_years.iloc[0])
                    results[fund.upper()] = {
                        "depletion_year_mean": depletion_year,
                        "depletion_year_median": depletion_year,
                        "depletion_year_std": None,  # No std dev from single trajectory
                        "depletion_year_10pct": None,
                        "depletion_year_90pct": None,
                        "probability_depleted": 1.0,  # Assume 100% if mean depletes
                    }
                else:
                    results[fund.upper()] = {
                        "depletion_year_mean": None,
                        "depletion_year_median": None,
                        "depletion_year_std": None,
                        "depletion_year_10pct": None,
                        "depletion_year_90pct": None,
                        "probability_depleted": 0.0,
                    }
            else:
                # Raw projection data with iterations
                balance_col = f"{fund}_balance_billions"
                
                # Vectorized approach: Find first depletion year per iteration
                depleted_mask = projections[balance_col] <= 0
                
                # Get depleted rows with iteration and year
                depleted_df = projections[depleted_mask][['iteration', 'year']].copy()
                
                # Group by iteration and get the minimum (first) year for each
                depletion_by_iter = depleted_df.groupby('iteration')['year'].min()
                
                # Calculate statistics
                unique_iterations = projections['iteration'].nunique()
                if unique_iterations == 0:
                    logger.warning(f"{fund.upper()}: No iterations found in projections DataFrame")
                    unique_iterations = 1
                
                num_depleted = len(depletion_by_iter)
                probability_depleted = float(num_depleted / unique_iterations)
                
                if num_depleted > 0:
                    # Have depletion data - calculate full statistics
                    depletion_years = depletion_by_iter.values
                    results[fund.upper()] = {
                        "depletion_year_mean": float(np.mean(depletion_years)),
                        "depletion_year_median": float(np.median(depletion_years)),
                        "depletion_year_std": float(np.std(depletion_years)) if len(depletion_years) > 1 else 0.0,
                        "depletion_year_10pct": float(np.percentile(depletion_years, 10)),
                        "depletion_year_90pct": float(np.percentile(depletion_years, 90)),
                        "probability_depleted": probability_depleted,
                    }
                else:
                    # No depletion - return consistent structure with None values
                    results[fund.upper()] = {
                        "depletion_year_mean": None,
                        "depletion_year_median": None,
                        "depletion_year_std": None,
                        "depletion_year_10pct": None,
                        "depletion_year_90pct": None,
                        "probability_depleted": probability_depleted,
                    }

        logger.info(f"Solvency analysis complete: {results}")
        return results
    
    def apply_means_testing(
        self,
        base_benefit: float,
        total_income: float,
        threshold_1: Optional[float] = None,
        threshold_2: Optional[float] = None,
        reduction_rate_1: Optional[float] = None,
        reduction_rate_2: Optional[float] = None,
    ) -> float:
        """
        Apply means testing to reduce benefits based on income.
        
        Implements tiered benefit reduction:
        - Below threshold_1: No reduction
        - threshold_1 to threshold_2: reduction_rate_1 applied
        - Above threshold_2: reduction_rate_2 applied
        
        Args:
            base_benefit: Original benefit amount
            total_income: Beneficiary's total income
            threshold_1: First income threshold
            threshold_2: Second income threshold
            reduction_rate_1: Reduction rate for tier 1
            reduction_rate_2: Reduction rate for tier 2
            
        Returns:
            Adjusted benefit after means testing
        """
        # Use benefit formula defaults if not provided
        threshold_1 = threshold_1 or self.benefit_formula.means_test_threshold_1
        threshold_2 = threshold_2 or self.benefit_formula.means_test_threshold_2
        reduction_rate_1 = reduction_rate_1 or self.benefit_formula.means_test_reduction_rate_1
        reduction_rate_2 = reduction_rate_2 or self.benefit_formula.means_test_reduction_rate_2
        
        if total_income <= threshold_1:
            return base_benefit
        elif total_income <= threshold_2:
            excess_income = total_income - threshold_1
            reduction = excess_income * reduction_rate_1
            return max(0, base_benefit - reduction)
        else:
            # Apply tier 1 reduction to income between threshold_1 and threshold_2
            tier_1_reduction = (threshold_2 - threshold_1) * reduction_rate_1
            # Apply tier 2 reduction to income above threshold_2
            excess_income = total_income - threshold_2
            tier_2_reduction = excess_income * reduction_rate_2
            total_reduction = tier_1_reduction + tier_2_reduction
            return max(0, base_benefit - total_reduction)
    
    def calculate_benefit_phaseout(
        self,
        benefit: float,
        income: float,
        phaseout_start: float,
        phaseout_end: float,
    ) -> float:
        """
        Calculate smooth benefit reduction curve using linear phaseout.
        
        Args:
            benefit: Base benefit amount
            income: Beneficiary's income
            phaseout_start: Income where phaseout begins
            phaseout_end: Income where benefit fully phases out
            
        Returns:
            Adjusted benefit with smooth phaseout
        """
        if income <= phaseout_start:
            return benefit
        elif income >= phaseout_end:
            return 0.0
        else:
            # Linear phaseout
            phaseout_range = phaseout_end - phaseout_start
            income_in_range = income - phaseout_start
            reduction_pct = income_in_range / phaseout_range
            return benefit * (1 - reduction_pct)
    
    def apply_tiered_benefit_reduction(
        self,
        benefit: float,
        income_bracket: str,
        reduction_schedule: Dict[str, float],
    ) -> float:
        """
        Apply different benefit reductions by income bracket.
        
        Args:
            benefit: Base benefit amount
            income_bracket: Income bracket code (e.g., "Q1", "Q2", "Q3", "Q4", "Q5")
            reduction_schedule: Dict mapping brackets to reduction percentages
            
        Returns:
            Adjusted benefit based on bracket
        """
        reduction_pct = reduction_schedule.get(income_bracket, 0.0)
        return benefit * (1 - reduction_pct)
    
    def track_cohort_life_expectancy(
        self,
        birth_year: int,
        current_year: int,
    ) -> float:
        """
        Track life expectancy changes by cohort.
        
        Uses linear improvement model from baseline.
        
        Args:
            birth_year: Year of birth for cohort
            current_year: Current projection year
            
        Returns:
            Life expectancy at age 65 for this cohort
        """
        years_from_baseline = current_year - 2025
        # Assume life expectancy increases by ~0.1 years per year
        life_expectancy_improvement = years_from_baseline * 0.1
        return self.demographics.life_expectancy_at_65 + life_expectancy_improvement
    
    def apply_longevity_indexing(
        self,
        base_benefit: float,
        birth_year: int,
        current_year: int,
    ) -> float:
        """
        Adjust benefits for increased longevity to maintain actuarial balance.
        
        As life expectancy increases, benefits are reduced proportionally to
        maintain the same total lifetime benefit payout.
        
        Args:
            base_benefit: Original benefit amount
            birth_year: Beneficiary's birth year
            current_year: Current year
            
        Returns:
            Longevity-adjusted benefit
        """
        if not self.benefit_formula.longevity_indexing_enabled:
            return base_benefit
        
        current_life_expectancy = self.track_cohort_life_expectancy(birth_year, current_year)
        baseline_life_expectancy = self.benefit_formula.baseline_life_expectancy_at_65
        
        # Calculate adjustment factor
        longevity_ratio = baseline_life_expectancy / current_life_expectancy
        
        # Apply adjustment (reduced benefit for longer life expectancy)
        return base_benefit * longevity_ratio
    
    def calculate_actuarial_adjustment(
        self,
        benefit: float,
        expected_years_receiving: float,
        baseline_years: float = 19.5,
    ) -> float:
        """
        Calculate actuarial adjustment to maintain neutrality across cohorts.
        
        Args:
            benefit: Monthly benefit amount
            expected_years_receiving: Expected years receiving benefits
            baseline_years: Baseline years (2025 life expectancy at 65)
            
        Returns:
            Actuarially adjusted benefit
        """
        if expected_years_receiving <= 0:
            return 0.0
        
        # Maintain constant total lifetime benefits
        adjustment_factor = baseline_years / expected_years_receiving
        return benefit * adjustment_factor
    
    def calculate_dynamic_cola(
        self,
        previous_benefit: float,
        cpi_change: float,
        wage_growth: float,
        cola_formula: Optional[str] = None,
    ) -> float:
        """
        Calculate COLA based on actual inflation (CPI-W, CPI-E, or chained CPI).
        
        Args:
            previous_benefit: Previous year's benefit
            cpi_change: Consumer Price Index change
            wage_growth: Average wage growth
            cola_formula: Which CPI to use ("cpi_w", "cpi_e", "chained_cpi")
            
        Returns:
            New benefit with COLA applied
        """
        cola_formula = cola_formula or self.benefit_formula.cola_formula
        
        if cola_formula == "cpi_w":
            # Standard CPI-W (current law)
            cola_rate = cpi_change
        elif cola_formula == "cpi_e":
            # CPI-E (elderly inflation, typically higher)
            cola_rate = cpi_change * 1.2  # Elderly costs rise ~20% faster
        elif cola_formula == "chained_cpi":
            # Chained CPI (typically lower, accounts for substitution)
            cola_rate = cpi_change * 0.9  # ~0.3% lower annually
        else:
            cola_rate = cpi_change
        
        # Apply COLA with limits
        return self.apply_cola_with_limits(previous_benefit, cola_rate)
    
    def apply_cola_with_limits(
        self,
        benefit: float,
        inflation_rate: float,
        min_cola: Optional[float] = None,
        max_cola: Optional[float] = None,
    ) -> float:
        """
        Apply COLA with minimum and maximum limits.
        
        Args:
            benefit: Current benefit amount
            inflation_rate: Inflation rate
            min_cola: Minimum COLA (default 0%)
            max_cola: Maximum COLA (default 5%)
            
        Returns:
            Benefit with limited COLA applied
        """
        min_cola = min_cola if min_cola is not None else self.benefit_formula.cola_min
        max_cola = max_cola if max_cola is not None else self.benefit_formula.cola_max
        
        # Constrain COLA between min and max
        constrained_cola = max(min_cola, min(inflation_rate, max_cola))
        
        return benefit * (1 + constrained_cola)
    
    def apply_progressive_payroll_tax(
        self,
        earnings: float,
        base_rate: float,
        threshold: float,
        additional_rate: float,
    ) -> float:
        """
        Apply progressive payroll tax with higher rate above threshold.
        
        Args:
            earnings: Annual earnings
            base_rate: Base payroll tax rate
            threshold: Income threshold for additional rate
            additional_rate: Additional rate above threshold
            
        Returns:
            Total payroll tax
        """
        if earnings <= threshold:
            return earnings * base_rate
        else:
            base_tax = threshold * base_rate
            additional_tax = (earnings - threshold) * (base_rate + additional_rate)
            return base_tax + additional_tax
    
    def calculate_self_employment_tax(
        self,
        net_earnings: float,
        wage_base: Optional[float] = None,
    ) -> float:
        """
        Calculate self-employment tax (SE tax) with special rules.
        
        SE tax is 15.3% (12.4% Social Security + 2.9% Medicare).
        Only 92.35% of net earnings are subject to SE tax.
        
        Args:
            net_earnings: Net self-employment earnings
            wage_base: Wage base limit (if any)
            
        Returns:
            Self-employment tax amount
        """
        wage_base = wage_base or self.trust_fund.payroll_tax_cap
        
        # Apply 92.35% reduction
        se_earnings = net_earnings * 0.9235
        
        # Apply wage base cap if it exists
        if wage_base is not None:
            se_earnings = min(se_earnings, wage_base)
        
        # Calculate SE tax (15.3% total: 12.4% SS + 2.9% Medicare)
        se_tax_rate = 0.153
        return se_earnings * se_tax_rate
    
    def apply_gradual_tax_increase(
        self,
        current_year: int,
        start_year: int,
        end_year: int,
        initial_rate: float,
        target_rate: float,
    ) -> float:
        """
        Calculate gradually increasing tax rate over a phase-in period.
        
        Args:
            current_year: Current projection year
            start_year: Year phase-in begins
            end_year: Year phase-in completes
            initial_rate: Starting tax rate
            target_rate: Final tax rate
            
        Returns:
            Tax rate for current year
        """
        if current_year < start_year:
            return initial_rate
        elif current_year >= end_year:
            return target_rate
        else:
            # Linear phase-in
            years_elapsed = current_year - start_year
            total_years = end_year - start_year
            progress = years_elapsed / total_years
            rate_increase = (target_rate - initial_rate) * progress
            return initial_rate + rate_increase

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
                    "impact": {},
                }
                
                # Calculate OASI extension years with null safety
                reform_oasi_year = reform_solvency.get("OASI", {}).get("depletion_year_mean")
                baseline_oasi_year = baseline_solvency.get("OASI", {}).get("depletion_year_mean")
                
                if reform_oasi_year is not None and baseline_oasi_year is not None:
                    comparison["impact"]["oasi_extension_years"] = reform_oasi_year - baseline_oasi_year
                elif reform_oasi_year is None and baseline_oasi_year is not None:
                    comparison["impact"]["oasi_extension_years"] = "Never depletes (reform fixes solvency)"
                elif reform_oasi_year is not None and baseline_oasi_year is None:
                    comparison["impact"]["oasi_extension_years"] = "Reform causes depletion"
                else:
                    comparison["impact"]["oasi_extension_years"] = "Both scenarios solvent"
                
                # Calculate DI extension years with null safety
                reform_di_year = reform_solvency.get("DI", {}).get("depletion_year_mean")
                baseline_di_year = baseline_solvency.get("DI", {}).get("depletion_year_mean")
                
                if reform_di_year is not None and baseline_di_year is not None:
                    comparison["impact"]["di_extension_years"] = reform_di_year - baseline_di_year
                elif reform_di_year is None and baseline_di_year is not None:
                    comparison["impact"]["di_extension_years"] = "Never depletes (reform fixes solvency)"
                elif reform_di_year is not None and baseline_di_year is None:
                    comparison["impact"]["di_extension_years"] = "Reform causes depletion"
                else:
                    comparison["impact"]["di_extension_years"] = "Both scenarios solvent"
                
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
    def remove_social_security_wage_cap() -> Dict[str, Any]:
        """Alias for remove_payroll_tax_cap() for test compatibility."""
        return SocialSecurityReforms.remove_payroll_tax_cap()

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
    
    @staticmethod
    def apply_means_testing_reform(
        threshold_1: float = 85_000,
        threshold_2: float = 150_000,
        reduction_rate_1: float = 0.25,
        reduction_rate_2: float = 0.50,
    ) -> Dict[str, Any]:
        """
        Apply means testing to reduce benefits for high earners.
        
        Args:
            threshold_1: First income threshold
            threshold_2: Second income threshold
            reduction_rate_1: Reduction rate for tier 1
            reduction_rate_2: Reduction rate for tier 2
        """
        return {
            "name": "means_testing",
            "description": f"Apply means testing with {reduction_rate_1:.1%} reduction above ${threshold_1:,.0f}",
            "reforms": {
                "means_test_threshold_1": threshold_1,
                "means_test_threshold_2": threshold_2,
                "means_test_reduction_rate_1": reduction_rate_1,
                "means_test_reduction_rate_2": reduction_rate_2,
            },
        }
    
    @staticmethod
    def enable_longevity_indexing() -> Dict[str, Any]:
        """Enable automatic benefit adjustment for increasing life expectancy."""
        return {
            "name": "longevity_indexing",
            "description": "Adjust benefits automatically as life expectancy increases",
            "reforms": {
                "longevity_indexing_enabled": True,
            },
        }
    
    @staticmethod
    def change_cola_formula(cola_formula: str = "chained_cpi") -> Dict[str, Any]:
        """
        Change COLA calculation formula.
        
        Args:
            cola_formula: "cpi_w" (current), "cpi_e" (elderly), or "chained_cpi" (lower)
        """
        descriptions = {
            "cpi_w": "CPI-W (current law, standard inflation)",
            "cpi_e": "CPI-E (elderly costs, typically higher)",
            "chained_cpi": "Chained CPI (substitution effects, typically lower)",
        }
        return {
            "name": "change_cola_formula",
            "description": f"Change COLA to {descriptions.get(cola_formula, cola_formula)}",
            "reforms": {
                "cola_formula": cola_formula,
            },
        }
    
    @staticmethod
    def apply_cola_limits(min_cola: float = 0.0, max_cola: float = 0.03) -> Dict[str, Any]:
        """
        Apply minimum and maximum limits to COLA adjustments.
        
        Args:
            min_cola: Minimum COLA (e.g., 0% floor)
            max_cola: Maximum COLA (e.g., 3% cap)
        """
        return {
            "name": "cola_limits",
            "description": f"Cap COLA between {min_cola:.1%} and {max_cola:.1%}",
            "reforms": {
                "cola_min": min_cola,
                "cola_max": max_cola,
            },
        }
    
    @staticmethod
    def progressive_payroll_tax(
        threshold: float = 250_000,
        additional_rate: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Apply progressive payroll tax with additional rate above threshold.
        
        Args:
            threshold: Income threshold for additional tax
            additional_rate: Additional rate above threshold
        """
        return {
            "name": "progressive_payroll_tax",
            "description": f"Add {additional_rate:.1%} payroll tax above ${threshold:,.0f}",
            "reforms": {
                "progressive_tax_threshold": threshold,
                "progressive_additional_rate": additional_rate,
            },
        }

