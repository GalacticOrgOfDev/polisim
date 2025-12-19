"""One-click report generator: Excel workbook, PNGs, HTML interactive charts, Markdown summary, and ZIP package."""
import os
import zipfile
from core.healthcare import HealthcarePolicyFactory
from core.comparison import compare_and_summarize, build_normalized_timeseries
from ui.healthcare_charts import build_all_charts
from utils.io import export_results_to_file
import pandas as pd


def generate_markdown_summary(summary_table: pd.DataFrame, diff_table: pd.DataFrame, out_path: str):
    lines = []
    lines.append('# Policy Comparison Summary')
    if not summary_table.empty:
        lines.append('\n## Summary Table\n')
        lines.append(summary_table.to_markdown(index=False))
    if diff_table is not None and not diff_table.empty:
        lines.append('\n## Differences vs Baseline\n')
        lines.append(diff_table.to_markdown(index=False))

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(lines))
    return out_path


def run_report(output_dir: str = 'reports/package'):
    os.makedirs(output_dir, exist_ok=True)
    baseline = HealthcarePolicyFactory.create_current_us()
    proposed = HealthcarePolicyFactory.create_usgha()

    time_series, summary_table, diff_table = compare_and_summarize([baseline, proposed], base_gdp=29e12, initial_debt=35e12, years=22, population=335e6, gdp_growth=0.025, start_year=2025)

    # Normalized table
    normalized_table = build_normalized_timeseries(time_series, population=335e6)

    # Export Excel workbook
    xlsx_path = os.path.join(output_dir, 'policy_comparison.xlsx')
    export_results_to_file(time_series.get(baseline.policy_name), time_series.get(proposed.policy_name), summary_table, xlsx_path, diff_table=diff_table, normalized_table=normalized_table)

    # Generate charts (PNG + HTML)
    charts_dir = os.path.join(output_dir, 'charts')
    charts_map = build_all_charts(time_series, charts_dir)

    # Generate markdown summary
    md_path = os.path.join(output_dir, 'summary.md')
    generate_markdown_summary(summary_table, diff_table, md_path)

    # Package into zip
    zip_path = os.path.join(output_dir, 'policy_report.zip')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Add workbook
        zf.write(xlsx_path, arcname=os.path.basename(xlsx_path))
        # Add markdown
        zf.write(md_path, arcname=os.path.basename(md_path))
        # Add charts
        for policy, files in charts_map.items():
            for name, p in files.items():
                if os.path.exists(p):
                    zf.write(p, arcname=os.path.join('charts', os.path.relpath(p, charts_dir)))

    print(f'Wrote report package to {os.path.abspath(zip_path)}')
    return zip_path


if __name__ == '__main__':
    run_report()
