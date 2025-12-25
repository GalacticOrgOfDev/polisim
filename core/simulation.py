"""Simulation engine for economic policy scenarios.

This module handles multi-year simulations of economic policies,
tracking GDP, debt, surplus, and other macroeconomic indicators.
"""

from typing import Optional
import logging

import pandas as pd
from tkinter import messagebox

logger = logging.getLogger(__name__)

from core.economics import calculate_revenues_and_outs
from core.healthcare import PolicyType
from core.context_aware_healthcare import (
    calculate_mechanism_based_outcomes,
    RevenueBreakdown,
    SpendingBreakdown,
    SurplusBreakdown
)

# L2 Fix: Extract simulation magic numbers to named constants
# Category reduction bounds
REDUCTION_FACTOR_MIN = 0.5  # Minimum spending level (50% reduction max)
REDUCTION_FACTOR_MAX = 1.5  # Maximum spending level (50% increase max for growth categories)

# Baseline healthcare metrics
BASELINE_HEALTH_PCT_GDP = 0.185  # 18.5% GDP (2025 US baseline)


def _simulate_with_mechanics(policy, base_gdp: float, initial_debt: float, years: int,
                            population: float, gdp_growth: float, start_year: int = None,
                            cbo_data: dict = None) -> pd.DataFrame:
    """
    Context-aware simulation using extracted policy mechanics.
    
    This function understands WHY revenues and spending change, not just THAT they change.
    """
    rows = []
    current_debt = float(initial_debt)
    
    # Baseline healthcare spending
    baseline_health_pct_gdp = BASELINE_HEALTH_PCT_GDP
    
    # Determine start year
    timeline = policy.transition_timeline
    if start_year is None:
        start_year = timeline.start_year if timeline and timeline.start_year else 2025
    
    # Accumulate reserves
    contingency_reserve_balance = 0.0
    
    for i in range(years):
        year = start_year + i
        
        # Calculate current GDP with compounded growth
        current_gdp = base_gdp * ((1.0 + gdp_growth) ** i)
        
        # CONTEXT-AWARE: Calculate outcomes from mechanics
        outcomes = calculate_mechanism_based_outcomes(
            mechanics=policy.mechanics,
            gdp=current_gdp,
            year=year,
            start_year=start_year,
            baseline_spending_pct_gdp=baseline_health_pct_gdp
        )
        
        revenue_breakdown: RevenueBreakdown = outcomes['revenue']
        spending_breakdown: SpendingBreakdown = outcomes['spending']
        surplus = outcomes['surplus']
        surplus_allocation: Optional[SurplusBreakdown] = outcomes['surplus_allocation']
        circuit_breakers = outcomes['circuit_breakers']
        
        # Calculate baseline health spending for comparison
        baseline_health_spending_this_year = baseline_health_pct_gdp * current_gdp
        savings_vs_baseline = baseline_health_spending_this_year - spending_breakdown.net_spending
        
        # Apply surplus allocation
        debt_reduction_amount = 0.0
        infrastructure_allocation = 0.0
        dividend_pool = 0.0
        contingency_addition = 0.0
        
        if surplus > 0 and surplus_allocation:
            debt_reduction_amount = surplus_allocation.debt_reduction
            infrastructure_allocation = surplus_allocation.infrastructure
            dividend_pool = surplus_allocation.dividends
            contingency_addition = surplus_allocation.contingency_reserve
            
            # Add to contingency reserve
            contingency_reserve_balance += contingency_addition
            
            # Reduce debt
            current_debt = max(0, current_debt - debt_reduction_amount)
        elif surplus < 0:
            # Deficit: may need to draw from reserves or increase debt
            if contingency_reserve_balance > abs(surplus):
                contingency_reserve_balance -= abs(surplus)
            else:
                current_debt += abs(surplus)
        
        # Calculate interest on debt (assume 3.5% average rate)
        interest_rate = 0.035
        interest_spending = current_debt * interest_rate
        
        # Innovation fund allocation (from policy mechanics if specified)
        innovation_fund_amount = 0.0
        if policy.mechanics and policy.mechanics.innovation_fund and savings_vs_baseline > 0:
            # Fund based on savings percentage
            fund_pct = policy.mechanics.innovation_fund.funding_min_pct / 100
            innovation_fund_amount = savings_vs_baseline * fund_pct
            
            # Apply annual cap
            if policy.mechanics.innovation_fund.annual_cap_pct > 0 and surplus > 0:
                cap = surplus * (policy.mechanics.innovation_fund.annual_cap_pct / 100)
                innovation_fund_amount = min(innovation_fund_amount, cap)
        
        # Per capita metrics (with validation to prevent division by zero)
        if population > 0:
            per_capita_spending = spending_breakdown.net_spending / population
            dividend_per_capita = dividend_pool / population if dividend_pool > 0 else 0.0
        else:
            per_capita_spending = 0.0
            dividend_per_capita = 0.0
            logger.error(f"Year {year}: Population is zero or negative, cannot calculate per-capita metrics")
        
        # Circuit breaker status
        circuit_breaker_triggered = len(circuit_breakers) > 0
        circuit_breaker_msg = "; ".join([msg for _, msg in circuit_breakers]) if circuit_breaker_triggered else ""
        
        # Build row
        row = {
            'Year': year,
            'GDP': current_gdp,
            'Remaining Debt ($)': current_debt,
            'Debt % GDP': (current_debt / current_gdp) * 100,
            
            # Revenue breakdown
            'Revenue ($)': revenue_breakdown.total,
            'Payroll Tax Revenue': revenue_breakdown.payroll_tax,
            'Redirected Federal Revenue': revenue_breakdown.redirected_federal,
            'Converted Premiums Revenue': revenue_breakdown.converted_premiums,
            'Efficiency Gains Revenue': revenue_breakdown.efficiency_gains,
            'Other Revenue': revenue_breakdown.other_sources,
            
            # Spending breakdown
            'Health Spending ($)': spending_breakdown.net_spending,
            'Health % GDP': (spending_breakdown.net_spending / current_gdp) * 100,
            'Baseline Health Spending': baseline_health_spending_this_year,
            'Savings vs Baseline': savings_vs_baseline,
            'Administrative Savings': spending_breakdown.administrative_savings,
            'Drug Pricing Savings': spending_breakdown.drug_pricing_savings,
            'Preventive Care Savings': spending_breakdown.preventive_care_savings,
            
            # Fiscal outcomes
            'Surplus ($)': surplus,
            'Surplus % GDP': (surplus / current_gdp) * 100,
            'Interest Spending': interest_spending,
            
            # Surplus allocation
            'Contingency Reserve': contingency_reserve_balance,
            'Debt Reduction': debt_reduction_amount,
            'Infrastructure Allocation': infrastructure_allocation,
            'Dividend Pool': dividend_pool,
            'Dividend Per Capita': dividend_per_capita,
            
            # Innovation
            'Innovation Fund': innovation_fund_amount,
            
            # Per capita
            'Per Capita Health ($)': per_capita_spending,
            'Population': population,
            
            # Circuit breakers
            'Circuit Breaker Triggered': circuit_breaker_triggered,
            'Circuit Breaker Message': circuit_breaker_msg
        }
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def simulate_years(internal_general, internal_revenues, internal_outs):
    """
    Simulate economic policy over multiple years.

    EDGE CASE HANDLING:
    - Negative GDP growth (recession)
    - Hyperinflation (>50% inflation)
    - Debt explosion (debt > 10x GDP)
    - Interest payments exceeding total revenue
    
    Args:
        internal_general: Dict with 'gdp', 'gdp_growth_rate', 'inflation_rate', etc.
        internal_revenues: List of revenue dicts
        internal_outs: List of expenditure dicts
    
    Returns:
        pandas.DataFrame with simulation results, or None if error
    """
    try:
        # Ensure simulation_years is a positive integer
        sim_years = int(float(internal_general['simulation_years']))
        if sim_years <= 0:
            raise ValueError("Simulation years must be positive")
        internal_general['simulation_years'] = sim_years
    except (ValueError, TypeError) as e:
        messagebox.showerror("Error", f"Invalid simulation years value: {str(e)}")
        return None

    results = []
    current_gdp = internal_general['gdp']
    current_debt = internal_general['national_debt']
    current_interest = current_debt * (internal_general['interest_rate'] / 100)
    base_gdp_growth_decimal = internal_general['gdp_growth_rate'] / 100  # Store base rate
    inflation_decimal = internal_general['inflation_rate'] / 100
    surplus_redirect_decimal = internal_general['surplus_redirect_post_debt'] / 100

    # P1: Get debt-drag and stop-on-explosion settings
    debt_drag_factor = internal_general.get('debt_drag_factor', 0.0)
    stop_on_explosion = internal_general.get('stop_on_debt_explosion', 0)

    # Edge case warnings
    warnings = []
    if base_gdp_growth_decimal < 0:
        warnings.append(f"WARNING: Negative GDP growth ({internal_general['gdp_growth_rate']}%) - recession scenario")
    if inflation_decimal > 0.5:
        warnings.append(f"WARNING: Hyperinflation detected ({internal_general['inflation_rate']}%) - model may be unreliable")
    if current_debt / current_gdp > 10:
        warnings.append(f"WARNING: Debt-to-GDP ratio > 1000% - debt explosion scenario")

    if warnings:
        warning_msg = "\n".join(warnings) + "\n\nContinue simulation?"
        if not messagebox.askyesno("Edge Case Detected", warning_msg):
            return None

    for year in range(1, int(internal_general['simulation_years']) + 1):
        # P1: Apply debt-drag factor (endogenous growth slowdown from high debt)
        # Based on CBO/IMF models: high debt slows growth
        debt_to_gdp_ratio = current_debt / current_gdp
        debt_drag = debt_drag_factor * (debt_to_gdp_ratio * 10)  # Per 10% debt/GDP
        gdp_growth_decimal = base_gdp_growth_decimal - (debt_drag / 100)  # Convert to decimal

        # Handle negative growth gracefully
        scale_factor = (1 + gdp_growth_decimal) * (1 + inflation_decimal)
        inflation_factor = 1 + inflation_decimal

        # Prevent GDP from going negative
        if scale_factor <= 0:
            messagebox.showerror("Error", f"Year {year}: Combined growth factor <= 0 (GDP would become negative). Simulation stopped.")
            break

        category_surplus, rev_totals = calculate_revenues_and_outs(internal_revenues, internal_outs, current_gdp, scale_factor, inflation_factor)

        if 'federal' in category_surplus:
            category_surplus['federal'] -= current_interest

        total_surplus = sum(category_surplus.values()) - internal_general['transition_fund']

        if total_surplus > 0 and current_debt > 0:
            debt_reduction = min(total_surplus, current_debt)
            current_debt -= debt_reduction
            if current_debt <= 0:
                extra_surplus = total_surplus - debt_reduction
                # Use configurable surplus_redirect_target
                redirect_target = str(internal_general.get('surplus_redirect_target', '0.0'))

                # Check if redirect_target is numeric (0.0, 0, etc.) - means "no redirect"
                is_numeric_target = False
                try:
                    numeric_val = float(redirect_target)
                    is_numeric_target = True
                    # If it's 0.0, don't redirect anything - surplus just stays as surplus
                    if numeric_val == 0.0:
                        pass  # Don't redirect - surplus remains in the system
                    # If it's non-zero numeric, that's invalid
                except (ValueError, TypeError):
                    # It's a string (category name)
                    if redirect_target in category_surplus:
                        # Valid category specified - redirect to it
                        category_surplus[redirect_target] += extra_surplus * surplus_redirect_decimal
        elif total_surplus < 0:
            # Deficit: add to debt
            current_debt += abs(total_surplus)

        current_interest = current_debt * (internal_general['interest_rate'] / 100)

        # P1: EDGE CASE - Check for debt explosion with optional stop
        if current_debt / current_gdp > 10:
            if stop_on_explosion:
                messagebox.showerror("Debt Explosion - Simulation Stopped",
                    f"Year {year}: Debt-to-GDP ratio exceeded 1000% ({current_debt/current_gdp*100:.1f}%). "
                    "Simulation stopped (stop_on_debt_explosion=1).")
                break
            else:
                messagebox.showwarning("Debt Explosion",
                    f"Year {year}: Debt-to-GDP ratio exceeded 1000% ({current_debt/current_gdp*100:.1f}%). "
                    "Simulation will continue but results may be unrealistic.")

        # EDGE CASE: Check if interest payments exceed total revenue
        total_revenue = sum(rev_totals.values())
        if current_interest > total_revenue:
            messagebox.showwarning("Interest Crisis",
                f"Year {year}: Interest payments (${current_interest:.2f}T) exceed total revenue (${total_revenue:.2f}T). "
                "Debt spiral detected - simulation may be unrealistic.")

        result = {'Year': year, 'GDP': round(current_gdp, 2), 'Total Surplus': round(total_surplus, 2), 'Remaining Debt': round(current_debt, 2)}
        # Add surplus columns
        for cat, sur in category_surplus.items():
            result[cat.capitalize() + ' Surplus'] = round(sur, 2)

        # Also include revenue time-series so we can plot revenue breakdowns
        for rev_name, rev_val in rev_totals.items():
            # e.g. 'income_tax Revenue'
            key = f"{rev_name} Revenue"
            result[key] = round(rev_val, 2)

        results.append(result)

        current_gdp *= (1 + gdp_growth_decimal)

    return pd.DataFrame(results) if results else None


