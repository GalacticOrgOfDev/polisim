"""Load scenario JSON into a `HealthcarePolicyModel` instance.

This loader uses `HealthcarePolicyFactory.create_usgha()` as a conservative base
and applies overrides from the scenario file so the resulting object is
compatible with `simulate_healthcare_years`.
"""
import json
from typing import Any
from datetime import datetime

from core.healthcare import HealthcarePolicyFactory, HealthcarePolicyModel, TransitionTimeline
from core.policy_mechanics_extractor import PolicyMechanicsExtractor


def load_scenario(path: str) -> HealthcarePolicyModel:
    with open(path, 'r', encoding='utf-8') as f:
        scen = json.load(f)

    # Start from a baseline USGHA policy which includes full structure
    policy = HealthcarePolicyFactory.create_usgha()

    # Coverage
    cov = scen.get('coverage', {})
    if 'zero_out_of_pocket' in cov:
        policy.zero_out_of_pocket = bool(cov['zero_out_of_pocket'])
    if 'opt_out_voucher_system' in cov:
        # opt_out corresponds to opt_out_allowed
        policy.opt_out_allowed = bool(cov['opt_out_voucher_system'])

    # Targets: convert percent values (e.g., 7.0) to fraction (0.07)
    targets = scen.get('targets', {})
    if 'health_spending_percent_gdp' in targets and targets['health_spending_percent_gdp'] is not None:
        try:
            pct = float(targets['health_spending_percent_gdp'])
            # convert percent to decimal if >1
            if pct > 1:
                pct = pct / 100.0
            policy.healthcare_spending_target_gdp = pct
        except Exception:
            pass

    # Fiscal
    fiscal = scen.get('fiscal', {})
    # store target year as debt_elimination_year if present
    if fiscal.get('fiscal_surplus_target_year'):
        try:
            policy.debt_elimination_year = int(fiscal['fiscal_surplus_target_year'])
        except Exception:
            pass

    # Goals
    goals = scen.get('goals', {})
    if 'eliminate_medical_bankruptcy' in goals:
        # reflect as a target metric
        policy.target_metrics['medical_bankruptcy_cases'] = 0 if goals['eliminate_medical_bankruptcy'] else policy.target_metrics.get('medical_bankruptcy_cases', None)

    # Transition timeline: use provided years_mentioned or simulation settings
    years = scen.get('years_mentioned', [])
    sim_set = scen.get('simulation_settings', {})
    start_year = sim_set.get('start_year') or (min(years) if years else 2025)
    within = scen.get('targets', {}).get('target_within_years') or 2
    try:
        start_year = int(start_year)
    except Exception:
        start_year = 2025
    full_impl = start_year + int(within)

    policy.transition_timeline = TransitionTimeline(
        start_year=start_year,
        full_implementation_year=full_impl,
        sunset_year=None,
        key_milestones={},
        transition_funding_source=scen.get('source', '')
    )

    # Optional structured mechanics (context-aware simulation)
    mechanics_data = scen.get('structured_mechanics')
    if mechanics_data:
        try:
            policy.mechanics = PolicyMechanicsExtractor.mechanics_from_dict(
                mechanics_data,
                default_name=policy.policy_name,
                default_type="healthcare"
            )

            if policy.mechanics.target_spending_pct_gdp:
                policy.healthcare_spending_target_gdp = float(policy.mechanics.target_spending_pct_gdp) / 100.0
        except Exception:
            policy.mechanics = None

    # Attach excerpts to description for traceability
    excerpts = scen.get('excerpts')
    if excerpts:
        policy.description = (policy.description or '') + '\n\nScenario excerpts:\n' + json.dumps(excerpts, indent=2)

    # Return the policy model ready for simulation
    return policy
