"""
Centralized tooltip registry for Streamlit UI components.
Provides reusable tooltip strings and helpers for consistent help text.
"""

from typing import Dict, Optional

TOOLTIPS: Dict[str, str] = {
    # Healthcare
    "healthcare_spending_target": "Target healthcare spending as percentage of GDP. Lower = more efficient system.",
    "circuit_breaker": "Automatic policy adjustment when spending exceeds thresholds. Prevents runaway costs.",
    "innovation_fund": "Dedicated funding for healthcare R&D, prizes, and breakthrough initiatives.",
    "healthcare_policy_builtin": "Choose a baseline or proposed healthcare policy to simulate against the default US system.",
    "healthcare_policy_custom": "Select one of your saved custom healthcare scenarios to run with live inputs.",
    "healthcare_projection_years": "Number of years to simulate healthcare spending and revenues. Longer horizons show sustainability trends.",
    "healthcare_base_gdp": "Starting GDP level in trillions. Used to size healthcare spending and debt paths.",
    "healthcare_initial_debt": "Current national debt in trillions. Sets the starting point for debt trajectory calculations.",

    # Social Security
    "payroll_tax_rate": "Combined employer + employee Social Security tax rate. Current law: 12.4% (6.2% each).",
    "wage_cap": "Maximum annual earnings subject to Social Security tax. 2025 cap: $168,600.",
    "full_retirement_age": "Age at which workers can claim full benefits without reduction. Currently 67 for those born 1960+.",
    "cola": "Cost of Living Adjustment - annual increase in benefits to account for inflation.",
    "trust_fund_depletion": "Year when reserves are exhausted and can only pay about 77% of scheduled benefits.",

    # Revenue
    "gdp_growth": "Real GDP growth rate (inflation-adjusted). Historical average is roughly 2-3% annually.",
    "wage_growth": "Average wage growth rate. Affects payroll tax revenue and Social Security benefits.",
    "baseline_scenario": "Projection under current law with no policy changes. Used as reference point.",
    "revenue_economic_scenario": "Preset macro assumptions for GDP and wage growth used to drive revenue projections.",
    "revenue_projection_years": "How far forward to project federal revenues. 10-year windows align with budget scoring.",
    "revenue_iterations": "Monte Carlo runs for revenue uncertainty. More runs tighten confidence intervals but take longer.",

    # Monte Carlo
    "monte_carlo_iterations": "Number of simulation runs with varying assumptions. More iterations improve accuracy but take longer.",
    "confidence_interval": "Range of outcomes with specified probability. A 90% CI means 90% of outcomes fall in this range.",
    "p10_p90": "P10 is the best 10% of outcomes, P90 is the worst 10%. Shows the range of uncertainty.",

    # Policy
    "policy_type": "Policy category: Healthcare, Tax Reform, Spending Reform, or Combined.",
    "policy_parameters": "Adjustable values that define policy behavior (rates, caps, thresholds).",
    "policy_versioning": "Save multiple versions of a policy to track changes over time.",

    # General Fiscal
    "deficit": "Annual shortfall when spending exceeds revenue. Increases national debt.",
    "surplus": "Annual excess when revenue exceeds spending. Can reduce national debt.",
    "national_debt": "Cumulative total of all deficits minus surpluses.",
    "debt_to_gdp": "National debt as percentage of GDP. Above 100% is concerning for sustainability.",
    "primary_balance": "Budget balance excluding interest payments. Shows underlying fiscal health.",
    "mandatory_spending": "Spending required by law (Social Security, Medicare, Medicaid). Roughly two-thirds of the budget.",
    "discretionary_spending": "Spending set by annual appropriations (defense, education). Roughly one-third of the budget.",
    "medicare_projection_years": "Horizon for Medicare projections. Longer windows capture trust fund dynamics and demographic shifts.",
    "medicare_iterations": "Monte Carlo runs for Medicare. Captures uncertainty in enrollment and cost trends.",
    "medicaid_projection_years": "Horizon for Medicaid projections. Reflects joint federal/state funding needs over time.",
    "medicaid_iterations": "Monte Carlo runs for Medicaid. Captures volatility in enrollment and per-capita costs.",
    "combined_projection_years": "Years to simulate the unified federal outlook (revenue + spending + interest).",
    "combined_iterations": "Monte Carlo runs for the unified outlook. Higher counts give smoother confidence bands.",
    "defense_scenario": "Defense spending growth path (baseline, growth, reduction) used in discretionary projections.",
    "nondefense_scenario": "Non-defense discretionary growth path (baseline, growth, reduction) covering education, transport, etc.",
    "discretionary_projection_years": "Projection horizon for discretionary spending (defense + non-defense). Longer windows show appropriation sensitivity.",
    "combined_revenue_scenario": "Macro assumption set driving revenue and discretionary forecasts (baseline, recession, strong growth, demographic).",
    "combined_discretionary_scenario": "Growth path for discretionary spending (baseline, growth, reduction). Influences defense/non-defense outlays.",
    "combined_interest_scenario": "Projected path for interest rates on federal debt (baseline, rising, falling, spike). Affects debt service costs.",
}


def get_tooltip(key: str, fallback: Optional[str] = None) -> str:
    """Return tooltip text by key, with optional fallback."""
    return TOOLTIPS.get(key, fallback or "")


def add_tooltip_icon(label: str, tooltip_key: str) -> str:
    """Append an info marker to labels that have tooltips."""
    tooltip = get_tooltip(tooltip_key)
    if tooltip:
        return f"{label} (i)"
    return label
