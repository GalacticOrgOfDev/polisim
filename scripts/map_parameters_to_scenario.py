"""Map extracted policy parameters into a simulator-ready scenario JSON.

Reads `policies/parameters.json` and writes `policies/galactic_health_scenario.json`.
This uses conservative defaults for ranges (takes midpoint) and produces fields
likely useful to a healthcare simulator: coverage rules, targets, timelines, funding.
"""
import os
import json
import statistics

ROOT = os.path.dirname(os.path.dirname(__file__))

PARAMS_PATH = os.path.join(ROOT, 'policies', 'parameters.json')
OUT_PATH = os.path.join(ROOT, 'policies', 'galactic_health_scenario.json')


def parse_percent_range(s: str):
    # Accept strings like '1–2' or '1-2' and return midpoint float
    if not s:
        return None
    s = s.replace('\u2013', '-').replace('\u2012', '-').replace('\u2014', '-')
    if '-' in s:
        parts = [p.strip() for p in s.split('-') if p.strip()]
        try:
            nums = [float(p) for p in parts]
            return statistics.mean(nums)
        except Exception:
            return None
    try:
        return float(s)
    except Exception:
        return None


def map_params_to_scenario(params: dict) -> dict:
    p = params.copy()
    scenario = {}

    # Basic identity
    scenario['policy_title'] = 'United States Galactic Health Act (extracted)'
    scenario['source'] = 'policies/parameters.json'

    # Coverage rules
    scenario['coverage'] = {
        'zero_out_of_pocket': bool(p.get('zero_out_of_pocket', False)),
        'opt_out_voucher_system': bool(p.get('opt_out_voucher_system', False)),
    }

    # Financial targets
    # target health spending percent of GDP
    health_pct = p.get('target_health_percent_gdp') or p.get('found_percent_of_gdp')
    if health_pct:
        scenario['targets'] = {
            'health_spending_percent_gdp': float(health_pct),
            'target_within_years': int(p.get('target_within_years', 20))
        }
    else:
        scenario['targets'] = {}

    # Fiscal surplus target (may be a range string)
    fiscal = p.get('fiscal_surplus_percent_gdp')
    fiscal_mid = parse_percent_range(str(fiscal)) if fiscal is not None else None
    scenario['fiscal'] = {
        'fiscal_surplus_percent_gdp': fiscal_mid,
        'fiscal_surplus_target_year': p.get('fiscal_surplus_target_year')
    }

    # Goals and flags
    scenario['goals'] = {
        'eliminate_medical_bankruptcy': bool(p.get('eliminate_medical_bankruptcy', False)),
        'establish_galactic_department_of_health': bool(p.get('establish_galactic_department_of_health', False)),
        'accelerate_biomedical_innovation': bool(p.get('accelerate_biomedical_innovation', False))
    }

    # Timeline hints
    scenario['years_mentioned'] = p.get('years_mentioned', [])

    # Attach excerpts for human review
    if 'excerpts' in p:
        scenario['excerpts'] = p['excerpts']

    # Default simulation knobs — these can be tuned later
    scenario['simulation_settings'] = {
        'start_year': min(scenario['years_mentioned']) if scenario['years_mentioned'] else 2025,
        'end_year': max(scenario['years_mentioned']) if scenario['years_mentioned'] else 2050,
        'annual_budget_adjustment_rate_pct': 0.5  # placeholder: percent change per year
    }

    return scenario


def main():
    if not os.path.exists(PARAMS_PATH):
        print('parameters.json not found. Run extractor first.')
        return
    with open(PARAMS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # pick the galactic health entry
    key = None
    for k in data.keys():
        if 'galactic health' in k.lower():
            key = k
            break
    if not key:
        key = next(iter(data.keys()))

    params = data[key]
    scenario = map_params_to_scenario(params)

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)

    print('Wrote scenario to', OUT_PATH)


if __name__ == '__main__':
    main()
