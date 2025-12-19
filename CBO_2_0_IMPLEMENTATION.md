# CBO 2.0 Implementation Specification

**Detailed technical specifications for transforming POLISIM into an open-source CBO successor**

---

## 1. Architecture Overview

### 1.1 Core Principles

```
┌─────────────────────────────────────────────────────────┐
│         CBO 2.0 Unified Fiscal Projection Model         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Policy Configuration & Scenario Builder        │   │
│  │  (YAML/JSON interface for all parameters)       │   │
│  └──────────────────────────────────────────────────┘   │
│                        ▲                                  │
│                        │                                  │
│  ┌──────────┬─────────┴──────────┬──────────────────┐   │
│  │          │                    │                  │   │
│  ▼          ▼                    ▼                  ▼   │
│  Healthcare│ Social Security│ Revenue    │ Mandatory   │
│  (Phase 1) │ (Phase 2)     │ (Phase 2)  │ Spending    │
│            │               │            │ (Phase 3)   │
│  ┌─────┐   │ ┌──────────┐  │┌─────────┐ │┌────────┐  │
│  │HC   │   │ │OASI/DI   │  ││Inc Tax  │ ││Medicare│  │
│  │Mkt  │   │ │Trust     │  ││Payroll  │ ││Medicaid│  │
│  │Reform   │ │Funds     │  ││Corp Tax │ ││Veterans│  │
│  └─────┘   │ └──────────┘  │└─────────┘ │└────────┘  │
│            │                │            │             │
│  ┌──────────────────────────────────────────────────┐   │
│  │   Macroeconomic Feedback Layer (Phase 3)        │   │
│  │   • GDP growth effects on tax base               │   │
│  │   • Interest rate responses to debt growth       │   │
│  │   • Wage growth & productivity impacts           │   │
│  └──────────────────────────────────────────────────┘   │
│                        ▲                                  │
│                        │                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │    Monte Carlo Engine (100K+ iterations)        │   │
│  │    • Stochastic demographic drivers             │   │
│  │    • Correlated economic uncertainties          │   │
│  │    • Outcome distributions & confidence bands   │   │
│  └──────────────────────────────────────────────────┘   │
│                        ▲                                  │
│                        │                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │   Data Integration & Source Management          │   │
│  │   • CBO Economic & Budget Outlook               │   │
│  │   • SSA Trustees Report                         │   │
│  │   • Census Population Projections               │   │
│  │   • CMS Medicare/Medicaid data                  │   │
│  └──────────────────────────────────────────────────┘   │
│                        ▲                                  │
└─────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
    ┌──────────────────┐   ┌──────────────────┐
    │  Web Dashboard   │   │  Report Engine   │
    │  (Streamlit)     │   │  (PDF/HTML/Excel)│
    │  (Phase 4)       │   │  (Phase 4)       │
    └──────────────────┘   └──────────────────┘
```

### 1.2 Design Patterns

1. **Modular Domain Models**: Each fiscal domain (healthcare, SS, revenue, etc.) is an independent module with consistent interface
2. **Configuration-Driven**: All parameters configurable via YAML/JSON; no hardcoding policy assumptions
3. **Stochastic First**: All models support distributions; deterministic projections are special cases
4. **Transparent Assumptions**: Every assumption documented, traced to official source
5. **Validate Continuously**: Automated checks against CBO/SSA baselines

---

## 2. Phase 2 Detailed Specification

### 2.1 Social Security Module (`core/social_security.py`)

#### 2.1.1 Data Model

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

@dataclass
class DemographicAssumptions:
    """SSA demographic assumptions (from Trustees Report)."""
    
    # Mortality
    mortality_rates: Dict[int, float]  # age -> annual probability
    
    # Fertility
    total_fertility_rate: float  # children per woman
    
    # Immigration
    net_immigration_annual: int  # annual net migration
    
    # Life expectancy
    life_expectancy_at_birth: float
    life_expectancy_at_65: float
    
    # Uncertainty (for Monte Carlo)
    mortality_uncertainty: float  # std dev multiplier
    fertility_uncertainty: float
    immigration_uncertainty: float
    
    @classmethod
    def from_ssa_trustees(cls, year: int) -> "DemographicAssumptions":
        """Load official SSA assumptions for given year."""
        # Fetch from config/data_sources or API
        pass

