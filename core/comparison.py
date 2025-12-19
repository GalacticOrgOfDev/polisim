"""Policy comparison utilities for healthcare simulations.

Provides helpers to run multiple policy simulations, produce per-policy
time-series outputs, and synthesize concise summary metrics and difference
matrices useful for policymaker reports and Excel exports.
"""

from typing import List, Dict, Tuple
import pandas as pd
from core.simulation import simulate_healthcare_years
from core.healthcare import HealthcarePolicyModel


def summarize_timeseries(df: pd.DataFrame, population: float) -> pd.DataFrame:
    """Create a one-row summary from a multi-year simulation DataFrame.

    Returns cumulative and final-state metrics useful for comparison.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # cumulative metrics
    cum_surplus = df['Surplus ($)'].sum() if 'Surplus ($)' in df.columns else 0.0
    cum_debt_reduction = df['Debt Reduction ($)'].sum() if 'Debt Reduction ($)' in df.columns else 0.0
    final_debt = df['Remaining Debt ($)'].iloc[-1] if 'Remaining Debt ($)' in df.columns else None
    avg_health_pct = df['Health % GDP'].mean() if 'Health % GDP' in df.columns else None
    avg_per_capita = df['Per Capita Health ($)'].mean() if 'Per Capita Health ($)' in df.columns else None
    total_payroll = df['Payroll Revenue ($)'].sum() if 'Payroll Revenue ($)' in df.columns else 0.0
    total_general = df['General Revenue ($)'].sum() if 'General Revenue ($)' in df.columns else 0.0
    total_other = df['Other Revenues ($)'].sum() if 'Other Revenues ($)' in df.columns else 0.0
    total_innovation = df['Innovation Fund ($)'].sum() if 'Innovation Fund ($)' in df.columns else 0.0
    total_pharmacy_savings = df['Pharmacy Negotiation Savings ($)'].sum() if 'Pharmacy Negotiation Savings ($)' in df.columns else 0.0
    circuit_triggers = int(df['Circuit Breaker Triggered'].sum()) if 'Circuit Breaker Triggered' in df.columns else 0

    summary = {
        'Cumulative Surplus ($)': cum_surplus,
        'Cumulative Debt Reduction ($)': cum_debt_reduction,
        'Final Remaining Debt ($)': final_debt,
        'Avg Health % GDP': avg_health_pct,
        'Avg Per Capita Health ($)': avg_per_capita,
        'Total Payroll Revenue ($)': total_payroll,
        'Total General Revenue ($)': total_general,
        'Total Other Revenue ($)': total_other,
        'Total Innovation Fund ($)': total_innovation,
        'Total Pharmacy Savings ($)': total_pharmacy_savings,
        'Circuit Breaker Triggers': circuit_triggers,
        'Years Simulated': len(df),
    }

    # Normalize per-capita and percent-of-GDP where useful
    if population and population > 0:
        summary['Cumulative Surplus Per Capita ($)'] = cum_surplus / population
        summary['Cumulative Debt Reduction Per Capita ($)'] = cum_debt_reduction / population

    return pd.DataFrame([summary])


def compare_and_summarize(policies: List[HealthcarePolicyModel], base_gdp: float, initial_debt: float, years: int = 22, population: float = 335e6, gdp_growth: float = 0.025, start_year: int = 2027) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Run simulations for multiple policies and return:

    - dict of policy_name -> time-series DataFrame
    - summary_table: DataFrame where each row is a policy summary
    - diff_table: DataFrame expressing differences vs the first policy (baseline)

    The first policy in `policies` is treated as the baseline for difference calculations.
    """
    time_series: Dict[str, pd.DataFrame] = {}
    summaries = []

    for p in policies:
        df = simulate_healthcare_years(p, base_gdp=base_gdp, initial_debt=initial_debt, years=years, population=population, gdp_growth=gdp_growth, start_year=start_year)
        time_series[p.policy_name] = df
        summ = summarize_timeseries(df, population)
        summ.insert(0, 'Policy', p.policy_name)
        summaries.append(summ)

    summary_table = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()

    # Build difference table vs baseline (first policy)
    diff_table = pd.DataFrame()
    if not summary_table.empty and len(summary_table) > 1:
        baseline = summary_table.iloc[0]
        diffs = []
        for idx in range(1, len(summary_table)):
            row = summary_table.iloc[idx]
            diff = {'Policy': row['Policy']}
            for col in summary_table.columns:
                if col == 'Policy':
                    continue
                try:
                    diff[col + ' vs Baseline'] = row[col] - baseline[col]
                except Exception:
                    diff[col + ' vs Baseline'] = None
            diffs.append(diff)
        diff_table = pd.DataFrame(diffs)

    return time_series, summary_table, diff_table


def list_available_metrics() -> List[str]:
    """Return a list of summary metrics produced by summarize_timeseries.

    Useful for building report templates and ensuring stable column names.
    """
    return [
        'Cumulative Surplus ($)', 'Cumulative Debt Reduction ($)', 'Final Remaining Debt ($)', 'Avg Health % GDP',
        'Avg Per Capita Health ($)', 'Total Payroll Revenue ($)', 'Total General Revenue ($)', 'Total Other Revenue ($)',
        'Total Innovation Fund ($)', 'Total Pharmacy Savings ($)', 'Circuit Breaker Triggers', 'Years Simulated',
        'Cumulative Surplus Per Capita ($)', 'Cumulative Debt Reduction Per Capita ($)'
    ]


def build_normalized_timeseries(time_series: Dict[str, pd.DataFrame], population: float) -> pd.DataFrame:
    """Return a concatenated DataFrame with per-year normalized metrics for each policy.

    Columns: Policy, Year, Health Spending ($), Health % GDP, Health per Capita ($),
    Revenue per Capita ($), Surplus per Capita ($), Remaining Debt ($)
    """
    rows = []
    for policy_name, df in time_series.items():
        if df is None or df.empty:
            continue
        for _, r in df.iterrows():
            year = r.get('Year')
            health_spend = r.get('Health Spending ($)', 0.0)
            health_pct = r.get('Health % GDP', None)
            revenue = r.get('Revenue ($)', None)
            surplus = r.get('Surplus ($)', None)
            remaining_debt = r.get('Remaining Debt ($)', None)
            per_capita_health = (health_spend / population) if population and population > 0 else None
            revenue_per_capita = (revenue / population) if revenue is not None and population and population > 0 else None
            surplus_per_capita = (surplus / population) if surplus is not None and population and population > 0 else None

            rows.append({
                'Policy': policy_name,
                'Year': year,
                'Health Spending ($)': health_spend,
                'Health % GDP': health_pct,
                'Health per Capita ($)': per_capita_health,
                'Revenue per Capita ($)': revenue_per_capita,
                'Surplus per Capita ($)': surplus_per_capita,
                'Remaining Debt ($)': remaining_debt,
            })

    return pd.DataFrame(rows)

