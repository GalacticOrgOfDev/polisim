import pandas as pd

df = pd.read_csv('usgha_simulation_22y.csv')

# Check revenue growth
print('Revenue Growth Analysis:')
print(f"Year 1 Revenue: ${df.iloc[0]['Revenue ($)']:,.0f}")
print(f"Year 2 Revenue: ${df.iloc[1]['Revenue ($)']:,.0f}")
print(f"Year 10 Revenue: ${df.iloc[9]['Revenue ($)']:,.0f}")
print(f"Year 22 Revenue: ${df.iloc[21]['Revenue ($)']:,.0f}")
print()
print('Percent Change:')
rev_y1 = df.iloc[0]['Revenue ($)']
rev_y22 = df.iloc[21]['Revenue ($)']
pct_change = (rev_y22 / rev_y1 - 1) * 100
print(f'Year 1 to Year 22: {pct_change:.1f}%')
print()

# Check if circuit breaker is being triggered
circuit_breaker_count = df['Circuit Breaker Triggered'].sum()
print(f'Circuit Breaker triggered: {circuit_breaker_count} times out of 22 years')
print()

# Check health spending vs revenue
print('Spending vs Revenue:')
print(f"Year 1: Health Spending ${df.iloc[0]['Health Spending ($)']/1e12:.2f}T, Revenue ${df.iloc[0]['Revenue ($)']/1e12:.2f}T")
print(f"Year 22: Health Spending ${df.iloc[21]['Health Spending ($)']/1e12:.2f}T, Revenue ${df.iloc[21]['Revenue ($)']/1e12:.2f}T")
print()

# Check surplus trend
print('Surplus Analysis:')
print(f"Year 1 Surplus: ${df.iloc[0]['Surplus ($)']/1e12:.2f}T")
print(f"Year 22 Surplus: ${df.iloc[21]['Surplus ($)']/1e12:.2f}T")
