"""Run a comparison between baseline and USGHA and export results for review.

Produces an Excel workbook with time-series sheets and a CBO-style summary.
"""
from core.healthcare import HealthcarePolicyFactory
from core.comparison import compare_and_summarize
from utils.io import export_results_to_file
import pandas as pd
import os


def run_and_export(output_path: str = 'usgha_comparison.xlsx'):
    baseline = HealthcarePolicyFactory.create_current_us()
    proposed = HealthcarePolicyFactory.create_usgha()

    time_series, summary_table, diff_table = compare_and_summarize([baseline, proposed], base_gdp=29e12, initial_debt=35e12, years=22, population=335e6, gdp_growth=0.025, start_year=2025)

    # Pick baseline/proposed by name
    baseline_df = time_series.get(baseline.policy_name)
    proposed_df = time_series.get(proposed.policy_name)

    # Build normalized per-capita timeseries
    from core.comparison import build_normalized_timeseries
    normalized_table = build_normalized_timeseries(time_series, population=335e6)

    # Use utils.io export (it accepts two DataFrames and a summary table). Include diffs and normalized.
    export_results_to_file(baseline_df, proposed_df, summary_table, output_path, diff_table=diff_table, normalized_table=normalized_table)
    print(f'Wrote comparison workbook to {os.path.abspath(output_path)}')


if __name__ == '__main__':
    run_and_export()
