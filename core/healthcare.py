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
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime


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
        """US Galactic Health Act V0.6"""
        policy = HealthcarePolicyModel(
            policy_type=PolicyType.USGHA,
            policy_name="United States Galactic Health Act",
            policy_version="0.6",
            created_date="2025-11-25",
            description="Universal zero-out-of-pocket healthcare with innovation focus and multiplanetary imperatives",
            
            universal_coverage=True,
            zero_out_of_pocket=True,
            opt_out_allowed=True,
            emergency_coverage=True,
            coverage_percentage=0.99,
            
            total_payroll_tax=0.15,
            employer_contribution_pct=0.0825,
            employee_contribution_pct=0.0675,
            general_revenue_pct=0.15,
            other_funding_sources={
                "drug_pricing_negotiation": 0.08,
                "financial_transaction_tax": 0.04,
                "excise_taxes": 0.03,
                "import_tariffs": 0.03,
            },
            
            healthcare_spending_target_gdp=0.09,
            debt_elimination_year=2057,
            life_expectancy_target=132.0,
            
            admin_overhead_pct=0.03,
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
            national_debt_reduction_pct=0.50,
            infrastructure_education_pct=0.25,
            space_exploration_pct=0.00,
            taxpayer_dividend_pct=0.15,
            dividend_distribution_date="April 15",
            description="Distribution of annual surpluses (when revenues > 105% of projections)"
        )
        
        # Transition timeline
        policy.transition_timeline = TransitionTimeline(
            start_year=2025,
            full_implementation_year=2027,
            sunset_year=2047,
            key_milestones={
                2025: "Legislation enacted",
                2026: "Enrollment begins, infrastructure built",
                2027: "Coverage begins Jan 1",
                2035: "Healthcare spending target: <9% GDP",
                2045: "Longevity Moonshot Fund reaches $400B+",
                2047: "Debt elimination projected, sunset review",
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
        
        return policy
    
    @staticmethod
    def create_current_us() -> HealthcarePolicyModel:
        """Current US fragmented multi-payer system (2025 baseline)"""
        policy = HealthcarePolicyModel(
            policy_type=PolicyType.CURRENT_US,
            policy_name="Current US Healthcare System",
            policy_version="2025",
            created_date="2025-11-25",
            description="Baseline: multi-payer, fragmented system with 18% GDP spending",
            
            universal_coverage=False,
            zero_out_of_pocket=False,
            opt_out_allowed=False,
            emergency_coverage=True,
            coverage_percentage=0.92,
            
            total_payroll_tax=0.075,
            employer_contribution_pct=0.10,
            employee_contribution_pct=0.08,
            general_revenue_pct=0.07,
            other_funding_sources={
                "out_of_pocket": 0.11,
                "other_private": 0.17,
            },
            
            healthcare_spending_target_gdp=0.18,
            admin_overhead_pct=0.16,
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


def list_available_policies() -> Dict[str, PolicyType]:
    """Get all available policy types and names"""
    return {
        "USGHA": PolicyType.USGHA,
        "Current US System": PolicyType.CURRENT_US,
        "Medicare for All": PolicyType.MEDICARE_FOR_ALL,
        "UK NHS": PolicyType.UK_NHS,
        "Canada Single-Payer": PolicyType.CANADA_SP,
    }
