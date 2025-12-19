"""Run visualization pipeline: compare policies and produce chart PNGs."""
from core.healthcare import HealthcarePolicyFactory
from core.comparison import compare_and_summarize
from ui.healthcare_charts import build_all_charts
import os


def run_visualize(output_dir: str = 'reports/charts'):
    baseline = HealthcarePolicyFactory.create_current_us()
    proposed = HealthcarePolicyFactory.create_usgha()
    time_series, summary_table, diff_table = compare_and_summarize([baseline, proposed], base_gdp=29e12, initial_debt=35e12, years=22, population=335e6, gdp_growth=0.025, start_year=2025)

    mapping = build_all_charts(time_series, output_dir)
    print('Charts written:')
    for policy, files in mapping.items():
        print(f'  {policy}:')
        for k, v in files.items():
            print(f'    {k} -> {os.path.abspath(v)}')


if __name__ == '__main__':
    run_visualize()