def simulate_healthcare_years(policy, base_gdp: float, initial_debt: float, years: int = 22,
                              population: float = 335e6, gdp_growth: float = 0.025,
                              start_year: int = None, cbo_data: dict = None):
    """
    Context-aware multi-year healthcare simulation.

    Calculates outcomes based on extracted policy mechanics when available,
    falls back to legacy hard-coded models for backward compatibility.

    CONTEXT-AWARE MODE (policy.mechanics != None):
    - Revenue calculated from funding mechanisms (payroll, redirected federal, converted premiums, efficiency)
    - Spending calculated from target trajectory with mechanism attribution
    - Surplus allocated per policy rules (contingency, debt, infrastructure, dividends)
    - Circuit breakers enforced (spending caps, surplus triggers)

    LEGACY MODE (policy.mechanics == None):
    - Uses hard-coded USGHA values and linear interpolation
    - Maintains backward compatibility with existing policies

    Parameters
    - policy: HealthcarePolicyModel (from core.healthcare)
    - base_gdp: starting GDP in dollars
    - initial_debt: starting national debt in dollars
    - years: number of years to simulate (default 22)
    - population: population count for per-capita metrics
    - gdp_growth: annual GDP growth rate (decimal, default 0.025)
    - start_year: calendar start year (optional)
    - cbo_data: optional dict with 'revenues' and 'outs' arrays from CBO scraper

    Returns: pandas.DataFrame with yearly projections
    """
    # Input validation
    if population <= 0:
        raise ValueError("Population must be positive")
    if base_gdp <= 0:
        raise ValueError("Base GDP must be positive")
    if initial_debt < 0:
        raise ValueError("Initial debt cannot be negative")
    
    # CONTEXT-AWARE PATH: Use extracted mechanics if available
    if hasattr(policy, 'mechanics') and policy.mechanics is not None:
        return _simulate_with_mechanics(
            policy, base_gdp, initial_debt, years, population, 
            gdp_growth, start_year, cbo_data
        )
    
    # LEGACY PATH: Fall back to hard-coded model
    # Defensive imports to avoid circular dependencies at top-level
    from math import isfinite

    rows = []
    current_gdp = float(base_gdp)
    current_debt = float(initial_debt)

    # Baseline healthcare spending (January 2025) - $5.7T national healthcare
    baseline_health_spending = 5.7e12  # $5.7T

    # Baseline health spending pct (assume current US baseline if not provided)
    baseline_health_pct = 0.18

    # Determine transition target year
    timeline = policy.transition_timeline
    if start_year is None:
        start_year = timeline.start_year if timeline and timeline.start_year else 2025

    full_impl_year = timeline.full_implementation_year if timeline and timeline.full_implementation_year else (start_year + 2)
    years_to_target = max(1, full_impl_year - start_year)

    # For USGHA, spending reduction takes 20 years to reach 7% GDP (USGHA Section 2(b)(3))
    spending_transition_years = 20 if policy.policy_type == PolicyType.USGHA else years_to_target

    # Per-year linear change in health spending % toward target
    target_health_pct = float(policy.healthcare_spending_target_gdp)
    annual_health_pct_delta = (target_health_pct - baseline_health_pct) / float(spending_transition_years)


    # CORRECTED REVENUE MODEL for USGHA
    # USGHA consolidates existing federal health spending + converts private premiums
    # Initial revenues should be ~10-11% GDP ($3T+) to cover transition and generate surpluses
    
    # For USGHA: revenues come from consolidated sources as % of GDP
    # These grow with GDP and include efficiency gains over time
    if policy.policy_type == PolicyType.USGHA:
        # USGHA funding model (Section 6): consolidated + converted funding
        # Year 1: ~$1.6T federal + $1.2T converted premiums + $0.4T other = $3.2T (11% GDP)
        # Revenues as % GDP remain stable while spending decreases
        general_revenue = current_gdp * float(policy.general_revenue_pct)  # Redirected federal health
        
        # Payroll revenue: minimal direct payroll component (most comes from converted premiums)
        employment = float(policy.employment_rate) * float(population) if getattr(policy, 'employment_rate', None) is not None else 0.0
        payroll_tax_rate = float(policy.total_payroll_tax) if getattr(policy, 'total_payroll_tax', None) is not None else 0.0
        payroll_base = employment * float(policy.avg_annual_wage) * float(policy.payroll_coverage_rate)
        payroll_revenue = payroll_base * payroll_tax_rate
        
        # Other sources: converted premiums + efficiency gains
        other_sources_abs = 0.0
        if policy.other_funding_sources:
            for source_name, frac in policy.other_funding_sources.items():
                try:
                    other_sources_abs += current_gdp * float(frac)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to process USGHA funding source '{source_name}' with value '{frac}': {e}")
                    continue
        
        # Total USGHA revenue: ~10-11% GDP initially, remains stable
        revenue = payroll_revenue + general_revenue + other_sources_abs
    else:
        # Non-USGHA policies: use employment-based payroll model
        employment = float(policy.employment_rate) * float(population) if getattr(policy, 'employment_rate', None) is not None else 0.0
        payroll_tax_rate = float(policy.total_payroll_tax) if getattr(policy, 'total_payroll_tax', None) is not None else 0.0
        payroll_base = employment * float(policy.avg_annual_wage) * float(policy.payroll_coverage_rate)
        payroll_revenue = payroll_base * payroll_tax_rate
        general_revenue = current_gdp * float(policy.general_revenue_pct)
        other_sources_abs = 0.0
        if policy.other_funding_sources:
            for source_name, frac in policy.other_funding_sources.items():
                try:
                    other_sources_abs += current_gdp * float(frac)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to process funding source '{source_name}' with value '{frac}': {e}")
                    continue
        revenue = payroll_revenue + general_revenue + other_sources_abs
    
    # Initialize previous-year revenue trackers (used for tax-freeze behavior)
    prev_payroll_revenue = payroll_revenue
    prev_general_revenue = general_revenue
    prev_other_revenues = other_sources_abs

    # Iterate years
    for i in range(years):
        year = start_year + i

        # Update GDP FIRST (compounded growth from initial GDP)
        current_gdp = base_gdp * ((1.0 + gdp_growth) ** i)

        # Update health spending percent (linear towards target over transition window)
        if i < years_to_target:
            current_health_pct = baseline_health_pct + annual_health_pct_delta * i
        else:
            current_health_pct = target_health_pct

        # Calculate absolute spending
        health_spending = current_gdp * current_health_pct
        
        # UPDATE REVENUE COMPONENTS WITH GDP/WAGE GROWTH
        # Use CBO data if provided (for Current US System), otherwise use policy percentages
        if cbo_data and cbo_data.get('revenues'):
            # Use actual CBO revenue data scaled by GDP growth
            cbo_rev_dict = {}
            for rev in cbo_data['revenues']:
                cbo_rev_dict[rev['name']] = rev['value']
            
            # Scale revenues by GDP ratio and growth
            gdp_growth_multiplier = (current_gdp / base_gdp) ** (i / max(1, years))
            payroll_revenue = cbo_rev_dict.get('payroll_tax', 1.6) * 1e12 * gdp_growth_multiplier
            income_revenue = cbo_rev_dict.get('income_tax', 2.5) * 1e12 * gdp_growth_multiplier
            corporate_revenue = cbo_rev_dict.get('corporate_tax', 0.6) * 1e12 * gdp_growth_multiplier
            other_revenue = cbo_rev_dict.get('other_revenues', 1.1) * 1e12 * gdp_growth_multiplier
            
            general_revenue = income_revenue + corporate_revenue
            other_sources_abs = other_revenue
            revenue = payroll_revenue + general_revenue + other_sources_abs
        elif policy.policy_type == PolicyType.USGHA:
            # USGHA: revenues remain stable as % GDP, grow with GDP
            general_revenue = current_gdp * float(policy.general_revenue_pct)
            
            # Payroll component grows with wages (GDP growth proxy)
            employment = float(policy.employment_rate) * float(population) if getattr(policy, 'employment_rate', None) is not None else 0.0
            payroll_base = employment * float(policy.avg_annual_wage) * float(policy.payroll_coverage_rate) * ((1.0 + gdp_growth) ** i)
            payroll_revenue = payroll_base * payroll_tax_rate
            
            # Other sources grow with GDP
            other_sources_abs = 0.0
            if policy.other_funding_sources:
                for source_name, frac in policy.other_funding_sources.items():
                    try:
                        other_sources_abs += current_gdp * float(frac)
                    except Exception as e:
                        logger.warning(f"Year {year}: Failed to process funding source '{source_name}': {e}")
                        continue
            
            revenue = payroll_revenue + general_revenue + other_sources_abs
        else:
            # Use policy percentages (default behavior)
            employment = float(policy.employment_rate) * float(population) if getattr(policy, 'employment_rate', None) is not None else 0.0
            payroll_base = employment * float(policy.avg_annual_wage) * float(policy.payroll_coverage_rate) * ((1.0 + gdp_growth) ** i)
            payroll_revenue = payroll_base * payroll_tax_rate
            # General revenue grows with GDP
            general_revenue = current_gdp * float(policy.general_revenue_pct)
            # Other funding sources grow with GDP
            other_sources_abs = 0.0
            if policy.other_funding_sources:
                for source_name, frac in policy.other_funding_sources.items():
                    try:
                        other_sources_abs += current_gdp * float(frac)
                    except Exception as e:
                        logger.warning(f"Year {year}: Failed to process funding source '{source_name}': {e}")
                        continue
            # Total revenue = sum of all sources
            revenue = payroll_revenue + general_revenue + other_sources_abs

        # Category-level estimates (proportional to category current_spending_pct)
        category_spending = {}
        total_cat_share = sum([c.current_spending_pct for c in policy.categories.values()])
        for key, cat in policy.categories.items():
            share = cat.current_spending_pct / total_cat_share if total_cat_share > 0 else 0.0
            
            # H3 Fix: Apply reduction target gradually over transition years
            # reduction_target is the TOTAL reduction desired (e.g., 0.25 = 25% reduction)
            # We apply it proportionally over the transition period
            reduction_years = years_to_target
            if reduction_years > 0:
                years_elapsed = min(i, reduction_years)
                progress = years_elapsed / reduction_years
                actual_reduction = cat.reduction_target * progress  # 0 to reduction_target over time
                reduction_factor = 1.0 - actual_reduction  # SUBTRACT to reduce spending
            else:
                reduction_factor = 1.0 - cat.reduction_target  # Immediate reduction if no transition
            
            # Clamp reduction_factor to reasonable range
            # Allow 50% max reduction or 50% increase for growth categories
            reduction_factor = max(REDUCTION_FACTOR_MIN, min(REDUCTION_FACTOR_MAX, reduction_factor))
            
            # Spending for category
            category_spending[key] = health_spending * share * reduction_factor

        # Administrative savings: compute baseline admin share and new admin share
        admin_cat = policy.categories.get('administrative', None)
        admin_share = admin_cat.current_spending_pct if admin_cat else 0.16
        admin_reduction_target = admin_cat.reduction_target if admin_cat else 0.0
        # Linear admin % reduction
        admin_pct_now = admin_share + (admin_reduction_target / years_to_target) * min(i, years_to_target)
        admin_spending = health_spending * (admin_pct_now / total_cat_share) if total_cat_share > 0 else 0.0

        # Negotiation savings (pharmacy)
        pharmacy_cat = policy.categories.get('pharmacy', None)
        pharmacy_negotiation = 0.0
        if pharmacy_cat:
            # Savings realized proportional to negotiation potential and time
            realized_pct = pharmacy_cat.negotiation_potential * min(i / max(1, years_to_target), 1.0)
            pharmacy_spend = category_spending.get('pharmacy', 0.0)
            pharmacy_negotiation = pharmacy_spend * realized_pct

        # Innovation fund allocation - MOVED TO SURPLUS ALLOCATION
        # (No longer added to expenses; allocated from surplus if savings achieved)
        innovation_alloc = 0.0  # Will be calculated from surplus later

    # (revenue already computed above as absolute USD totals)

        # Surplus = revenue - health_spending + savings (pharmacy negotiation)
        # CORRECTED: NO innovation_alloc in expenses!
        total_savings = pharmacy_negotiation
        estimated_expenses = health_spending - total_savings
        surplus = revenue - estimated_expenses

        # Initialize allocation variables
        contingency_reserve = 0.0
        debt_reduction = 0.0
        infrastructure_alloc = 0.0
        dividend_pool = 0.0
        dividend_per_capita = 0.0
        savings_vs_baseline = 0.0
        innovation_alloc = 0.0

        # Apply surplus allocation to debt reduction (only portion after contingency/reserve)
        circuit_breaker_triggered = False

        # Check fiscal circuit breaker (spending as % GDP)
        spending_gdp_ratio = health_spending / current_gdp if current_gdp else 0.0
        if policy.circuit_breaker and spending_gdp_ratio > policy.circuit_breaker.spending_gdp_ceiling:
            circuit_breaker_triggered = True
            # If tax freeze enabled, freeze growth in general and other revenues this year
            if policy.circuit_breaker.tax_freeze_enabled:
                general_revenue = prev_general_revenue
                other_sources_abs = prev_other_revenues
                # payroll revenue typically depends on wages and employment; freeze payroll revenue too if conservative
                payroll_revenue = prev_payroll_revenue
                revenue = payroll_revenue + general_revenue + other_sources_abs
            # Apply a conservative immediate spending cut to bring spending down
            cut_pct = getattr(policy.circuit_breaker, 'spending_cut_pct', 0.05)
            try:
                health_spending = health_spending * (1.0 - float(cut_pct))
            except (ValueError, TypeError) as e:
                # if malformed, default to 5% cut
                logger.warning(f"Year {year}: Failed to parse spending_cut_pct '{cut_pct}': {e}. Using default 5% cut")
                health_spending = health_spending * 0.95

        if surplus > 0:
            # ========== SURPLUS ALLOCATION (Section 11(a)) ==========
            # Allocate surplus per legislation
            contingency_reserve = surplus * 0.10
            remaining_surplus = surplus - contingency_reserve
            
            debt_reduction = remaining_surplus * 0.70
            infrastructure_alloc = remaining_surplus * 0.10
            dividend_pool = remaining_surplus * 0.10
            
            # Apply debt reduction
            current_debt = max(0.0, current_debt - debt_reduction)
            
            # Calculate per-capita dividend (April 15 payment)
            dividend_per_capita = dividend_pool / population if population else 0
            
            # ========== INNOVATION FUND ALLOCATION ==========
            # GHIF from verified savings (Section 9(a)(2))
            savings_vs_baseline = baseline_health_spending - health_spending
            if savings_vs_baseline > 0:
                # Conservative: use 10% of verified savings
                ghif_allocation_pct = 0.10
                innovation_alloc = savings_vs_baseline * ghif_allocation_pct
            else:
                innovation_alloc = 0.0
        else:
            # Deficit increases debt
            current_debt += abs(surplus)
            contingency_reserve = 0.0
            debt_reduction = 0.0
            infrastructure_alloc = 0.0
            dividend_pool = 0.0
            dividend_per_capita = 0.0
            innovation_alloc = 0.0
            savings_vs_baseline = 0.0

        # Update previous-year revenue trackers for next iteration
        prev_payroll_revenue = payroll_revenue
        prev_general_revenue = general_revenue
        prev_other_revenues = other_sources_abs

        # Record metrics
        per_capita = health_spending / population if population and isfinite(population) else None

        rows.append({
            'Year': year,
            'GDP': current_gdp,
            'Health Spending ($)': health_spending,
            'Health % GDP': current_health_pct,
            'Per Capita Health ($)': per_capita,
            'Revenue ($)': revenue,
            'Payroll Revenue ($)': payroll_revenue,
            'General Revenue ($)': general_revenue,
            'Other Revenues ($)': other_sources_abs,
            'Baseline Health Spending ($)': baseline_health_spending,
            'Savings vs Baseline ($)': savings_vs_baseline,
            'Innovation Fund ($)': innovation_alloc,
            'Pharmacy Negotiation Savings ($)': pharmacy_negotiation,
            'Administrative Spending ($)': admin_spending,
            'Surplus ($)': surplus,
            'Contingency Reserve ($)': contingency_reserve,
            'Debt Reduction ($)': debt_reduction,
            'Infrastructure Allocation ($)': infrastructure_alloc,
            'Dividend Pool ($)': dividend_pool,
            'Dividend Per Capita ($)': dividend_per_capita,
            'Remaining Debt ($)': current_debt,
            'Circuit Breaker Triggered': circuit_breaker_triggered,
        })

        # GDP already updated at start of loop

    return pd.DataFrame(rows)
