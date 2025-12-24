"""
Healthcare Policy Modeling Module

Provides comprehensive healthcare policy structures, comparison frameworks,
and economic modeling for government-grade policy analysis.

Policy Models:
- USGHA (United States Galactic Health Act) - Timothy Nordyke proposal
- Current US System (multi-payer, fragmented)
- Medicare-for-All (single-payer, universal)
- UK NHS (public, integrated)
- Canada Single-Payer (provincial, universal)
- UN Proposals (various models)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING
import pandas as pd
from datetime import datetime

if TYPE_CHECKING:
    from core.policy_mechanics_extractor import PolicyMechanics


class PolicyType(Enum):
    """Healthcare policy models"""
    USGHA = "USGHA"  # United States Galactic Health Act
    CURRENT_US = "CURRENT_US"  # Current fragmented US system
    MEDICARE_FOR_ALL = "MEDICARE_FOR_ALL"  # Bernie Sanders-style single-payer
    UK_NHS = "UK_NHS"  # National Health Service (UK)
    CANADA_SP = "CANADA_SP"  # Canadian single-payer
    UN_PROPOSAL = "UN_PROPOSAL"  # UN health initiatives
    AUSTRALIA_MBS = "AUSTRALIA_MBS"  # Australian Medicare + private
    GERMANY_BISMARCK = "GERMANY_BISMARCK"  # German multi-payer model


class TransitionPhase(Enum):
    """Implementation phases"""
    CURRENT = "CURRENT"  # Baseline before reform
    TRANSITION = "TRANSITION"  # During implementation
    MATURE = "MATURE"  # After full implementation


@dataclass
class DrugPricingTier:
    """Pharmaceutical pricing structure"""
    tier_name: str
    price_multiplier: float  # 1.0 = same as baseline, 0.6 = 40% discount
    description: str
    innovation_incentive_multiplier: float = 1.0  # R&D prize multiplier
    examples: List[str] = field(default_factory=list)


@dataclass
class HealthcareCategory:
    """Healthcare spending categories"""
    category_name: str
    current_spending_pct: float  # % of total health spending
    baseline_cost: float  # $ billions annually
    reduction_target: float  # Target reduction % by year X
    description: str
    negotiation_potential: float = 0.3  # Potential cost savings through negotiation


@dataclass
class WorkforceIncentive:
    """Provider and workforce payment structures"""
    role: str  # "primary_care", "specialist", "hospital", "mental_health"
    base_compensation: float  # $ annually
    outcome_multiplier: float  # 1.0 = baseline, 5.0 = max 5x for performance
    underserved_loan_forgiveness: float  # $ total loan forgiveness available
    description: str


@dataclass
class InnovationFund:
    """Medical innovation investment parameters"""
    annual_allocation_pct: float  # % of health spending (12-28%)
    prize_pct: float  # % allocated to prizes (min 65%)
    small_firm_pct: float  # % to small firms (min 35%)
    moonshot_annual_budget: float  # $ billions (ramps to $400B by 2045)
    open_source_pct: float  # % required open-sourced (15%+)
    longevity_priority_tax_credit: float  # Tax credit % for longevity companies
    description: str


@dataclass
class FiscalCircuitBreaker:
    """Automatic fiscal safeguards"""
    spending_gdp_ceiling: float  # Max % of GDP (13% for USGHA)
    trigger_action: str  # What happens when ceiling is hit
    tax_freeze_enabled: bool  # Freeze tax rates until compliant
    surplus_auto_tax_reduction: bool  # Auto reduce taxes on surplus
    surplus_tax_reduction_per_600b: float  # E.g., 1% income tax reduction per $600B surplus
    spending_cut_pct: float = 0.05  # Conservative immediate spending cut (fraction) when triggered
    description: str = ""


@dataclass
class SurplusAllocation:
    """How budget surpluses are distributed"""
    contingency_reserve_pct: float
    national_debt_reduction_pct: float
    infrastructure_education_pct: float
    space_exploration_pct: float
    taxpayer_dividend_pct: float
    dividend_distribution_date: str  # E.g., "April 15"
    description: str


@dataclass
class TransitionTimeline:
    """Implementation schedule"""
    start_year: int
    full_implementation_year: int
    sunset_year: Optional[int]  # None = permanent
    key_milestones: Dict[int, str] = field(default_factory=dict)
    transition_funding_source: str = "Redirection of existing programs"


@dataclass
class HealthcarePolicyModel:
    """Complete healthcare policy specification"""
    policy_type: PolicyType
    policy_name: str
    policy_version: str
    created_date: str
    description: str
    
    # Coverage and access
    universal_coverage: bool
    zero_out_of_pocket: bool
    opt_out_allowed: bool
    emergency_coverage: bool
    coverage_percentage: float  # % of population covered
    
    # Financing
    total_payroll_tax: float  # % of wages
    employer_contribution_pct: float  # % employer paid
    employee_contribution_pct: float  # % employee paid
    general_revenue_pct: float  # % from general tax revenue
    healthcare_spending_target_gdp: float  # Target % GDP (e.g., 9%)
    # Payroll and labor assumptions (optional - used to compute payroll-derived revenue)
    employment_rate: float = 0.60  # Fraction of population employed (0-1)
    avg_annual_wage: float = 65000.0  # Average annual wage in USD
    payroll_coverage_rate: float = 1.0  # Fraction of wages subject to payroll taxes (0-1)
    
    # Fiscal targets - with defaults
    other_funding_sources: Dict[str, float] = field(default_factory=dict)
    debt_elimination_year: Optional[int] = None  # E.g., 2057
    life_expectancy_target: float = 78.0  # E.g., 132 years (USGHA)
    
    # Coverage details
    categories: Dict[str, "HealthcareCategory"] = field(default_factory=dict)
    drug_pricing_tiers: Dict[str, DrugPricingTier] = field(default_factory=dict)
    
    # Workforce and innovation
    workforce_incentives: Dict[str, WorkforceIncentive] = field(default_factory=dict)
    innovation_fund: Optional[InnovationFund] = None
    
    # Safeguards
    circuit_breaker: Optional[FiscalCircuitBreaker] = None
    surplus_allocation: Optional[SurplusAllocation] = None
    
    # Implementation
    transition_timeline: Optional[TransitionTimeline] = None
    
    # Extracted policy mechanics (context-aware)
    mechanics: Optional["PolicyMechanics"] = None
    
    # Anti-fraud and enforcement
    fraud_penalties_multiplier: float = 1.0  # 3.0 = 300% fines
    malpractice_cap_non_economic: Optional[float] = None  # $ cap on non-economic damages
    
    # Administrative overhead
    admin_overhead_pct: float = 0.05  # % of budget consumed by admin
    board_size: int = 1
    board_public_meetings: bool = False
    
    # Performance metrics
    target_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def total_funding_pct(self) -> float:
        """Verify total funding sources sum to 100%"""
        total = (self.general_revenue_pct + self.employer_contribution_pct + 
                self.employee_contribution_pct + sum(self.other_funding_sources.values()))
        return total
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'policy_type': self.policy_type.value,
            'policy_name': self.policy_name,
            'version': self.policy_version,
            'created_date': self.created_date,
            'universal_coverage': self.universal_coverage,
            'coverage_percentage': self.coverage_percentage,
            'healthcare_spending_target_gdp': self.healthcare_spending_target_gdp,
            'admin_overhead_pct': self.admin_overhead_pct,
            'total_payroll_tax': self.total_payroll_tax,
        }


class HealthcarePolicyFactory:
    """Factory for creating standard healthcare policy models"""
    
    @staticmethod
    def create_usgha() -> HealthcarePolicyModel:
        """US Galactic Health Act V0.6
        
        USGHA targets:
        - Healthcare spending: 9% of GDP (document: <7% long-term goal)
        - Fiscal surplus: 1-2% of GDP
        - Zero out-of-pocket costs
        - Full implementation by 2027
        
        Revenue breakdown (dedicated to healthcare):
        - Payroll tax: 15.0% of payroll (for employed workers)
        - Health income tax surcharge: 6.0% of GDP (new dedicated tax)
        - Drug pricing savings: ~0.5% of GDP (negotiation revenue)
        - Administrative overhead savings: ~0.5% of GDP (current US waste reduction)
        Total dedicated: ~12% of GDP for healthcare operations
        
        Plus general federal revenues (already existing):
        - General income tax, corporate tax, etc. provide ~14.7% of GDP
        - Healthcare allocation: ~9% goes to Medicare/Medicaid now
        - USGHA consolidates this plus adds payroll tax surcharge
        """
        policy = HealthcarePolicyModel(
            policy_type=PolicyType.USGHA,
            policy_name="United States Galactic Health Act",
            policy_version="0.6",
            created_date="2025-11-25",
            description="Universal zero-out-of-pocket healthcare with innovation focus. Targets: 7% healthcare spending by 2045, 1-2% fiscal surplus, zero medical bankruptcy.",
            
            universal_coverage=True,
            zero_out_of_pocket=True,
            opt_out_allowed=True,
            emergency_coverage=True,
            coverage_percentage=0.99,
            
            # Healthcare-specific revenue streams (USGHA Section 6)
            # CORRECTED MODEL: USGHA consolidates $5.4T existing US health spending (18.5% GDP)
            # Sources: $1.8T federal + $1.2T employer premiums + $1.0T employee premiums + $1.4T other = $5.4T
            # Revenues start at ~11-12% GDP, sufficient to fund 7% GDP spending + 1-2% surplus + 2% transition costs
            total_payroll_tax=0.0,  # Payroll tax handled via converted premiums below
            employer_contribution_pct=0.0,
            employee_contribution_pct=0.0,
            general_revenue_pct=0.062,  # 6.2% GDP redirected federal health (Medicare/Medicaid/VA/ACA/CHIP)
            other_funding_sources={
                "employer_premiums_converted": 0.041,  # 4.1% GDP - employer health premiums converted to payroll
                "employee_premiums_converted": 0.034,  # 3.4% GDP - employee health premiums converted to payroll
                "mfn_pricing_savings": 0.007,  # 0.7% GDP from MFN-minus-20% pharmaceutical pricing
                "administrative_efficiencies": 0.008,  # 0.8% GDP from reducing 30% admin waste to 3%
                "financial_transaction_tax": 0.003,  # 0.3% GDP from 1% FTT reallocation
                "excise_tax_reallocation": 0.002,  # 0.2% GDP from reallocated excise taxes
                "import_tariffs": 0.004,  # 0.4% GDP from 12% of import tariffs
            },
            # Total revenue: 6.2% + 7.5% (premiums) + 2.4% (other) = 16.1% GDP initially
            # Covers: 7% GDP spending + 1-2% surplus + transition/equity funds
            
            healthcare_spending_target_gdp=0.07,  # 7% of GDP target by 2045 (USGHA Section 2(b)(3))
            debt_elimination_year=2057,
            life_expectancy_target=132.0,
            
            admin_overhead_pct=0.03,  # 3% admin (vs 16% current US)
            board_size=19,
            board_public_meetings=True,
            
            fraud_penalties_multiplier=3.0,
            malpractice_cap_non_economic=500_000,
        )
        
        # Categories
        policy.categories = {
            "hospital": HealthcareCategory(
                category_name="Hospital Inpatient/Outpatient",
                current_spending_pct=0.31,
                baseline_cost=250.0,
                reduction_target=0.25,
                description="Hospital services and emergency care",
                negotiation_potential=0.35
            ),
            "physician": HealthcareCategory(
                category_name="Physician Services",
                current_spending_pct=0.20,
                baseline_cost=160.0,
                reduction_target=0.15,
                description="Primary and specialist care",
                negotiation_potential=0.20
            ),
            "pharmacy": HealthcareCategory(
                category_name="Pharmaceuticals",
                current_spending_pct=0.10,
                baseline_cost=80.0,
                reduction_target=0.40,
                description="Prescription drugs and biologics",
                negotiation_potential=0.60
            ),
            "mental_health": HealthcareCategory(
                category_name="Mental Health & Substance Use",
                current_spending_pct=0.06,
                baseline_cost=48.0,
                reduction_target=0.20,
                description="Mental health and addiction treatment",
                negotiation_potential=0.25
            ),
            "long_term_care": HealthcareCategory(
                category_name="Long-Term Care",
                current_spending_pct=0.08,
                baseline_cost=64.0,
                reduction_target=0.15,
                description="Nursing homes, home health, palliative care",
                negotiation_potential=0.30
            ),
            "preventive": HealthcareCategory(
                category_name="Preventive & Wellness",
                current_spending_pct=0.05,
                baseline_cost=40.0,
                reduction_target=-0.10,
                description="Preventive care, wellness, vaccination",
                negotiation_potential=0.10
            ),
            "dental_vision_hearing": HealthcareCategory(
                category_name="Dental, Vision, Hearing",
                current_spending_pct=0.04,
                baseline_cost=32.0,
                reduction_target=0.05,
                description="Dental, vision, and hearing services",
                negotiation_potential=0.20
            ),
            "administrative": HealthcareCategory(
                category_name="Administrative",
                current_spending_pct=0.16,
                baseline_cost=128.0,
                reduction_target=0.70,
                description="Billing, insurance overhead",
                negotiation_potential=0.85
            ),
        }
        
        # Drug pricing tiers
        policy.drug_pricing_tiers = {
            "tier_1": DrugPricingTier(
                tier_name="Most-Favored-Nation Minus 20%",
                price_multiplier=0.80,
                description="Standard tier pricing",
                innovation_incentive_multiplier=1.0,
                examples=["Established drugs", "Common treatments"]
            ),
            "tier_2": DrugPricingTier(
                tier_name="Most-Favored-Nation Minus 40%",
                price_multiplier=0.60,
                description="High-value innovations",
                innovation_incentive_multiplier=1.5,
                examples=["Recently FDA-approved", "Breakthrough therapies"]
            ),
            "tier_3": DrugPricingTier(
                tier_name="Price Freedom (14 years)",
                price_multiplier=1.0,
                description="Longevity priority breakthroughs with R&D prizes",
                innovation_incentive_multiplier=2.0,
                examples=["Alzheimer's cure", "Radiation hardening", "Life extension"]
            ),
        }
        
        # Workforce incentives
        policy.workforce_incentives = {
            "primary_care": WorkforceIncentive(
                role="primary_care",
                base_compensation=200_000,
                outcome_multiplier=3.0,
                underserved_loan_forgiveness=300_000,
                description="Primary care physicians, incentive for underserved areas"
            ),
            "specialist": WorkforceIncentive(
                role="specialist",
                base_compensation=350_000,
                outcome_multiplier=5.0,
                underserved_loan_forgiveness=250_000,
                description="Medical specialists with performance-based pay"
            ),
            "hospital": WorkforceIncentive(
                role="hospital",
                base_compensation=0,
                outcome_multiplier=1.7,
                underserved_loan_forgiveness=0,
                description="Hospital global budgets with savings retention"
            ),
            "mental_health": WorkforceIncentive(
                role="mental_health",
                base_compensation=150_000,
                outcome_multiplier=3.5,
                underserved_loan_forgiveness=350_000,
                description="Mental health professionals with expansion incentives"
            ),
        }
        
        # Innovation fund
        policy.innovation_fund = InnovationFund(
            annual_allocation_pct=0.20,
            prize_pct=0.65,
            small_firm_pct=0.35,
            moonshot_annual_budget=50.0,
            open_source_pct=0.15,
            longevity_priority_tax_credit=0.40,
            description="Health Innovation Fund + Longevity Moonshot Fund"
        )
        
        # Circuit breaker
        policy.circuit_breaker = FiscalCircuitBreaker(
            spending_gdp_ceiling=0.13,
            trigger_action="Freeze tax rates and reduce spending until compliance",
            tax_freeze_enabled=True,
            surplus_auto_tax_reduction=True,
            surplus_tax_reduction_per_600b=0.01,
            description="Fiscal safeguards to prevent runaway spending"
        )
        
        # Surplus allocation
        policy.surplus_allocation = SurplusAllocation(
            contingency_reserve_pct=0.10,
            national_debt_reduction_pct=0.70,
            infrastructure_education_pct=0.10,
            space_exploration_pct=0.00,
            taxpayer_dividend_pct=0.10,
            dividend_distribution_date="April 15",
            description="Distribution of annual surpluses per USGHA Section 11(a)"
        )
        
        # Transition timeline (USGHA Section 4(c))
        policy.transition_timeline = TransitionTimeline(
            start_year=2025,
            full_implementation_year=2035,  # Full national implementation Jan 1, 2035
            sunset_year=2047,
            key_milestones={
                2025: "Legislation enacted",
                2027: "State pilots begin, enrollment starts",
                2032: "Pilot acceleration possible if 95% metrics achieved",
                2035: "Full national coverage",
                2040: "Spending <10% GDP, surpluses begin",
                2045: "Spending <7% GDP, longevity targets",
                2047: "Debt elimination, sunset review",
            },
            transition_funding_source="Redirection of Medicare, Medicaid, CHIP, VA spending + payroll taxes"
        )
        
        # Performance targets
        policy.target_metrics = {
            "coverage_percentage": 0.99,
            "zero_oop_compliance": 1.0,
            "medical_bankruptcy_cases": 0,
            "healthcare_spending_gdp": 0.09,
            "avg_patient_savings": 3000,
            "life_expectancy": 132.0,
            "innovation_breakthroughs_annual": 50,
        }
        
        # Attach structured mechanics for context-aware simulation
        from core.policy_mechanics_extractor import (
            PolicyMechanics, FundingMechanism, SurplusAllocation as MechSurplusAllocation,
            CircuitBreaker, InnovationFundRules, TimelineMilestone
        )
        
        policy.mechanics = PolicyMechanics(
            policy_name="United States Galactic Health Act",
            policy_type="healthcare",
            funding_mechanisms=[
                FundingMechanism(
                    source_type="payroll_tax",
                    percentage_rate=15.0,
                    percentage_gdp=None,
                    description="15% payroll tax on wages (Section 6a)"
                ),
                FundingMechanism(
                    source_type="redirected_federal",
                    percentage_gdp=6.2,
                    description="Redirected Medicare/Medicaid/VA/ACA/CHIP (Section 6b)"
                ),
                FundingMechanism(
                    source_type="converted_premiums",
                    percentage_gdp=7.5,
                    description="Employer + employee premiums converted (4.1% + 3.4% GDP)"
                ),
                FundingMechanism(
                    source_type="efficiency_gains",
                    percentage_gdp=2.4,
                    description="Drug pricing + admin savings + other (0.7% + 0.8% + 0.9% GDP)"
                ),
            ],
            surplus_allocation=MechSurplusAllocation(
                contingency_reserve_pct=10.0,
                debt_reduction_pct=70.0,
                infrastructure_pct=10.0,
                dividends_pct=10.0,
                other_allocations={},
                trigger_conditions=["Annual surpluses after healthcare spending"]
            ),
            circuit_breakers=[
                CircuitBreaker(
                    trigger_type="spending_cap",
                    threshold_value=13.0,
                    threshold_unit="percent_gdp",
                    action="Freeze tax rates and reduce spending",
                    description="Healthcare spending must not exceed 13% GDP (Section 6d)"
                ),
                CircuitBreaker(
                    trigger_type="surplus_trigger",
                    threshold_value=600.0,
                    threshold_unit="billion_dollars",
                    action="Automatic 1% tax reduction",
                    description="For every $600B in surpluses, reduce taxes by 1% (Section 6d)"
                ),
            ],
            innovation_fund=InnovationFundRules(
                funding_min_pct=1.0,
                funding_max_pct=20.0,
                funding_base="savings vs baseline",
                prize_min_dollars=1e9,
                prize_max_dollars=50e9,
                annual_cap_pct=5.0,
                annual_cap_base="annual surpluses",
                eligible_categories=["longevity", "radiation_hardening", "alzheimers", "breakthrough_therapies"]
            ),
            timeline_milestones=[
                TimelineMilestone(year=2025, description="Legislation enacted"),
                TimelineMilestone(year=2027, description="State pilots begin, enrollment starts"),
                TimelineMilestone(year=2032, description="Pilot acceleration if 95% metrics achieved"),
                TimelineMilestone(year=2035, description="Full national coverage"),
                TimelineMilestone(year=2040, description="Spending <10% GDP, surpluses begin", metric_type="spending_target", target_value=10.0),
                TimelineMilestone(year=2045, description="Spending <7% GDP, longevity targets", metric_type="spending_target", target_value=7.0),
                TimelineMilestone(year=2047, description="Debt elimination, sunset review"),
            ],
            target_spending_pct_gdp=7.0,
            target_spending_year=2045,
            zero_out_of_pocket=True,
            universal_coverage=True,
            confidence_score=1.0
        )
        
        return policy
    
    @staticmethod
    def create_current_us() -> HealthcarePolicyModel:
        """Current US fragmented multi-payer system (2025 baseline)
        
        Current US healthcare funding breakdown:
        - Medicare/Medicaid/VA: ~3.5% of GDP
        - Private insurance (payroll-based): ~4.0% of GDP  
        - Out-of-pocket patient spending: ~1.0% of GDP
        - Other (pharmaceutical, etc.): ~0.5% of GDP
        Total: ~9% of GDP in government + employer healthcare spending
        (Total including OOP is ~10.5% of GDP)
        
        Note: Out-of-pocket and other private are NOT government revenues
        available for healthcare spending. They're what patients pay directly.
        """
        policy = HealthcarePolicyModel(
            policy_type=PolicyType.CURRENT_US,
            policy_name="Current US Healthcare System",
            policy_version="2025",
            created_date="2025-11-25",
            description="Baseline: multi-payer fragmented system. Government + employer spending ~9% GDP, total (incl. patient OOP) ~10.5% GDP.",
            
            universal_coverage=False,
            zero_out_of_pocket=False,
            opt_out_allowed=False,
            emergency_coverage=True,
            coverage_percentage=0.92,
            
            # Government + employer dedicated healthcare revenue only
            total_payroll_tax=0.04,  # Employer + employee payroll-based insurance
            employer_contribution_pct=0.10,
            employee_contribution_pct=0.08,
            general_revenue_pct=0.035,  # Medicare/Medicaid/VA from general revenue
            other_funding_sources={
                # These are net reductions/offsets, not additional revenues
                # Out-of-pocket is patient burden, not government revenue
            },
            
            healthcare_spending_target_gdp=0.18,  # Total spending including OOP
            admin_overhead_pct=0.16,  # 16% admin waste (insurance overhead)
        )
        
        policy.categories = {
            "hospital": HealthcareCategory(
                category_name="Hospital Inpatient/Outpatient",
                current_spending_pct=0.31,
                baseline_cost=250.0,
                reduction_target=0.0,
                description="Hospital services"
            ),
            "physician": HealthcareCategory(
                category_name="Physician Services",
                current_spending_pct=0.20,
                baseline_cost=160.0,
                reduction_target=0.0,
                description="Physician care"
            ),
            "pharmacy": HealthcareCategory(
                category_name="Pharmaceuticals",
                current_spending_pct=0.10,
                baseline_cost=80.0,
                reduction_target=0.0,
                description="Drugs at premium pricing"
            ),
            "administrative": HealthcareCategory(
                category_name="Administrative",
                current_spending_pct=0.16,
                baseline_cost=128.0,
                reduction_target=0.0,
                description="Insurance overhead, billing"
            ),
            "other": HealthcareCategory(
                category_name="Other",
                current_spending_pct=0.23,
                baseline_cost=184.0,
                reduction_target=0.0,
                description="Other services"
            ),
        }
        
        policy.target_metrics = {
            "coverage_percentage": 0.92,
            "healthcare_spending_gdp": 0.18,
            "medical_bankruptcy_cases": 800_000,
            "avg_patient_oop": 1200,
        }
        
        # No surplus allocation for current US (fiscal deficits)
        policy.surplus_allocation = None
        
        # Transition timeline
        policy.transition_timeline = TransitionTimeline(
            start_year=2025,
            full_implementation_year=2025,  # Already implemented
            sunset_year=None,
            key_milestones={},
            transition_funding_source="N/A - Status Quo"
        )
        
        # Attach structured mechanics for context-aware simulation (baseline model)
        from core.policy_mechanics_extractor import (
            PolicyMechanics, FundingMechanism, TimelineMilestone
        )
        
        policy.mechanics = PolicyMechanics(
            policy_name="Current US Healthcare System",
            policy_type="healthcare",
            funding_mechanisms=[
                FundingMechanism(
                    source_type="redirected_federal",
                    percentage_gdp=3.5,
                    description="Medicare/Medicaid/VA federal spending (~3.5% GDP)"
                ),
                FundingMechanism(
                    source_type="converted_premiums",
                    percentage_gdp=4.0,
                    description="Private insurance payroll-based premiums (~4% GDP)"
                ),
            ],
            surplus_allocation=None,  # Current US runs deficits
            circuit_breakers=[],
            innovation_fund=None,
            timeline_milestones=[
                TimelineMilestone(year=2025, description="Current baseline year"),
            ],
            target_spending_pct_gdp=18.5,  # Current US spends ~18.5% GDP
            target_spending_year=2025,
            zero_out_of_pocket=False,
            universal_coverage=False,
            confidence_score=1.0
        )
        
        return policy
    
    @staticmethod
    def create_medicare_for_all() -> HealthcarePolicyModel:
        """Medicare-for-All style single-payer system"""
        return HealthcarePolicyModel(
            policy_type=PolicyType.MEDICARE_FOR_ALL,
            policy_name="Medicare for All (Single-Payer)",
            policy_version="2.0",
            created_date="2025-11-25",
            description="Universal single-payer system similar to Bernie Sanders proposal",
            
            universal_coverage=True,
            zero_out_of_pocket=True,
            opt_out_allowed=False,
            emergency_coverage=True,
            coverage_percentage=1.0,
            
            total_payroll_tax=0.12,
            employer_contribution_pct=0.055,
            employee_contribution_pct=0.045,
            general_revenue_pct=0.05,
            other_funding_sources={
                "progressive_taxes": 0.08,
                "elimination_of_premiums": 0.10,
            },
            
            healthcare_spending_target_gdp=0.12,
            admin_overhead_pct=0.02,
            board_size=7,
            board_public_meetings=True,
            
            target_metrics={
                "coverage_percentage": 1.0,
                "healthcare_spending_gdp": 0.12,
                "medical_bankruptcy_cases": 0,
                "avg_patient_oop": 0,
            }
        )
    
    @staticmethod
    def create_uk_nhs() -> HealthcarePolicyModel:
        """UK National Health Service model"""
        return HealthcarePolicyModel(
            policy_type=PolicyType.UK_NHS,
            policy_name="UK National Health Service",
            policy_version="2025",
            created_date="2025-11-25",
            description="Public integrated healthcare like UK NHS",
            
            universal_coverage=True,
            zero_out_of_pocket=True,
            opt_out_allowed=True,
            emergency_coverage=True,
            coverage_percentage=0.98,
            
            total_payroll_tax=0.10,
            employer_contribution_pct=0.0,
            employee_contribution_pct=0.0,
            general_revenue_pct=0.10,
            
            healthcare_spending_target_gdp=0.10,
            admin_overhead_pct=0.02,
            board_size=1,
            
            target_metrics={
                "coverage_percentage": 0.98,
                "healthcare_spending_gdp": 0.10,
                "medical_bankruptcy_cases": 0,
            }
        )
    
    @staticmethod
    def create_canada_single_payer() -> HealthcarePolicyModel:
        """Canadian provincial single-payer system"""
        return HealthcarePolicyModel(
            policy_type=PolicyType.CANADA_SP,
            policy_name="Canadian Provincial Single-Payer",
            policy_version="2025",
            created_date="2025-11-25",
            description="Provincial single-payer system like Canada",
            
            universal_coverage=True,
            zero_out_of_pocket=True,
            opt_out_allowed=False,
            emergency_coverage=True,
            coverage_percentage=0.99,
            
            total_payroll_tax=0.095,
            employer_contribution_pct=0.0,
            employee_contribution_pct=0.0,
            general_revenue_pct=0.095,
            
            healthcare_spending_target_gdp=0.11,
            admin_overhead_pct=0.01,
            board_size=1,
            
            target_metrics={
                "coverage_percentage": 0.99,
                "healthcare_spending_gdp": 0.11,
                "medical_bankruptcy_cases": 0,
            }
        )


def get_policy_by_type(policy_type: PolicyType) -> HealthcarePolicyModel:
    """Get a policy model by type"""
    factory = HealthcarePolicyFactory()
    policies = {
        PolicyType.USGHA: factory.create_usgha,
        PolicyType.CURRENT_US: factory.create_current_us,
        PolicyType.MEDICARE_FOR_ALL: factory.create_medicare_for_all,
        PolicyType.UK_NHS: factory.create_uk_nhs,
        PolicyType.CANADA_SP: factory.create_canada_single_payer,
    }
    
    if policy_type in policies:
        return policies[policy_type]()
    
    raise ValueError(f"Unknown policy type: {policy_type}")


def list_available_policies() -> List[HealthcarePolicyModel]:
    """Get all available policy models"""
    return [
        get_policy_by_type(PolicyType.USGHA),
        get_policy_by_type(PolicyType.CURRENT_US),
        get_policy_by_type(PolicyType.MEDICARE_FOR_ALL),
        get_policy_by_type(PolicyType.UK_NHS),
        get_policy_by_type(PolicyType.CANADA_SP),
    ]
