import pandas as pd
from core.healthcare import HealthcarePolicyFactory
from core.comparison import compare_and_summarize


def test_compare_and_summarize_basic():
    baseline = HealthcarePolicyFactory.create_current_us()
    proposed = HealthcarePolicyFactory.create_usgha()
    time_series, summary_table, diff_table = compare_and_summarize([baseline, proposed], base_gdp=29e12, initial_debt=35e12, years=5, population=335e6, gdp_growth=0.02, start_year=2027)
    assert isinstance(time_series, dict)
    assert baseline.policy_name in time_series
    assert proposed.policy_name in time_series
    assert isinstance(summary_table, pd.DataFrame)
    assert summary_table.shape[0] == 2
    # diff_table should have one row (proposed vs baseline)
    assert isinstance(diff_table, pd.DataFrame)
    assert diff_table.shape[0] == 1


if __name__ == '__main__':
    test_compare_and_summarize_basic()
