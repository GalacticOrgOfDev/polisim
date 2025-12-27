"""Run visualization pipeline: compare policies and produce chart PNGs."""
import os
import sys
from pathlib import Path
from typing import Optional, Union

# Ensure repo root on sys.path when running from scripts/
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.healthcare import HealthcarePolicyFactory
from core.comparison import compare_and_summarize
from ui.healthcare_charts import build_all_charts


def run_visualize(output_dir: Optional[Union[Path, str]] = None):
    output_dir = Path(output_dir) if output_dir is not None else REPO_ROOT / 'reports' / 'charts'
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = HealthcarePolicyFactory.create_current_us()
    proposed = HealthcarePolicyFactory.create_usgha()
    time_series, summary_table, diff_table = compare_and_summarize([baseline, proposed], base_gdp=29e12, initial_debt=35e12, years=22, population=335e6, gdp_growth=0.025, start_year=2025)

    mapping = build_all_charts(time_series, str(output_dir))
    print('Charts written:')
    for policy, files in mapping.items():
        print(f'  {policy}:')
        for k, v in files.items():
            print(f'    {k} -> {os.path.abspath(v)}')


if __name__ == '__main__':
    run_visualize()
