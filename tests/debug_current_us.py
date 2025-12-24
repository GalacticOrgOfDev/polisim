#!/usr/bin/env python
"""Debug script to test Current US system simulation for accuracy."""

from defaults import initial_general, initial_revenues, initial_outs
from core.simulation import simulate_years

# Run simulation with current defaults
results = simulate_years(initial_general, initial_revenues, initial_outs)
if results is not None and not results.empty:
    print('Current US System - First 5 years:')
    print(results[['Year', 'GDP', 'Total Surplus', 'Remaining Debt']].head())
    print(f'\nYear 1 Details:')
    y1 = results.iloc[0]
    for key in y1.index:
        if 'Surplus' in key or 'Revenue' in key:
            print(f'  {key}: ${y1[key]:.2f}T')
    
    print(f'\nYear 22 Summary:')
    year22 = results.iloc[-1]
    print(f'  GDP: ${year22["GDP"]:.2f}T')
    print(f'  Total Surplus: ${year22["Total Surplus"]:.2f}T')
    print(f'  Remaining Debt: ${year22["Remaining Debt"]:.2f}T')
    print(f'  Debt-to-GDP: {(year22["Remaining Debt"]/year22["GDP"])*100:.1f}%')
    
    # Check if it's showing unrealistic surpluses
    print(f'\nAnalysis:')
    avg_surplus = results['Total Surplus'].mean()
    print(f'  Average Annual Surplus: ${avg_surplus:.2f}T')
    print(f'  Debt Trend: Started at ${initial_general["national_debt"]:.2f}T, ended at ${year22["Remaining Debt"]:.2f}T')
    
    if year22["Total Surplus"] > 0:
        print('\n⚠️  CRITICAL ISSUE: Current US system showing SURPLUS!')
        print('    Real US Data (2024):')
        print('    - Actual deficit: ~$1.8T')
        print('    - Federal revenues: ~$4.8T')
        print('    - Federal spending: ~$6.6T')
        print('    - Debt-to-GDP: ~125%')
        print('\n    Our simulation shows unrealistic SURPLUS because:')
        print('    - Revenue assumptions are TOO HIGH')
        print('    - Spending assumptions are TOO LOW')
        print('    - Parameters not grounded in real CBO/OMB data')
    else:
        print(f'  ✓ Current US system showing deficit (realistic)')
else:
    print('ERROR: Simulation failed')