@dataclass
class BenefitFormula:
    """Social Security benefit calculation parameters."""
    
    # Primary Insurance Amount (PIA) calculation
    bend_points: List[float]  # 2025: [1174, 7078]
    bend_point_factors: List[float]  # 0.9, 0.32, 0.15
    
    # Earnings test (for early filers)
    earnings_test_exempt_age: int
    earnings_test_threshold: int
    earnings_reduction_rate: float  # 0.33 or 0.5
    
    # COLAs and indexing
    cost_of_living_adjustment: float
    wage_index_annual_growth: float
    
    # Claiming strategy
    early_claiming_age: int  # 62
    full_retirement_age: int
    delayed_claiming_age: int  # 70
    early_reduction_factor: Dict[int, float]  # age -> % of FRA benefit
    delayed_credits: float  # 8% per year after FRA
    
    @classmethod
    def from_ssa_trustees(cls, year: int) -> "BenefitFormula":
        """Load official SSA benefit formula for given year."""
        pass

@dataclass
class TrustFundProjection:
    """Annual trust fund accounting."""
    
    year: int
    
    # Income side
    payroll_tax_income: float  # billions
    interest_income: float
    taxable_benefits_income: float
    
    # Outgo side
    benefit_payments: float
    administrative_expenses: float
    
    # Fund balance
    beginning_balance: float
    ending_balance: float
    
    # Derived metrics
    income_rate: float  # % of taxable payroll
    outgo_rate: float
    cost_rate: float
    
    @property
    def is_solvent(self) -> bool:
        """Fund has positive balance."""
        return self.ending_balance > 0
    
    @property
    def reserve_ratio(self) -> float:
        """End-of-year reserve as % of annual outgo."""
        return self.ending_balance / self.benefit_payments if self.benefit_payments > 0 else 0

