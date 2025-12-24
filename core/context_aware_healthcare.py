"""
Context-Aware Healthcare Simulation Engine
Calculates outcomes based on extracted policy mechanics instead of hard-coded values.

Provides mechanism-based calculators for:
- Revenue (payroll tax, redirected federal, converted premiums, efficiency gains)
- Spending (administrative reduction, drug pricing savings, preventive care)
- Surplus allocation (reserves, debt reduction, infrastructure, dividends)
- Circuit breakers (spending caps, surplus triggers)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class RevenueBreakdown:
    """Detailed revenue breakdown by source."""
    payroll_tax: float = 0.0
    redirected_federal: float = 0.0
    converted_premiums: float = 0.0
    efficiency_gains: float = 0.0
    other_sources: float = 0.0
    total: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'payroll_tax': self.payroll_tax,
            'redirected_federal': self.redirected_federal,
            'converted_premiums': self.converted_premiums,
            'efficiency_gains': self.efficiency_gains,
            'other_sources': self.other_sources,
            'total': self.total
        }


@dataclass
class SpendingBreakdown:
    """Detailed spending breakdown by reduction mechanism."""
    baseline_spending: float
    administrative_savings: float = 0.0
    drug_pricing_savings: float = 0.0
    preventive_care_savings: float = 0.0
    other_savings: float = 0.0
    net_spending: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'baseline_spending': self.baseline_spending,
            'administrative_savings': self.administrative_savings,
            'drug_pricing_savings': self.drug_pricing_savings,
            'preventive_care_savings': self.preventive_care_savings,
            'other_savings': self.other_savings,
            'net_spending': self.net_spending
        }


@dataclass
class SurplusBreakdown:
    """Detailed surplus allocation breakdown."""
    total_surplus: float
    contingency_reserve: float = 0.0
    debt_reduction: float = 0.0
    infrastructure: float = 0.0
    dividends: float = 0.0
    other_allocations: Dict[str, float] = None
    
    def __post_init__(self):
        if self.other_allocations is None:
            self.other_allocations = {}
    
    def to_dict(self) -> Dict[str, float]:
        result = {
            'total_surplus': self.total_surplus,
            'contingency_reserve': self.contingency_reserve,
            'debt_reduction': self.debt_reduction,
            'infrastructure': self.infrastructure,
            'dividends': self.dividends
        }
        result.update(self.other_allocations)
        return result


class MechanismBasedRevenueCalculator:
    """Calculate revenue based on policy funding mechanisms."""
    
    @staticmethod
    def calculate_payroll_revenue(
        rate: float,
        gdp: float,
        employment_rate: float = 0.63,
        wage_share_gdp: float = 0.53
    ) -> float:
        """
        Calculate payroll tax revenue.
        
        Args:
            rate: Payroll tax rate (e.g., 0.15 for 15%)
            gdp: Current GDP in billions
            employment_rate: Fraction of population employed
            wage_share_gdp: Wages as fraction of GDP
        
        Returns:
            Revenue in billions
        """
        wage_base = gdp * wage_share_gdp
        return rate * wage_base
    
    @staticmethod
    def calculate_redirected_federal(
        pct_gdp: float,
        gdp: float
    ) -> float:
        """
        Calculate redirected federal health spending.
        
        Args:
            pct_gdp: Percentage of GDP (e.g., 0.062 for 6.2%)
            gdp: Current GDP in billions
        
        Returns:
            Redirected amount in billions
        """
        return pct_gdp * gdp
    
    @staticmethod
    def calculate_converted_premiums(
        pct_gdp: float,
        gdp: float,
        conversion_rate: float = 0.95,
        year: int = 0,
        ramp_years: int = 8
    ) -> float:
        """
        Calculate converted employer/employee premiums.
        
        Args:
            pct_gdp: Target percentage of GDP (e.g., 0.075 for 7.5%)
            gdp: Current GDP in billions
            conversion_rate: Fraction successfully converted (0-1)
            year: Years since policy start
            ramp_years: Years to reach full conversion
        
        Returns:
            Converted premium revenue in billions
        """
        # Ramp up conversion over time
        progress = min(year / ramp_years, 1.0) if ramp_years > 0 else 1.0
        return pct_gdp * gdp * conversion_rate * progress
    
    @staticmethod
    def calculate_efficiency_gains(
        pct_gdp: float,
        gdp: float,
        year: int = 0,
        ramp_years: int = 8,
        curve: str = "sigmoid"
    ) -> float:
        """
        Calculate efficiency gain funding.
        
        Args:
            pct_gdp: Target percentage of GDP (e.g., 0.024 for 2.4%)
            gdp: Current GDP in billions
            year: Years since policy start
            ramp_years: Years to reach full efficiency
            curve: Ramp-up curve type ("linear" or "sigmoid")
        
        Returns:
            Efficiency gain funding in billions
        """
        if ramp_years == 0:
            progress = 1.0
        elif curve == "sigmoid":
            # S-curve: slow start, rapid middle, slow end
            x = (year / ramp_years) * 12 - 6  # Map to [-6, 6]
            progress = 1 / (1 + math.exp(-x))
        else:  # linear
            progress = min(year / ramp_years, 1.0)
        
        return pct_gdp * gdp * progress
    
    @staticmethod
    def calculate_from_mechanics(
        mechanics,
        gdp: float,
        year: int = 0,
        start_year: int = 2027
    ) -> RevenueBreakdown:
        """
        Calculate total revenue from PolicyMechanics object.
        
        Args:
            mechanics: PolicyMechanics object with funding_mechanisms
            gdp: Current GDP in billions
            year: Current simulation year
            start_year: Year policy started
        
        Returns:
            RevenueBreakdown with detailed sources
        """
        breakdown = RevenueBreakdown()
        years_since_start = year - start_year
        
        if not mechanics or not mechanics.funding_mechanisms:
            return breakdown
        
        for mechanism in mechanics.funding_mechanisms:
            if mechanism.source_type == "payroll_tax":
                if mechanism.percentage_rate:
                    breakdown.payroll_tax = MechanismBasedRevenueCalculator.calculate_payroll_revenue(
                        rate=mechanism.percentage_rate / 100,
                        gdp=gdp
                    )
            
            elif mechanism.source_type == "redirected_federal":
                if mechanism.percentage_gdp:
                    breakdown.redirected_federal = MechanismBasedRevenueCalculator.calculate_redirected_federal(
                        pct_gdp=mechanism.percentage_gdp / 100,
                        gdp=gdp
                    )
            
            elif mechanism.source_type == "converted_premiums":
                if mechanism.percentage_gdp:
                    breakdown.converted_premiums = MechanismBasedRevenueCalculator.calculate_converted_premiums(
                        pct_gdp=mechanism.percentage_gdp / 100,
                        gdp=gdp,
                        year=years_since_start
                    )
            
            elif mechanism.source_type == "efficiency_gains":
                if mechanism.percentage_gdp:
                    breakdown.efficiency_gains = MechanismBasedRevenueCalculator.calculate_efficiency_gains(
                        pct_gdp=mechanism.percentage_gdp / 100,
                        gdp=gdp,
                        year=years_since_start
                    )
            
            else:
                # Other sources
                if mechanism.percentage_gdp:
                    breakdown.other_sources += mechanism.percentage_gdp / 100 * gdp
        
        breakdown.total = (
            breakdown.payroll_tax +
            breakdown.redirected_federal +
            breakdown.converted_premiums +
            breakdown.efficiency_gains +
            breakdown.other_sources
        )
        
        return breakdown


class MechanismBasedSpendingCalculator:
    """Calculate spending based on policy efficiency mechanisms."""
    
    @staticmethod
    def calculate_baseline_spending(
        baseline_pct_gdp: float,
        gdp: float
    ) -> float:
        """Calculate baseline spending (what would be spent without policy)."""
        return baseline_pct_gdp * gdp
    
    @staticmethod
    def calculate_administrative_savings(
        baseline_spending: float,
        admin_reduction_pct: float = 0.30,
        year: int = 0,
        ramp_years: int = 5
    ) -> float:
        """
        Calculate savings from administrative efficiency.
        
        Args:
            baseline_spending: Baseline healthcare spending
            admin_reduction_pct: Percentage reduction in admin costs (e.g., 0.30 for 30%)
            year: Years since policy start
            ramp_years: Years to achieve full admin efficiency
        
        Returns:
            Savings in billions
        """
        # Admin costs are ~25-30% of US healthcare spending
        admin_share = 0.275
        progress = min(year / ramp_years, 1.0) if ramp_years > 0 else 1.0
        
        return baseline_spending * admin_share * admin_reduction_pct * progress
    
    @staticmethod
    def calculate_drug_pricing_savings(
        baseline_spending: float,
        pricing_reduction_pct: float = 0.50,
        year: int = 0,
        ramp_years: int = 3
    ) -> float:
        """
        Calculate savings from drug price negotiation.
        
        Args:
            baseline_spending: Baseline healthcare spending
            pricing_reduction_pct: Price reduction percentage (e.g., 0.50 for 50%)
            year: Years since policy start
            ramp_years: Years to implement pricing reforms
        
        Returns:
            Savings in billions
        """
        # Drugs are ~10-12% of US healthcare spending
        drug_share = 0.11
        progress = min(year / ramp_years, 1.0) if ramp_years > 0 else 1.0
        
        return baseline_spending * drug_share * pricing_reduction_pct * progress
    
    @staticmethod
    def calculate_preventive_care_savings(
        baseline_spending: float,
        prevention_effectiveness: float = 0.15,
        year: int = 0,
        ramp_years: int = 10
    ) -> float:
        """
        Calculate savings from preventive care emphasis.
        
        Args:
            baseline_spending: Baseline healthcare spending
            prevention_effectiveness: Reduction in treatment costs (e.g., 0.15 for 15%)
            year: Years since policy start
            ramp_years: Years for prevention to show impact
        
        Returns:
            Savings in billions
        """
        # Preventive care saves on treatment costs (slow accumulation)
        progress = min(year / ramp_years, 1.0) if ramp_years > 0 else 1.0
        
        return baseline_spending * prevention_effectiveness * progress
    
    @staticmethod
    def calculate_from_target(
        target_pct_gdp: float,
        target_year: int,
        baseline_pct_gdp: float,
        gdp: float,
        year: int,
        start_year: int
    ) -> SpendingBreakdown:
        """
        Calculate spending trajectory toward target.
        
        Args:
            target_pct_gdp: Target spending percentage (e.g., 0.07 for 7%)
            target_year: Year to achieve target
            baseline_pct_gdp: Baseline spending percentage (e.g., 0.185 for 18.5%)
            gdp: Current GDP
            year: Current simulation year
            start_year: Year policy started
        
        Returns:
            SpendingBreakdown with savings details
        """
        breakdown = SpendingBreakdown(
            baseline_spending=baseline_pct_gdp * gdp
        )
        
        years_since_start = year - start_year
        years_to_target = target_year - start_year
        
        # Calculate progress toward target
        if years_to_target > 0:
            progress = min(years_since_start / years_to_target, 1.0)
        else:
            progress = 1.0
        
        # Interpolate spending
        current_pct = baseline_pct_gdp + (target_pct_gdp - baseline_pct_gdp) * progress
        target_spending = current_pct * gdp
        
        total_savings = breakdown.baseline_spending - target_spending
        
        # Attribute savings to mechanisms (rough approximation)
        breakdown.administrative_savings = total_savings * 0.40  # 40% from admin
        breakdown.drug_pricing_savings = total_savings * 0.25    # 25% from drug pricing
        breakdown.preventive_care_savings = total_savings * 0.20  # 20% from prevention
        breakdown.other_savings = total_savings * 0.15           # 15% other efficiencies
        
        breakdown.net_spending = target_spending
        
        return breakdown


class SurplusAllocationEngine:
    """Apply surplus allocation rules from policy mechanics."""
    
    @staticmethod
    def allocate_surplus(
        surplus: float,
        allocation_rules
    ) -> SurplusBreakdown:
        """
        Allocate surplus according to policy rules.
        
        Args:
            surplus: Total surplus amount
            allocation_rules: SurplusAllocation from PolicyMechanics
        
        Returns:
            SurplusBreakdown with detailed allocation
        """
        breakdown = SurplusBreakdown(total_surplus=surplus)
        
        if not allocation_rules or surplus <= 0:
            return breakdown
        
        # Apply allocation percentages
        breakdown.contingency_reserve = surplus * (allocation_rules.contingency_reserve_pct / 100)
        breakdown.debt_reduction = surplus * (allocation_rules.debt_reduction_pct / 100)
        breakdown.infrastructure = surplus * (allocation_rules.infrastructure_pct / 100)
        breakdown.dividends = surplus * (allocation_rules.dividends_pct / 100)
        
        # Handle other allocations
        if allocation_rules.other_allocations:
            for name, pct in allocation_rules.other_allocations.items():
                breakdown.other_allocations[name] = surplus * (pct / 100)
        
        return breakdown


class CircuitBreakerEnforcer:
    """Enforce fiscal circuit breakers from policy mechanics."""
    
    @staticmethod
    def check_spending_cap(
        spending_pct_gdp: float,
        circuit_breakers: List,
        year: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if spending exceeds circuit breaker cap.
        
        Returns:
            (triggered, action_description)
        """
        if not circuit_breakers:
            return False, None
        
        for breaker in circuit_breakers:
            if breaker.trigger_type == "spending_cap":
                if spending_pct_gdp > breaker.threshold_value:
                    return True, f"Spending {spending_pct_gdp:.1f}% GDP exceeds {breaker.threshold_value}% cap - {breaker.action}"
        
        return False, None
    
    @staticmethod
    def check_surplus_trigger(
        surplus_pct_gdp: float,
        circuit_breakers: List,
        year: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if surplus triggers automatic policy adjustment.
        
        Returns:
            (triggered, action_description)
        """
        if not circuit_breakers:
            return False, None
        
        for breaker in circuit_breakers:
            if breaker.trigger_type == "surplus_trigger":
                if surplus_pct_gdp > breaker.threshold_value:
                    return True, f"Surplus {surplus_pct_gdp:.1f}% GDP exceeds {breaker.threshold_value}% - {breaker.action}"
        
        return False, None


def calculate_mechanism_based_outcomes(
    mechanics,
    gdp: float,
    year: int,
    start_year: int,
    baseline_spending_pct_gdp: float = 0.185
) -> Dict:
    """
    Calculate all outcomes from policy mechanics.
    
    Args:
        mechanics: PolicyMechanics object
        gdp: Current GDP
        year: Current year
        start_year: Year policy started
        baseline_spending_pct_gdp: Baseline healthcare spending as % GDP
    
    Returns:
        Dictionary with revenue, spending, surplus, and circuit breaker status
    """
    results = {}
    
    # Calculate revenue
    revenue_calc = MechanismBasedRevenueCalculator()
    revenue_breakdown = revenue_calc.calculate_from_mechanics(
        mechanics, gdp, year, start_year
    )
    results['revenue'] = revenue_breakdown
    
    # Calculate spending
    if mechanics and mechanics.target_spending_pct_gdp and mechanics.target_spending_year:
        spending_breakdown = MechanismBasedSpendingCalculator.calculate_from_target(
            target_pct_gdp=mechanics.target_spending_pct_gdp / 100,
            target_year=mechanics.target_spending_year,
            baseline_pct_gdp=baseline_spending_pct_gdp,
            gdp=gdp,
            year=year,
            start_year=start_year
        )
    else:
        # Fallback: use baseline
        spending_breakdown = SpendingBreakdown(
            baseline_spending=baseline_spending_pct_gdp * gdp,
            net_spending=baseline_spending_pct_gdp * gdp
        )
    
    results['spending'] = spending_breakdown
    
    # Calculate surplus
    surplus = revenue_breakdown.total - spending_breakdown.net_spending
    results['surplus'] = surplus
    
    # Allocate surplus
    if mechanics and mechanics.surplus_allocation:
        surplus_breakdown = SurplusAllocationEngine.allocate_surplus(
            surplus, mechanics.surplus_allocation
        )
        results['surplus_allocation'] = surplus_breakdown
    else:
        results['surplus_allocation'] = None
    
    # Check circuit breakers
    spending_pct = (spending_breakdown.net_spending / gdp) * 100
    surplus_pct = (surplus / gdp) * 100
    
    circuit_breakers = []
    if mechanics and mechanics.circuit_breakers:
        cap_triggered, cap_msg = CircuitBreakerEnforcer.check_spending_cap(
            spending_pct, mechanics.circuit_breakers, year
        )
        if cap_triggered:
            circuit_breakers.append(('spending_cap', cap_msg))
        
        surplus_triggered, surplus_msg = CircuitBreakerEnforcer.check_surplus_trigger(
            surplus_pct, mechanics.circuit_breakers, year
        )
        if surplus_triggered:
            circuit_breakers.append(('surplus_trigger', surplus_msg))
    
    results['circuit_breakers'] = circuit_breakers
    
    return results
