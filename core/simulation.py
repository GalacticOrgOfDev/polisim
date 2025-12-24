"""Simulation engine for economic policy scenarios.

This module handles multi-year simulations of economic policies,
tracking GDP, debt, surplus, and other macroeconomic indicators.
"""

import pandas as pd
from tkinter import messagebox
from core.economics import calculate_revenues_and_outs


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
                              start_year: int = None):
    """
    Simplified multi-year healthcare-focused simulation.

    This function produces a conservative government-ready projection for
    healthcare spending, innovation fund allocation, savings from negotiation
    and administrative reforms, and the resulting surpluses used to reduce
    national debt.

    Parameters
    - policy: HealthcarePolicyModel (from core.healthcare)
    - base_gdp: starting GDP in dollars
    - initial_debt: starting national debt in dollars
    - years: number of years to simulate (default 22)
    - population: population count for per-capita metrics
    - gdp_growth: annual GDP growth rate (decimal, default 0.025)
    - start_year: calendar start year (optional)

    Returns: pandas.DataFrame with yearly projections
    """
    # Defensive imports to avoid circular dependencies at top-level
    from math import isfinite

    rows = []
    current_gdp = float(base_gdp)
    current_debt = float(initial_debt)

    # Baseline health spending pct (assume current US baseline if not provided)
    baseline_health_pct = 0.18

    # Determine transition target year
    timeline = policy.transition_timeline
    if start_year is None:
        start_year = timeline.start_year if timeline and timeline.start_year else 2025

    full_impl_year = timeline.full_implementation_year if timeline and timeline.full_implementation_year else (start_year + 2)
    years_to_target = max(1, full_impl_year - start_year)

    # Per-year linear change in health spending % toward target
    target_health_pct = float(policy.healthcare_spending_target_gdp)
    annual_health_pct_delta = (target_health_pct - baseline_health_pct) / float(years_to_target)


    # Refined revenue model (absolute USD values)
    # Use optional labor inputs from the policy (employment_rate, avg_annual_wage)
    # Payroll revenue = employed_people * avg_wage * payroll_coverage * payroll_tax_rate
    employment = float(policy.employment_rate) * float(population) if getattr(policy, 'employment_rate', None) is not None else 0.0
    payroll_tax_rate = float(policy.total_payroll_tax) if getattr(policy, 'total_payroll_tax', None) is not None else 0.0
    payroll_base = employment * float(policy.avg_annual_wage) * float(policy.payroll_coverage_rate)
    payroll_revenue = payroll_base * payroll_tax_rate
    # General revenue: fraction of GDP
    general_revenue = current_gdp * float(policy.general_revenue_pct)
    # Other funding sources expressed as fractions of GDP in the policy
    other_sources_abs = 0.0
    if policy.other_funding_sources:
        for _, frac in policy.other_funding_sources.items():
            try:
                other_sources_abs += current_gdp * float(frac)
            except Exception:
                # skip malformed entries
                continue
    # Total revenue is the sum of payroll-derived, general, and other sources
    revenue = payroll_revenue + general_revenue + other_sources_abs
    # Initialize previous-year revenue trackers (used for tax-freeze behavior)
    prev_payroll_revenue = payroll_revenue
    prev_general_revenue = general_revenue
    prev_other_revenues = other_sources_abs

    # Iterate years
    for i in range(years):
        year = start_year + i

        # Update health spending percent (linear towards target over transition window)
        if i < years_to_target:
            current_health_pct = baseline_health_pct + annual_health_pct_delta * i
        else:
            current_health_pct = target_health_pct

        # Calculate absolute spending
        health_spending = current_gdp * current_health_pct
        
        # UPDATE REVENUE COMPONENTS WITH GDP/WAGE GROWTH
        # Payroll revenue grows with employment and wage growth
        employment = float(policy.employment_rate) * float(population) if getattr(policy, 'employment_rate', None) is not None else 0.0
        payroll_base = employment * float(policy.avg_annual_wage) * float(policy.payroll_coverage_rate) * ((1.0 + gdp_growth) ** i)
        payroll_revenue = payroll_base * payroll_tax_rate
        # General revenue grows with GDP
        general_revenue = current_gdp * float(policy.general_revenue_pct)
        # Other funding sources grow with GDP
        other_sources_abs = 0.0
        if policy.other_funding_sources:
            for _, frac in policy.other_funding_sources.items():
                try:
                    other_sources_abs += current_gdp * float(frac)
                except Exception:
                    continue
        # Total revenue = sum of all sources
        revenue = payroll_revenue + general_revenue + other_sources_abs

        # Category-level estimates (proportional to category current_spending_pct)
        category_spending = {}
        total_cat_share = sum([c.current_spending_pct for c in policy.categories.values()])
        for key, cat in policy.categories.items():
            share = cat.current_spending_pct / total_cat_share if total_cat_share > 0 else 0.0
            # Apply reduction target gradually over transition years
            reduction_years = years_to_target
            per_year_reduction = cat.reduction_target / reduction_years if reduction_years > 0 else 0.0
            reduction_factor = 1.0 + per_year_reduction * min(i, reduction_years)
            # Spending for category
            category_spending[key] = health_spending * share * reduction_factor

        # Administrative savings: compute baseline admin share and new admin share
        admin_cat = policy.categories.get('administrative')
        admin_share = admin_cat.current_spending_pct if admin_cat else 0.16
        admin_reduction_target = admin_cat.reduction_target if admin_cat else 0.0
        # Linear admin % reduction
        admin_pct_now = admin_share + (admin_reduction_target / years_to_target) * min(i, years_to_target)
        admin_spending = health_spending * (admin_pct_now / total_cat_share) if total_cat_share > 0 else 0.0

        # Negotiation savings (pharmacy)
        pharmacy_cat = policy.categories.get('pharmacy')
        pharmacy_negotiation = 0.0
        if pharmacy_cat:
            # Savings realized proportional to negotiation potential and time
            realized_pct = pharmacy_cat.negotiation_potential * min(i / max(1, years_to_target), 1.0)
            pharmacy_spend = category_spending.get('pharmacy', 0.0)
            pharmacy_negotiation = pharmacy_spend * realized_pct

        # Innovation fund allocation
        innovation_alloc = 0.0
        if policy.innovation_fund:
            innovation_alloc = health_spending * policy.innovation_fund.annual_allocation_pct

    # (revenue already computed above as absolute USD totals)

        # Surplus = revenue - (health_spending + innovation_alloc) + admin & negotiation savings
        total_savings = pharmacy_negotiation
        estimated_expenses = health_spending + innovation_alloc - total_savings
        surplus = revenue - estimated_expenses

        # Apply surplus allocation to debt reduction (only portion after contingency/reserve)
        debt_reduction = 0.0
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
            except Exception:
                # if malformed, default to 5% cut
                health_spending = health_spending * 0.95

        if surplus > 0:
            # Reserve portion
            reserve_pct = policy.surplus_allocation.contingency_reserve_pct if policy.surplus_allocation else 0.10
            reserve = surplus * reserve_pct
            distributable = surplus - reserve
            # Debt reduction is primary recipient
            debt_reduction_pct = policy.surplus_allocation.national_debt_reduction_pct if policy.surplus_allocation else 0.50
            debt_reduction = distributable * debt_reduction_pct
            current_debt = max(0.0, current_debt - debt_reduction)
        else:
            # Deficit increases debt
            current_debt += abs(surplus)

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
            'Innovation Fund ($)': innovation_alloc,
            'Pharmacy Negotiation Savings ($)': pharmacy_negotiation,
            'Administrative Spending ($)': admin_spending,
            'Surplus ($)': surplus,
            'Debt Reduction ($)': debt_reduction,
            'Remaining Debt ($)': current_debt,
            'Circuit Breaker Triggered': circuit_breaker_triggered,
        })

        # Update GDP by growth
        current_gdp = current_gdp * (1.0 + gdp_growth)

    return pd.DataFrame(rows)