class SocialSecurityModel:
    """
    Comprehensive Social Security projection model.
    
    Incorporates:
    - Population projections (age/cohort)
    - Benefit eligibility & calculations
    - Trust fund accounting
    - Policy reform scenarios
    - Uncertainty quantification
    """
    
    def __init__(
        self,
        demographics: DemographicAssumptions,
        benefit_formula: BenefitFormula,
        start_year: int = 2025,
        base_population: Optional[Dict[int, int]] = None,
    ):
        self.demographics = demographics
        self.benefit_formula = benefit_formula
        self.start_year = start_year
        self.base_population = base_population or self._load_census_baseline()
    
    def project_population(
        self, years: int, iterations: int = 1
    ) -> Dict[str, np.ndarray]:
        """
        Project population by age/year with demographic uncertainty.
        
        Args:
            years: Number of years to project
            iterations: Number of stochastic iterations (1 = deterministic)
        
        Returns:
            {
                'population': array of shape (years, 101, iterations),  # age 0-100+
                'births': array,
                'deaths': array,
                'net_migration': array,
            }
        """
        pass
    
    def calculate_beneficiary_counts(
        self, population: np.ndarray, year: int
    ) -> Dict[str, int]:
        """
        Calculate OASI & DI beneficiary counts by type.
        
        Returns:
            {
                'OASI_retired': count,
                'OASI_family': count,
                'DI_workers': count,
                'DI_family': count,
            }
        """
        pass
    
    def calculate_average_benefits(
        self, year: int, iteration: int = 0
    ) -> Dict[str, float]:
        """
        Calculate average monthly benefit by beneficiary type.
        
        Returns:
            {
                'OASI_retired_PIA': dollars,
                'OASI_family': dollars,
                'DI_worker': dollars,
                'DI_family': dollars,
            }
        """
        pass
    
    def project_trust_funds(
        self, years: int, iterations: int = 10000
    ) -> pd.DataFrame:
        """
        Project OASI and DI trust funds with full stochastic modeling.
        
        Returns DataFrame with columns:
            year, scenario, iteration,
            oasi_beginning_balance, oasi_ending_balance, oasi_reserve_ratio,
            di_beginning_balance, di_ending_balance, di_reserve_ratio,
            payroll_tax_rate, cost_rate, income_rate,
            oasi_solvent, di_solvent,
        
        Shape: (years * iterations, columns)
        """
        pass
    
    def estimate_solvency_dates(
        self, projections: pd.DataFrame, reserve_threshold: float = 0
    ) -> Dict[str, Dict[str, Any]]:
        """
        Estimate when trust funds reach critical levels.
        
        Returns:
            {
                'OASI': {
                    'depletion_year': int,
                    'confidence_interval': (year_10pct, year_90pct),
                    'probability_by_2050': float,
                },
                'DI': {...},
            }
        """
        pass
    
    def apply_policy_reform(
        self, reforms: Dict[str, Any], projections: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Model impact of policy reforms.
        
        Supported reforms (examples):
        {
            'payroll_tax_rate': 0.135,  # Increase from 0.124
            'payroll_tax_cap': 180000,  # Increase from 168600
            'raise_full_retirement_age': True,
            'increase_bend_points': 0.10,  # 10% increase
            'progressive_benefit_reduction': {'top_quartile': 0.25},
            'means_testing': {'income_threshold': 50000, 'reduction_rate': 0.5},
        }
        
        Returns:
            {
                'baseline_oasi_depletion_year': 2035,
                'reform_oasi_depletion_year': 2050,
                'oasi_years_extended': 15,
                'revenue_impact_2050': {'billions': 50},
                'beneficiary_impact': {
                    'average_benefit_reduction_pct': -5,
                    'distribution': array,
                },
            }
        """
        pass
    
    def sensitivity_analysis(
        self,
        parameter: str,
        variation_pct: float = 0.20,
        projections: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on key parameters.
        
        Example:
            sensitivity_analysis('mortality_rates', variation_pct=0.1)
            → Impact on trust fund depletion date of ±0.1% annual mortality change
        """
        pass

@dataclass
class PolicyReform:
    """Template for Social Security policy reforms."""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    
    # Pre-defined common reforms
    @staticmethod
    def raise_payroll_tax_rate() -> "PolicyReform":
        """Increase payroll tax from 12.4% to 14.4%."""
        return PolicyReform(
            name="raise_payroll_tax_rate",
            description="Increase Social Security payroll tax from 12.4% to 14.4%",
            parameters={"payroll_tax_rate": 0.144},
        )
    
    @staticmethod
    def raise_payroll_tax_cap() -> "PolicyReform":
        """Remove or increase payroll tax cap."""
        return PolicyReform(
            name="raise_payroll_tax_cap",
            description="Remove payroll tax cap (currently $168,600)",
            parameters={"payroll_tax_cap": None},  # No cap
        )
    
    @staticmethod
    def gradually_raise_fra() -> "PolicyReform":
        """Gradually increase Full Retirement Age to 69."""
        return PolicyReform(
            name="gradually_raise_fra",
            description="Gradually increase Full Retirement Age from 67 to 69",
            parameters={"full_retirement_age": 69},
        )
    
    @staticmethod
    def means_testing() -> "PolicyReform":
        """Apply means testing to high-income beneficiaries."""
        return PolicyReform(
            name="means_testing",
            description="Apply means test to beneficiaries with income >$50k",
            parameters={
                "means_test_income_threshold": 50000,
                "means_test_reduction_rate": 0.5,
            },
        )
```

#### 2.1.2 Core Methods (Pseudocode)

```python
def project_trust_funds(self, years: int, iterations: int = 10000) -> pd.DataFrame:
    """
    Monte Carlo projection of trust funds.
    
    Algorithm:
    1. For each iteration:
       a. Sample demographic parameters (mortality, fertility, immigration)
       b. Project population by age/year
       c. For each year:
          - Count beneficiaries by type & age
          - Calculate average benefits
          - Calculate payroll tax income (wage base × payroll tax rate)
          - Calculate benefit outgo
          - Update trust fund balance
          - Check solvency
    2. Aggregate across iterations to get distributions
    """
    
    results = []
    
    for iteration in range(iterations):
        # Sample demographic parameters with uncertainty
        mortality = self.demographics.mortality_rates.copy()
        fertility = self.demographics.total_fertility_rate
        immigration = self.demographics.net_immigration_annual
        
        if iterations > 1:  # Add Monte Carlo noise
            mortality = {
                age: rate * np.random.normal(1.0, self.demographics.mortality_uncertainty)
                for age, rate in mortality.items()
            }
            fertility *= np.random.normal(1.0, self.demographics.fertility_uncertainty)
            immigration *= int(np.random.normal(1.0, self.demographics.immigration_uncertainty))
        
        # Project population
        population = self._simulate_population(mortality, fertility, immigration, years)
        
        # Project trust funds
        oasi_balance = self._get_initial_oasi_balance()
        di_balance = self._get_initial_di_balance()
        
        for year in range(self.start_year, self.start_year + years):
            # Beneficiary counts
            retired_workers = self._count_retired_workers(population, year)
            di_workers = self._count_di_workers(population, year)
            
            # Average benefits (with COLA adjustments)
            avg_pia = self.benefit_formula.average_pia * (
                (1 + self.benefit_formula.cost_of_living_adjustment) ** (year - self.start_year)
            )
            
            # Income (payroll tax)
            taxable_payroll = self._estimate_taxable_payroll(population, year)
            payroll_tax_income = taxable_payroll * self.benefit_formula.payroll_tax_rate
            interest_income = oasi_balance * 0.035  # assumed interest rate
            
            # Outgo
            benefit_payments = (retired_workers + di_workers) * avg_pia * 12
            administrative_expenses = benefit_payments * 0.01
            
            # Update balances
            oasi_balance = oasi_balance + payroll_tax_income + interest_income - benefit_payments
            
            # Record
            results.append({
                'year': year,
                'iteration': iteration,
                'oasi_balance': oasi_balance,
                'di_balance': di_balance,
                'payroll_tax_income': payroll_tax_income,
                'benefit_payments': benefit_payments,
                'retired_workers': retired_workers,
                'di_workers': di_workers,
            })
    
    return pd.DataFrame(results)
```

---

### 2.2 Revenue Modeling Module (`core/revenue_modeling.py`)

#### 2.2.1 Data Model

```python
@dataclass
class IndividualIncomeTaxAssumptions:
    """IRS/CBO individual income tax parameters."""
    
    # Tax brackets (2025)
    brackets: List[Tuple[float, float]]  # (income_threshold, rate)
    # Example: [(0, 0.10), (11000, 0.12), (44725, 0.22), ...]
    
    # Standard deduction by filing status
    standard_deduction_single: float
    standard_deduction_married: float
    standard_deduction_head_of_household: float
    
    # Credits and exclusions
    child_tax_credit: float
    earned_income_tax_credit_max: float
    retirement_savings_contribution_credit: float
    
    # Effective rate assumptions by income group (for calibration)
    effective_rate_by_percentile: Dict[int, float]  # 10th, 50th, 90th, 99th
    
    @classmethod
    def from_cbo_baseline(cls, year: int) -> "IndividualIncomeTaxAssumptions":
        """Load CBO historical tax data & assumptions."""
        pass

@dataclass
class PayrollTaxAssumptions:
    """Social Security & Medicare payroll tax parameters."""
    
    social_security_rate: float  # 12.4%
    social_security_cap: float  # $168,600 (2025)
    
    medicare_rate: float  # 2.9%
    medicare_additional_rate: float  # 0.9% above $200k
    medicare_cap: Optional[float]  # None = no cap
    
    # Wage base growth
    wage_index_growth_rate: float
    
    @classmethod
    def from_ssa_trustees(cls, year: int) -> "PayrollTaxAssumptions":
        """Load SSA payroll tax assumptions."""
        pass

@dataclass
class CorporateIncomeTaxAssumptions:
    """Corporate income tax parameters."""
    
    marginal_tax_rate: float  # 21% under TCJA
    average_effective_rate: float  # ~13-15% including adjustments
    
    # Depreciation & incentives
    bonus_depreciation: float  # % of capex
    r_and_d_credit: float  # % of R&D spending
    
    # Corporate profit assumptions
    corporate_profit_share_of_gdp: float
    profit_margin_distribution: Dict[str, float]  # by industry
    
    @classmethod
    def from_cbo_baseline(cls, year: int) -> "CorporateIncomeTaxAssumptions":
        """Load CBO corporate tax data."""
        pass

class FederalRevenueModel:
    """
    Comprehensive federal revenue projection model.
    
    Covers:
    - Individual income tax
    - Payroll taxes (Social Security, Medicare)
    - Corporate income tax
    - Excise taxes
    - Customs duties
    - Estate and gift taxes
    - Other revenues
    """
    
    def __init__(
        self,
        individual_income_tax: IndividualIncomeTaxAssumptions,
        payroll_tax: PayrollTaxAssumptions,
        corporate_income_tax: CorporateIncomeTaxAssumptions,
        start_year: int = 2025,
    ):
        self.iit = individual_income_tax
        self.payroll_tax = payroll_tax
        self.corporate_income_tax = corporate_income_tax
        self.start_year = start_year
    
    def project_individual_income_tax(
        self,
        years: int,
        gdp_growth: np.ndarray,
        wage_growth: np.ndarray,
        iterations: int = 10000,
    ) -> Dict[str, np.ndarray]:
        """
        Project individual income tax revenue.
        
        Drivers:
        - Number of filers (population growth)
        - Wages/salaries (wage growth, labor force participation)
        - Capital gains (linked to stock market, GDP growth)
        - Tax rates (policy, bracket creep via inflation)
        
        Returns:
            {
                'total_revenue': array(years, iterations),
                'by_income_group': Dict[str, array],  # top 1%, top 10%, etc.
                'effective_tax_rate': array,
            }
        """
        pass
    
    def project_payroll_tax(
        self,
        years: int,
        wage_growth: np.ndarray,
        employment: np.ndarray,
        iterations: int = 10000,
    ) -> Dict[str, np.ndarray]:
        """
        Project payroll tax revenue (Social Security + Medicare).
        
        Returns:
            {
                'social_security': array,
                'medicare': array,
                'total': array,
            }
        """
        pass
    
    def project_corporate_income_tax(
        self,
        years: int,
        gdp_growth: np.ndarray,
        profit_growth: np.ndarray,
        iterations: int = 10000,
    ) -> Dict[str, np.ndarray]:
        """
        Project corporate income tax revenue.
        
        Key challenges:
        - Corporate profit volatility
        - Tax avoidance/sheltering
        - Cyclical nature (recession impacts)
        
        Returns:
            {
                'total_revenue': array,
                'effective_rate': array,
            }
        """
        pass
    
    def project_all_revenues(
        self,
        years: int,
        gdp_growth: np.ndarray,
        wage_growth: np.ndarray,
        iterations: int = 10000,
    ) -> pd.DataFrame:
        """
        Project all federal revenues.
        
        Returns DataFrame:
            year, iteration, individual_income_tax, payroll_taxes, corporate_income_tax,
            excise_taxes, customs, estate_tax, other, total_revenues
        """
        pass
    
    def apply_tax_reform(
        self, reforms: Dict[str, Any], projections: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Model impact of tax policy reforms.
        
        Supported reforms:
        {
            'individual_income_tax': {
                'increase_top_bracket_rate': 0.40,
                'lower_top_bracket_threshold': 400000,
                'increase_capital_gains_rate': True,
            },
            'payroll_taxes': {
                'raise_tax_rate': 0.02,
                'remove_cap': True,
            },
            'corporate_income_tax': {
                'increase_rate': 0.28,
                'limit_deductions': True,
            },
        }
        
        Returns:
            {
                'baseline_revenues_2035': billions,
                'reform_revenues_2035': billions,
                'revenue_increase': billions,
                'distributional_impact': Dict,
            }
        """
        pass
    
    def dynamic_scoring(
        self,
        reform: Dict[str, Any],
        behavioral_elasticities: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Include behavioral responses to tax changes.
        
        Example elasticities:
        {
            'labor_supply': -0.3,  # 1% tax increase → 0.3% labor reduction
            'capital_formation': -0.5,
            'savings_rate': -0.2,
            'income_shifting': 0.3,  # Tax avoidance
        }
        
        Returns:
            {
                'static_revenue': billions,
                'behavioral_adjustment': billions,
                'dynamic_revenue': billions,
                'net_effect': billions,
            }
        """
        pass
```

#### 2.2.2 Validation Against CBO Baseline

```python
def validate_against_cbo_baseline(
    model_revenues: np.ndarray,
    cbo_baseline_revenues: np.ndarray,
    tolerance_pct: float = 0.01,
) -> Dict[str, Any]:
    """
    Compare model projections against official CBO baseline.
    
    Returns:
        {
            'mean_error_pct': float,  # Should be < 1%
            'max_error_pct': float,
            'year_by_year_error': array,
            'validation_pass': bool,
            'confidence_intervals': {
                'model_90pct': array,
                'cbo_range': array,
                'overlaps': bool,
            },
        }
    """
    errors = (model_revenues - cbo_baseline_revenues) / cbo_baseline_revenues
    
    return {
        'mean_error_pct': float(np.mean(np.abs(errors))),
        'max_error_pct': float(np.max(np.abs(errors))),
        'validation_pass': np.mean(np.abs(errors)) < tolerance_pct,
    }
```

---

### 2.3 Integration Module (`core/phase2_integrated_model.py`)

```python
class Phase2IntegratedModel:
    """
    Unified Social Security + Revenue + Healthcare model.
    
    Ensures:
    - Consistent demographic assumptions
    - Coordinated macroeconomic drivers
    - Unified reporting of combined fiscal impact
    """
    
    def __init__(
        self,
        healthcare_model: Optional[HealthcareModel] = None,
        social_security_model: SocialSecurityModel,
        revenue_model: FederalRevenueModel,
    ):
        self.healthcare = healthcare_model
        self.social_security = social_security_model
        self.revenue = revenue_model
    
    def project_unified_fiscal_outlook(
        self,
        years: int = 30,
        iterations: int = 10000,
        policy_reforms: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run comprehensive fiscal projection across all three domains.
        
        Returns:
            {
                'healthcare': {...},  # Healthcare model outputs
                'social_security': {...},  # SS model outputs
                'revenues': {...},  # Revenue model outputs
                'combined': {
                    'total_spending': array,
                    'total_revenues': array,
                    'deficit': array,
                    'deficit_to_gdp': array,
                    'debt_held_public': array,
                    'debt_to_gdp': array,
                },
            }
        """
        pass
    
    def compare_policy_packages(
        self,
        baseline_policy: Dict[str, Any],
        alternative_policies: List[Dict[str, Any]],
    ) -> pd.DataFrame:
        """
        Compare multiple policy scenarios.
        
        Returns DataFrame with rows for each alternative,
        columns for key metrics (solvency, revenues, coverage, etc.).
        """
        pass
```

---

## 3. Testing & Validation Strategy

### 3.1 Unit Tests

```python
# tests/test_social_security.py

class TestSocialSecurityProjection:
    """Validate SS module projections against SSA Trustees Report."""
    
    def test_population_projection_matches_census(self):
        """Population projections within 1% of Census Bureau."""
        
    def test_beneficiary_counts_reconciliation(self):
        """Total beneficiaries match official SSA counts."""
        
    def test_oasi_depletion_within_tolerance(self):
        """OASI trust fund depletion year within ±1 year of SSA estimate."""
        # SSA 2024 estimate: 2034
        # Model should estimate 2033-2035 (deterministic)
        
    def test_di_fund_solvency(self):
        """DI fund remains solvent through 2035."""
        
    def test_policy_reform_raises_payroll_tax(self):
        """Raising payroll tax from 12.4% to 14.4% extends solvency."""
        
    def test_policy_reform_raises_fra(self):
        """Raising FRA to 69 extends trust fund solvency."""
        
    def test_monte_carlo_convergence(self):
        """Increasing iterations reduces variance appropriately."""
        # With 10K iterations: std error < 1% of mean
        # With 100K iterations: std error < 0.3% of mean

class TestRevenueModeling:
    """Validate revenue module against CBO baseline."""
    
    def test_individual_income_tax_10yr_baseline(self):
        """IIT projections within ±1% of CBO 2025 baseline."""
        
    def test_payroll_tax_revenue(self):
        """Payroll tax revenue within ±0.5% of SSA estimates."""
        
    def test_corporate_income_tax_cyclicality(self):
        """CIT responds appropriately to profit cycles."""
        
    def test_total_federal_revenue_baseline(self):
        """Total revenues within ±1% of CBO baseline."""
        
    def test_tax_reform_impact(self):
        """Tax rate increase correctly reduces taxpayer behavior."""

class TestPhase2Integration:
    """Validate unified model."""
    
    def test_baseline_projections_consistent(self):
        """Healthcare + SS + Revenue baseline is internally consistent."""
        
    def test_deficit_calculation(self):
        """Spending - Revenue = Deficit (accounting identity)."""
        
    def test_policy_comparison_deterministic(self):
        """Comparing two policies returns consistent ranking."""
        
    def test_monte_carlo_distributions_reasonable(self):
        """Confidence intervals are symmetric and narrow with more iterations."""
```

### 3.2 Validation Checklist

| Component | Target | Test | Status |
|-----------|--------|------|--------|
| SS population projection | ±1% Census | Reconcile with published counts | ⬜ |
| OASI depletion date | ±1 year (2034) | Compare to SSA Trustees | ⬜ |
| DI solvency | 2050+ | Model projects >2050 | ⬜ |
| Individual income tax | ±1% CBO baseline | Compare 10-year projection | ⬜ |
| Payroll tax revenue | ±0.5% SSA | Compare to SSA assumptions | ⬜ |
| Total federal revenue | ±1% CBO baseline | Compare to CBO 2025 outlook | ⬜ |
| Combined healthcare + SS + revenue | ±2% on key metrics | Unified baseline | ⬜ |
| Monte Carlo convergence | <0.3% std error @ 100K | Run 100K iterations, check error | ⬜ |

---

## 4. Configuration & Scenarios

### 4.1 File Structure

```
policies/
├── social_security_baseline.json          # SSA 2024 Trustees Report
├── social_security_pessimistic.json       # Higher mortality, lower immigration
├── social_security_optimistic.json        # Lower mortality, higher wages
├── social_security_reform_raise_cap.json  # Remove payroll tax cap
├── social_security_reform_raise_tax.json  # Increase payroll tax to 14.4%
├── social_security_reform_raise_fra.json  # Gradually increase FRA to 69
├── revenue_baseline.json                  # Current law baseline
├── revenue_reform_tax_increase.json       # 2% across-the-board tax increase
├── revenue_reform_corporate.json          # Corporate rate 21% → 28%
├── phase2_combined_baseline.json          # Healthcare + SS + revenue baseline
└── phase2_combined_reform_package.json    # Integrated package (SS+tax reforms)
```

### 4.2 Configuration Example

```yaml
# policies/social_security_baseline.json
{
  "domain": "social_security",
  "name": "Social Security - 2024 Trustees Report Baseline",
  "year": 2024,
  "source": "https://www.ssa.gov/oact/TR/2024/",
  "demographics": {
    "total_fertility_rate": 1.76,
    "life_expectancy_at_birth": 77.4,
    "net_immigration_annual": 1000000,
    "mortality_assumptions": "SSA 2024 TR Table II.B1"
  },
  "benefit_formula": {
    "full_retirement_age": 67,
    "bend_points": [1174, 7078],
    "bend_point_factors": [0.90, 0.32, 0.15],
    "primary_insurance_amount_2025": 3890,
    "cost_of_living_adjustment": 0.032
  },
  "trust_fund_assumptions": {
    "initial_oasi_balance_billions": 1400,
    "initial_di_balance_billions": 267,
    "payroll_tax_rate": 0.124,
    "payroll_tax_cap": 168600
  },
  "validation": {
    "oasi_depletion_year": 2034,
    "di_depletion_year": null,
    "source": "SSA 2024 Trustees Report"
  }
}
```

---

## 5. Data Sources & APIs

| Data | Source | Update Frequency | Status |
|------|--------|-------------------|--------|
| Population projections | Census Bureau API | Annual | ⬜ Design |
| Mortality rates | CDC Wonder API | Annual | ⬜ Design |
| Wage index growth | SSA OACT database | Annual | ⬜ Design |
| Tax revenue data | IRS SOI tables | Annual | ⬜ Design |
| CBO baseline | CBO website | Twice yearly | ⬜ Manual |
| SSA Trustees Report | SSA OACT | Annual | ⬜ Manual |

---

## 6. Success Criteria Checklist

**Phase 2 Complete When All Are ✅:**

- [ ] Social Security module complete (400+ LOC, fully documented)
- [ ] Revenue modeling module complete (600+ LOC, fully documented)
- [ ] Integration module complete (300+ LOC, fully documented)
- [ ] 50+ test cases, all passing
- [ ] SS projections validate within ±1 year of SSA baseline
- [ ] Revenue projections validate within ±1% of CBO baseline
- [ ] Combined model runs 100K iterations in <2 minutes
- [ ] All configs, scenarios, and examples documented
- [ ] Phase 1 (healthcare) + Phase 2 integration verified
- [ ] MCP server updated with new tools
- [ ] Roadmap & documentation updated for Phase 3

---

**Document Status**: Draft - Ready for Development Kickoff
**Last Updated**: December 19, 2025
