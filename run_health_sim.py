"""Simple runner for healthcare simulation.

Usage (PowerShell):
    cd "e:\AI Projects\polisim"
    python run_health_sim.py [--scenario path/to/scenario.json]

If `--scenario` is provided, the scenario will be loaded and used in place
of the built-in USGHA policy.
"""
import os
import argparse
from core import get_policy_by_type, PolicyType, simulate_healthcare_years


parser = argparse.ArgumentParser(description='Run healthcare simulation')
parser.add_argument('--scenario', help='Path to scenario JSON to load', default=None)
parser.add_argument('--years', type=int, default=22, help='Number of years to simulate')
parser.add_argument('--start-year', type=int, default=2027, help='Calendar start year')
args = parser.parse_args()

if args.scenario:
    from core.scenario_loader import load_scenario
    print(f'Loading scenario from {args.scenario}...')
    policy = load_scenario(args.scenario)
else:
    policy = get_policy_by_type(PolicyType.USGHA)

base_gdp = 29e12
initial_debt = 35e12

print('Running simulation...')
df = simulate_healthcare_years(policy, base_gdp=base_gdp, initial_debt=initial_debt, years=args.years, population=335e6, gdp_growth=0.025, start_year=args.start_year)

out = os.path.join(os.getcwd(), 'usgha_simulation_22y.csv')
df.to_csv(out, index=False)
print(f'Wrote CSV to {out}')
