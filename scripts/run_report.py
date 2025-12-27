"""One-click report generator: Excel workbook, PNGs, HTML interactive charts, Markdown summary, and ZIP package."""
# mypy: ignore-errors
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional, Union

# Ensure repo root on sys.path when running from scripts/
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.healthcare import HealthcarePolicyFactory
from core.comparison import compare_and_summarize, build_normalized_timeseries
from ui.healthcare_charts import build_all_charts
from utils.io import export_results_to_file
import pandas as pd  # type: ignore[import-untyped]


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


def run_report(output_dir: Optional[Union[Path, str]] = None):
    output_dir = Path(output_dir) if output_dir is not None else REPO_ROOT / 'reports' / 'package'
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = HealthcarePolicyFactory.create_current_us()
    proposed = HealthcarePolicyFactory.create_usgha()

    time_series, summary_table, diff_table = compare_and_summarize([baseline, proposed], base_gdp=29e12, initial_debt=35e12, years=22, population=335e6, gdp_growth=0.025, start_year=2025)

    # Normalized table
    normalized_table = build_normalized_timeseries(time_series, population=335e6)

    # Export Excel workbook
    xlsx_path = output_dir / 'policy_comparison.xlsx'
    export_results_to_file(time_series.get(baseline.policy_name), time_series.get(proposed.policy_name), summary_table, str(xlsx_path), diff_table=diff_table, normalized_table=normalized_table)

    # Generate charts (PNG + HTML)
    charts_dir = output_dir / 'charts'
    charts_map = build_all_charts(time_series, str(charts_dir))

    # Generate markdown summary
    md_path = output_dir / 'summary.md'
    generate_markdown_summary(summary_table, diff_table, str(md_path))

    # Package into zip
    zip_path = output_dir / 'policy_report.zip'
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
