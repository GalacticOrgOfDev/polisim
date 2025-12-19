import pytest
from core import get_policy_by_type, PolicyType, simulate_healthcare_years
import pandas as pd


def test_simulate_healthcare_basic():
    policy = get_policy_by_type(PolicyType.USGHA)
    df = simulate_healthcare_years(policy, base_gdp=29e12, initial_debt=35e12, years=5, population=335e6, gdp_growth=0.02, start_year=2027)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    # Columns we expect
    expected = ['Year', 'GDP', 'Health Spending ($)', 'Health % GDP', 'Per Capita Health ($)', 'Revenue ($)', 'Surplus ($)', 'Remaining Debt ($)']
    for col in expected:
        assert col in df.columns
    # No NaNs in critical columns
    assert df['Health Spending ($)'].notna().all()
    assert df['Revenue ($)'].notna().all()


def test_simulate_healthcare_high_debt_edge_case():
    policy = get_policy_by_type(PolicyType.USGHA)
    # Very high initial debt to force deficit behavior
    df = simulate_healthcare_years(policy, base_gdp=1e12, initial_debt=100e12, years=3, population=1e6, gdp_growth=0.0, start_year=2027)
    # Should return DataFrame and debt should remain finite
    assert isinstance(df, pd.DataFrame)
    assert df['Remaining Debt ($)'].apply(lambda x: x >= 0).all()

if __name__ == '__main__':
    pytest.main([__file__])
