"""Plotly-based healthcare visualizations.

Provides functions to create publication-quality charts and save them to PNG.
Prioritizes visuals for dashboards; can be used offline to generate static images
for reports.
"""
import os
from typing import Dict
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Styling constants
DEFAULT_TEMPLATE = 'plotly_white'
COLORWAY = ['#0b5ea8', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd', '#8c564b']
FONT_FAMILY = 'DejaVu Sans, Arial, sans-serif'
DEFAULT_WIDTH = 1000
DEFAULT_HEIGHT = 600


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def plot_spending_trend(df: pd.DataFrame, out_path: str = None) -> go.Figure:
    """Plot Health Spending ($) and Health % GDP over time."""
    fig = go.Figure()
    if 'Health Spending ($)' in df.columns:
        fig.add_trace(go.Bar(x=df['Year'], y=df['Health Spending ($)'], name='Health Spending ($)', marker_color=COLORWAY[0]))
    if 'Health % GDP' in df.columns:
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Health % GDP'], name='Health % GDP', yaxis='y2', line=dict(color=COLORWAY[1], width=3)))

    fig.update_layout(title='Health Spending Trend', xaxis_title='Year', yaxis_title='Health Spending ($)', template=DEFAULT_TEMPLATE,
                      font=dict(family=FONT_FAMILY), colorway=COLORWAY, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)
    fig.update_layout(yaxis2=dict(overlaying='y', side='right', title='Health % GDP'))

    if out_path:
        ensure_dir(os.path.dirname(out_path))
        fig.write_image(out_path)
        # Also write interactive HTML next to PNG
        try:
            html_path = os.path.splitext(out_path)[0] + '.html'
            fig.write_html(html_path, include_plotlyjs='cdn')
        except Exception:
            pass
    return fig


def plot_revenue_breakdown(df: pd.DataFrame, out_path: str = None) -> go.Figure:
    """Plot stacked area or bar chart of Payroll, General, Other revenues over time."""
    cols = [c for c in ['Payroll Revenue ($)', 'General Revenue ($)', 'Other Revenues ($)'] if c in df.columns]
    if not cols:
        # fallback: plot Revenue ($)
        if 'Revenue ($)' in df.columns:
            fig = px.area(df, x='Year', y='Revenue ($)', title='Revenue Over Time')
        else:
            fig = go.Figure()
    else:
        fig = go.Figure()
        for c in cols:
            fig.add_trace(go.Scatter(x=df['Year'], y=df[c], stackgroup='one', name=c))

    fig.update_layout(title='Revenue Breakdown', xaxis_title='Year', yaxis_title='Revenue ($)', template=DEFAULT_TEMPLATE,
                      font=dict(family=FONT_FAMILY), colorway=COLORWAY, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)
    if out_path:
        ensure_dir(os.path.dirname(out_path))
        fig.write_image(out_path)
        try:
            html_path = os.path.splitext(out_path)[0] + '.html'
            fig.write_html(html_path, include_plotlyjs='cdn')
        except Exception:
            pass
    return fig


def plot_debt_and_surplus(df: pd.DataFrame, out_path: str = None) -> go.Figure:
    """Plot Remaining Debt and Surplus over time."""
    fig = go.Figure()
    if 'Remaining Debt ($)' in df.columns:
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Remaining Debt ($)'], name='Remaining Debt ($)'))
    if 'Surplus ($)' in df.columns:
        fig.add_trace(go.Bar(x=df['Year'], y=df['Surplus ($)'], name='Surplus ($)'))

    fig.update_layout(title='Debt and Surplus', xaxis_title='Year', template=DEFAULT_TEMPLATE, font=dict(family=FONT_FAMILY),
                      colorway=COLORWAY, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)
    if out_path:
        ensure_dir(os.path.dirname(out_path))
        fig.write_image(out_path)
        try:
            html_path = os.path.splitext(out_path)[0] + '.html'
            fig.write_html(html_path, include_plotlyjs='cdn')
        except Exception:
            pass
    return fig


def build_all_charts(time_series: Dict[str, pd.DataFrame], output_dir: str = 'reports/charts') -> Dict[str, Dict[str, str]]:
    """Create charts for each policy in time_series.

    Returns mapping policy_name -> {chart_name: filepath}
    """
    mapping = {}
    ensure_dir(output_dir)
    for name, df in time_series.items():
        safe_name = name.replace(' ', '_').replace('/', '_')
        policy_dir = os.path.join(output_dir, safe_name)
        ensure_dir(policy_dir)
        files = {}
        # Spending trend
        sp = os.path.join(policy_dir, f'{safe_name}_spending.png')
        plot_spending_trend(df, out_path=sp)
        files['spending_png'] = sp
        files['spending_html'] = os.path.splitext(sp)[0] + '.html'
        # Revenue breakdown
        rv = os.path.join(policy_dir, f'{safe_name}_revenue.png')
        plot_revenue_breakdown(df, out_path=rv)
        files['revenue_png'] = rv
        files['revenue_html'] = os.path.splitext(rv)[0] + '.html'
        # Debt and surplus
        ds = os.path.join(policy_dir, f'{safe_name}_debt_surplus.png')
        plot_debt_and_surplus(df, out_path=ds)
        files['debt_surplus_png'] = ds
        files['debt_surplus_html'] = os.path.splitext(ds)[0] + '.html'
        # Per-category waterfall chart (if categories present)
        try:
            if 'Pharmacy Negotiation Savings ($)' in df.columns or any(c.endswith(' Surplus') for c in df.columns):
                wf = os.path.join(policy_dir, f'{safe_name}_category_waterfall.png')
                # Simple per-year stacked bar of categories using columns that end with ' Surplus' as proxy
                cat_cols = [c for c in df.columns if c.endswith(' Surplus')]
                if cat_cols:
                    fig = go.Figure()
                    for c in cat_cols:
                        fig.add_trace(go.Bar(x=df['Year'], y=df[c], name=c))
                    fig.update_layout(title='Category Surplus by Year', xaxis_title='Year', yaxis_title='$')
                    fig.write_image(wf)
                    try:
                        fig.write_html(os.path.splitext(wf)[0] + '.html')
                    except Exception:
                        pass
                    files['category_waterfall_png'] = wf
                    files['category_waterfall_html'] = os.path.splitext(wf)[0] + '.html'
        except Exception:
            # don't let optional chart failures break main pipeline
            pass

        mapping[name] = files
    return mapping
