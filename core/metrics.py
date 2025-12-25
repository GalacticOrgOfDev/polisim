"""Metrics computation for policy analysis.

This module contains functions for computing fiscal metrics and
comparing policies using CBO-style analysis.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def compute_policy_metrics(df):
    """Compute core fiscal metrics for a single policy DataFrame.

    Returns a dict mapping metric name -> value. Designed to be robust to
    missing/empty data so that the UI never crashes.
    
    Args:
        df: pandas DataFrame with simulation results
    
    Returns:
        Dict of metric_name -> value pairs
    """
    try:
        import pandas as _pd  # local import to avoid issues if pandas is missing
    except Exception as e:  # pragma: no cover - should already be imported at top
        logger.warning(f"Failed to import pandas: {e}")
        _pd = None

    if df is None or _pd is None:
        return {}
    try:
        if getattr(df, "empty", True):  # handles non-DataFrame inputs safely
            return {}
    except Exception as e:
        logger.warning(f"Failed to check if DataFrame is empty: {e}")
        return {}

    metrics = {}

    # Basic horizon information
    try:
        metrics['Simulation years'] = int(len(df))
    except Exception as e:
        logger.warning(f"Failed to compute simulation years: {e}")
        pass

    # Surplus-related metrics
    if 'Total Surplus' in df.columns:
        try:
            total_surplus = float(df['Total Surplus'].sum())
            avg_surplus = float(df['Total Surplus'].mean())
            metrics['Cumulative total surplus (T$)'] = round(total_surplus, 2)
            metrics['Average annual surplus (T$/yr)'] = round(avg_surplus, 2)
        except Exception as e:
            logger.warning(f"Failed to compute surplus metrics: {e}")
            pass

    # Debt and debt-to-GDP metrics
    if 'Remaining Debt' in df.columns and 'GDP' in df.columns:
        try:
            if df.empty:
                logger.warning("DataFrame is empty, skipping debt metrics")
                return metrics
            
            final_debt = float(df['Remaining Debt'].iloc[-1])
            start_debt = float(df['Remaining Debt'].iloc[0])
            metrics['Final year debt (T$)'] = round(final_debt, 2)
            metrics['Change in debt over horizon (T$)'] = round(final_debt - start_debt, 2)

            debt_to_gdp = (df['Remaining Debt'] / df['GDP']) * 100.0
            peak_ratio = float(debt_to_gdp.max())
            peak_year = int(df.loc[debt_to_gdp.idxmax(), 'Year'])
            min_ratio = float(debt_to_gdp.min())
            min_year = int(df.loc[debt_to_gdp.idxmin(), 'Year'])

            metrics['Peak debt-to-GDP ratio (%)'] = round(peak_ratio, 1)
            metrics['Year of peak debt-to-GDP'] = peak_year
            metrics['Lowest debt-to-GDP ratio (%)'] = round(min_ratio, 1)
            metrics['Year of lowest debt-to-GDP'] = min_year

            zero_debt_rows = df[df['Remaining Debt'] <= 0]
            if not zero_debt_rows.empty:
                metrics['Year debt fully paid off (<=0 T$)'] = int(zero_debt_rows['Year'].iloc[0])
            else:
                metrics['Year debt fully paid off (<=0 T$)'] = "Not within horizon"
        except Exception as e:
            logger.warning(f"Failed to compute debt metrics: {e}")
            pass

    return metrics


def calculate_cbo_summary(df_current, df_proposed):
    """Calculate CBO-style summary metrics comparing current vs proposed policy.

    Returns (summary_text, summary_table_df).
    
    - summary_text: human-readable multi-line string for the UI
    - summary_table_df: pandas DataFrame suitable for export, with columns:
      [Metric, Current Policy, Proposed Policy, Difference (Proposed - Current)]
    
    Args:
        df_current: pandas DataFrame with current policy simulation results
        df_proposed: pandas DataFrame with proposed policy simulation results
    
    Returns:
        Tuple of (summary_text, summary_table_df)
    """
    cur_metrics = compute_policy_metrics(df_current)
    prop_metrics = compute_policy_metrics(df_proposed)

    # Build tabular representation first
    all_keys = sorted(set(cur_metrics.keys()) | set(prop_metrics.keys()))
    rows = []
    for key in all_keys:
        cur_val = cur_metrics.get(key)
        prop_val = prop_metrics.get(key)
        diff = None
        if isinstance(cur_val, (int, float)) and isinstance(prop_val, (int, float)):
            try:
                diff = round(prop_val - cur_val, 2)
            except Exception as e:
                logger.warning(f"Failed to compute difference for metric '{key}': {e}")
                diff = None
        rows.append({
            'Metric': key,
            'Current Policy': cur_val,
            'Proposed Policy': prop_val,
            'Difference (Proposed - Current)': diff,
        })

    summary_table = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['Metric', 'Current Policy', 'Proposed Policy', 'Difference (Proposed - Current)'])

    # Build human-readable text summary
    lines = []
    lines.append("=== CBO-Style Budget Summary ===")

    if summary_table.empty:
        lines.append("Run a successful simulation for both current and proposed policy to see a summary here.")
        return "\n".join(lines), summary_table

    horizon = cur_metrics.get('Simulation years') or prop_metrics.get('Simulation years')
    if horizon:
        lines.append(f"Horizon: {horizon} year(s) of simulation")
    lines.append("")

    def _fmt(val, suffix=""):
        if isinstance(val, (int, float)):
            return f"{val:,.2f}{suffix}" if isinstance(val, float) else f"{val:,}{suffix}"
        return str(val) if val is not None else "N/A"

    # Cumulative surplus
    c_cur = cur_metrics.get('Cumulative total surplus (T$)')
    c_prop = prop_metrics.get('Cumulative total surplus (T$)')
    if c_cur is not None or c_prop is not None:
        if isinstance(c_cur, (int, float)) and isinstance(c_prop, (int, float)):
            delta = c_prop - c_cur
        else:
            delta = None
        lines.append(
            f"• Cumulative total surplus over horizon: Current {_fmt(c_cur, 'T')}, "
            f"Proposed {_fmt(c_prop, 'T')} (Δ {_fmt(delta, 'T')})."
        )

    # Final debt level
    d_cur = cur_metrics.get('Final year debt (T$)')
    d_prop = prop_metrics.get('Final year debt (T$)')
    if d_cur is not None or d_prop is not None:
        if isinstance(d_cur, (int, float)) and isinstance(d_prop, (int, float)):
            delta_d = d_prop - d_cur
        else:
            delta_d = None
        lines.append(
            f"• Final-year debt: Current {_fmt(d_cur, 'T')}, Proposed {_fmt(d_prop, 'T')} "
            f"(Δ {_fmt(delta_d, 'T')})."
        )

    # Peak debt-to-GDP
    r_cur = cur_metrics.get('Peak debt-to-GDP ratio (%)')
    y_cur = cur_metrics.get('Year of peak debt-to-GDP')
    r_prop = prop_metrics.get('Peak debt-to-GDP ratio (%)')
    y_prop = prop_metrics.get('Year of peak debt-to-GDP')
    if r_cur is not None or r_prop is not None:
        lines.append(
            f"• Peak debt-to-GDP: Current {_fmt(r_cur, '%')} in year {_fmt(y_cur)}, "
            f"Proposed {_fmt(r_prop, '%')} in year {_fmt(y_prop)}."
        )

    # Debt elimination
    yr_cur_zero = cur_metrics.get('Year debt fully paid off (<=0 T$)')
    yr_prop_zero = prop_metrics.get('Year debt fully paid off (<=0 T$)')
    if yr_cur_zero is not None or yr_prop_zero is not None:
        lines.append(
            f"• Year debt fully paid off (if ever): Current {_fmt(yr_cur_zero)}, "
            f"Proposed {_fmt(yr_prop_zero)}."
        )

    return "\n".join(lines), summary_table
