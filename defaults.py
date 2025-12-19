"""Default policies and scenario export helpers.

Provides convenience functions to write out JSON/YAML policy scenario files
based on the in-memory HealthcarePolicyModel factory methods.
"""
import json
import os
from typing import Dict
from core.healthcare import HealthcarePolicyFactory
import yaml


SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), 'scenarios')


def ensure_scenarios_dir():
    if not os.path.exists(SCENARIOS_DIR):
        os.makedirs(SCENARIOS_DIR, exist_ok=True)


def dump_policy_to_json(policy, filename: str):
    ensure_scenarios_dir()
    path = os.path.join(SCENARIOS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(policy.to_dict(), f, indent=2)
    return path


def dump_policy_to_yaml(policy, filename: str):
    ensure_scenarios_dir()
    path = os.path.join(SCENARIOS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump({'metadata': {'version': policy.policy_version, 'created_date': policy.created_date}, 'policy': policy.to_dict()}, f)
    return path


def create_default_scenarios():
    """Create scenario JSON and YAML files for quick testing and CI.

    Returns mapping of name->file_path.
    """
    mapping: Dict[str, str] = {}
    usgha = HealthcarePolicyFactory.create_usgha()
    mapping['usgha_json'] = dump_policy_to_json(usgha, 'usgha_baseline.json')
    mapping['usgha_yaml'] = dump_policy_to_yaml(usgha, 'usgha_baseline.yaml')

    current = HealthcarePolicyFactory.create_current_us()
    mapping['current_us_json'] = dump_policy_to_json(current, 'current_us_baseline.json')
    mapping['current_us_yaml'] = dump_policy_to_yaml(current, 'current_us_baseline.yaml')
    # Additional scenarios
    medicare = HealthcarePolicyFactory.create_medicare_for_all()
    mapping['medicare_json'] = dump_policy_to_json(medicare, 'medicare_for_all_baseline.json')
    mapping['medicare_yaml'] = dump_policy_to_yaml(medicare, 'medicare_for_all_baseline.yaml')

    uk = HealthcarePolicyFactory.create_uk_nhs()
    mapping['uk_json'] = dump_policy_to_json(uk, 'uk_nhs_baseline.json')
    mapping['uk_yaml'] = dump_policy_to_yaml(uk, 'uk_nhs_baseline.yaml')

    canada = HealthcarePolicyFactory.create_canada_single_payer()
    mapping['canada_json'] = dump_policy_to_json(canada, 'canada_single_payer_baseline.json')
    mapping['canada_yaml'] = dump_policy_to_yaml(canada, 'canada_single_payer_baseline.yaml')

    # Additional scenarios can be added as needed using factory methods
    return mapping


if __name__ == '__main__':
    print('Creating default scenario files...')
    m = create_default_scenarios()
    for k, v in m.items():
        print(f'Wrote {k} -> {v}')
"""Default parameter sets for the Economic Projector app.

These are imported by Economic_projector.py and can also be reused by
other modules as we continue refactoring.
"""

# Initial revenues based on 2025 projections - EXPANDED TO MATCH CSV - note: expand to match national budget, etc
# NOTE: alloc_health/states/federal MUST match the out allocations below for data consistency
initial_revenues = [
    {'name': 'income_tax', 'is_percent': False, 'value': 2.5, 'desc': 'Individual income tax revenue', 'alloc_health': 45.0, 'alloc_states': 27.5, 'alloc_federal': 27.5},
    {'name': 'payroll_tax', 'is_percent': False, 'value': 1.6, 'desc': 'Payroll taxes for Social Security and Medicare', 'alloc_health': 50.0, 'alloc_states': 25.0, 'alloc_federal': 25.0},
    {'name': 'corporate_tax', 'is_percent': False, 'value': 0.6, 'desc': 'Corporate income tax revenue', 'alloc_health': 10.0, 'alloc_states': 0.0, 'alloc_federal': 90.0},
    {'name': 'sales_tax', 'is_percent': False, 'value': 2.5, 'desc': 'Sales tax revenue (primarily state and local)', 'alloc_health': 16.0, 'alloc_states': 84.0, 'alloc_federal': 0.0},
    {'name': 'excise_tax', 'is_percent': False, 'value': 0.1, 'desc': 'Excise taxes on goods and services', 'alloc_health': 20.0, 'alloc_states': 40.0, 'alloc_federal': 40.0},
    {'name': 'tariff', 'is_percent': False, 'value': 0.1, 'desc': 'Tariff and customs duties revenue', 'alloc_health': 10.0, 'alloc_states': 0.0, 'alloc_federal': 90.0},
    {'name': 'property_tax', 'is_percent': False, 'value': 1.0, 'desc': 'Property tax revenue (local and state)', 'alloc_health': 5.0, 'alloc_states': 42.75, 'alloc_federal': 52.25},
    {'name': 'estate_gift_tax', 'is_percent': False, 'value': 0.03, 'desc': 'Estate and gift taxes', 'alloc_health': 24.0, 'alloc_states': 43.24, 'alloc_federal': 32.76},
    {'name': 'other_taxes', 'is_percent': False, 'value': 1.2, 'desc': 'Other taxes and fees', 'alloc_health': 24.0, 'alloc_states': 43.24, 'alloc_federal': 32.76},
    {'name': 'ineligible_contributions', 'is_percent': False, 'value': 0.7, 'desc': 'Ineligible contributions', 'alloc_health': 100.0, 'alloc_states': 0.0, 'alloc_federal': 0.0},
    {'name': 'illegal_contributions', 'is_percent': False, 'value': 0.03, 'desc': 'Illegal contributions', 'alloc_health': 100.0, 'alloc_states': 0.0, 'alloc_federal': 0.0},
]

# Initial out categories - EXPANDED TO MATCH CSV
# Defaults are balanced so that total allocations from each revenue source sum to 100%
initial_outs = [
    {'name': 'healthcare_social', 'is_percent': False, 'value': 2.0, 'allocations': [
        {'source': 'income_tax', 'percent': 33.0},
        {'source': 'sales_tax', 'percent': 10.0},
        {'source': 'tariff', 'percent': 5.0},
        {'source': 'property_tax', 'percent': 5.0},
        {'source': 'other_taxes', 'percent': 15.0},
        {'source': 'estate_gift_tax', 'percent': 100.0},
    ]},
    {'name': 'social_security', 'is_percent': False, 'value': 1.4, 'allocations': [
        {'source': 'payroll_tax', 'percent': 80.0},
        {'source': 'income_tax', 'percent': 10.0},
    ]},
    {'name': 'states_local_aid', 'is_percent': False, 'value': 1.0, 'allocations': [
        {'source': 'income_tax', 'percent': 22.0},
        {'source': 'sales_tax', 'percent': 70.0},
        {'source': 'property_tax', 'percent': 40.0},
        {'source': 'other_taxes', 'percent': 35.0},
    ]},
    {'name': 'federal_operations', 'is_percent': False, 'value': 1.2, 'allocations': [
        {'source': 'income_tax', 'percent': 35.0},
        {'source': 'tariff', 'percent': 85.0},
        {'source': 'property_tax', 'percent': 50.0},
        {'source': 'other_taxes', 'percent': 35.0},
    ]},
    {'name': 'defense', 'is_percent': False, 'value': 0.9, 'allocations': [
        {'source': 'corporate_tax', 'percent': 46.0},
        {'source': 'tariff', 'percent': 10.0},
        {'source': 'excise_tax', 'percent': 60.0},
    ]},
    {'name': 'interest_debt', 'is_percent': False, 'value': 0.9, 'allocations': [
        {'source': 'payroll_tax', 'percent': 20.0},
        {'source': 'income_tax', 'percent': 0.0},
        {'source': 'corporate_tax', 'percent': 54.0},
    ]},
    {'name': 'education', 'is_percent': False, 'value': 0.7, 'allocations': [
        {'source': 'sales_tax', 'percent': 20.0},
        {'source': 'property_tax', 'percent': 5.0},
    ]},
    {'name': 'other_spending', 'is_percent': False, 'value': 0.5, 'allocations': [
        {'source': 'other_taxes', 'percent': 15.0},
        {'source': 'excise_tax', 'percent': 40.0},
        {'source': 'ineligible_contributions', 'percent': 100.0},
        {'source': 'illegal_contributions', 'percent': 100.0},
    ]},
]

# General parameters - UPDATED TO MATCH CSV
initial_general = {
    'gdp': 30.5,
    'gdp_growth_rate': 2.8,  # %
    'inflation_rate': 3.0,  # %
    'national_debt': 38.0,
    'interest_rate': 4.0,  # %
    'surplus_redirect_post_debt': 10.0,  # %
    'surplus_redirect_target': '0.0',  # 0.0 = no redirect (surplus stays as surplus)
    'transition_fund': 0.1,
    'simulation_years': 20,
    'stop_on_debt_explosion': 0,  # P1: 1=stop simulation if debt/GDP > 1000%, 0=continue with warning
    'debt_drag_factor': 0.0,  # P1: GDP growth reduction per 10% debt/GDP increase (e.g., 0.1 = -0.1% growth per 10% debt/GDP)
}

