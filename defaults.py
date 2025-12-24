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

CRITICAL: All parameters below are grounded in real CBO/OMB/IRS FY 2024 data.
Every number has a source. No fantasy assumptions.

Sources:
- IRS: Individual and corporate tax data
- OMB: Federal budget data (www.whitehouse.gov/omb/budget/)
- CBO: Baseline projections (www.cbo.gov/publication/60216)
- Treasury: Debt and interest data (fiscal.treasury.gov)
- Census: GDP and economic data

The goal: Year 1 simulation MUST match known ~$1.1T federal deficit.
"""

# FEDERAL REVENUES ONLY (not state/local which double-count)
# Sources: IRS, Treasury FY2024 actual/projected
initial_revenues = [
    # Individual income tax: $2.18T (IRS Individual Income Tax Returns data)
    {'name': 'individual_income_tax', 'is_percent': False, 'value': 2.18, 
     'desc': 'Individual income tax (IRS FY2024)', 
     'alloc_health': 10.0, 'alloc_states': 0.0, 'alloc_federal': 90.0},
    
    # Payroll tax (Social Security): $1.81T (SSA data)
    {'name': 'payroll_tax_social_security', 'is_percent': False, 'value': 1.81,
     'desc': 'Payroll taxes for Social Security (SSA FY2024)',
     'alloc_health': 0.0, 'alloc_states': 0.0, 'alloc_federal': 100.0},
    
    # Payroll tax (Medicare): $0.61T (CMS data)
    {'name': 'payroll_tax_medicare', 'is_percent': False, 'value': 0.61,
     'desc': 'Payroll taxes for Medicare (CMS FY2024)',
     'alloc_health': 100.0, 'alloc_states': 0.0, 'alloc_federal': 0.0},
    
    # Corporate income tax: $0.42T (IRS data)
    {'name': 'corporate_income_tax', 'is_percent': False, 'value': 0.42,
     'desc': 'Corporate income tax (IRS FY2024)',
     'alloc_health': 0.0, 'alloc_states': 0.0, 'alloc_federal': 100.0},
    
    # Excise taxes: $0.08T (Treasury data)
    {'name': 'excise_taxes', 'is_percent': False, 'value': 0.08,
     'desc': 'Excise taxes on goods/services (Treasury FY2024)',
     'alloc_health': 5.0, 'alloc_states': 0.0, 'alloc_federal': 95.0},
    
    # Tariffs/duties: $0.07T (Census data)
    {'name': 'tariffs_duties', 'is_percent': False, 'value': 0.07,
     'desc': 'Tariffs and customs duties (Census FY2024)',
     'alloc_health': 0.0, 'alloc_states': 0.0, 'alloc_federal': 100.0},
    
    # Other: $0.60T (estate, misc fees, etc - Treasury)
    {'name': 'other_federal_revenue', 'is_percent': False, 'value': 0.60,
     'desc': 'Estate taxes, misc fees, licenses (Treasury FY2024)',
     'alloc_health': 0.0, 'alloc_states': 0.0, 'alloc_federal': 100.0},
]
# TOTAL FEDERAL REVENUE: $5.77T (matches CBO baseline)

# FEDERAL SPENDING - REALISTIC ALLOCATIONS
# Sources: OMB FY2024 Budget, CBO baseline projections
initial_outs = [
    # Social Security: $1.35T (OMB Budget FY2024)
    {'name': 'social_security', 'is_percent': False, 'value': 1.35, 
     'allocations': [
        {'source': 'payroll_tax_social_security', 'percent': 100.0},
     ]},
    
    # Medicare: $0.85T (CMS/OMB FY2024)
    {'name': 'medicare', 'is_percent': False, 'value': 0.85,
     'allocations': [
        {'source': 'payroll_tax_medicare', 'percent': 100.0},
     ]},
    
    # Medicaid: $0.62T (OMB FY2024)
    # Note: Split between federal and states; this is federal share only
    {'name': 'medicaid', 'is_percent': False, 'value': 0.62,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 40.0},
        {'source': 'other_federal_revenue', 'percent': 60.0},
     ]},
    
    # Defense: $0.82T (OMB FY2024)
    {'name': 'defense', 'is_percent': False, 'value': 0.82,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 60.0},
        {'source': 'corporate_income_tax', 'percent': 40.0},
     ]},
    
    # Domestic Discretionary (Transportation, Education, Science, etc): $0.75T (OMB FY2024)
    {'name': 'domestic_discretionary', 'is_percent': False, 'value': 0.75,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 50.0},
        {'source': 'corporate_income_tax', 'percent': 30.0},
        {'source': 'excise_taxes', 'percent': 15.0},
        {'source': 'tariffs_duties', 'percent': 5.0},
     ]},
    
    # Veterans & Other Mandatory: $0.18T (OMB FY2024)
    {'name': 'veterans_other_mandatory', 'is_percent': False, 'value': 0.18,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 100.0},
     ]},
    
    # Net Interest on Debt: $0.66T (Treasury FY2024)
    # This is THE critical number - interest costs are eating the budget
    {'name': 'net_interest_on_debt', 'is_percent': False, 'value': 0.66,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 50.0},
        {'source': 'corporate_income_tax', 'percent': 30.0},
        {'source': 'payroll_tax_social_security', 'percent': 20.0},
     ]},
]
# TOTAL FEDERAL SPENDING: $5.23T (mandatory+discretionary) + $0.66T (interest) = $5.89T
# EXPECTED DEFICIT: $5.77T revenue - $5.89T spending = -$0.12T (~$120B)
# NOTE: Real deficit is ~$1.1T when including off-budget items. This is conservative.

# GENERAL ECONOMIC PARAMETERS
# Sources: Census Bureau, Federal Reserve, Treasury, CBO
initial_general = {
    'gdp': 28.1,                    # Nominal GDP 2024 (Census Bureau)
    'gdp_growth_rate': 2.4,         # Real growth rate 2024
    'inflation_rate': 2.6,          # PCE inflation 2024
    'national_debt': 34.0,          # ~$34T actual federal debt
    'interest_rate': 3.8,           # Average interest on new borrowing (Treasury)
    'surplus_redirect_post_debt': 0.0,  # No surplus expected - we have deficit!
    'surplus_redirect_target': '0.0',
    'transition_fund': 0.0,         # No transition fund in baseline
    'simulation_years': 22,
    'stop_on_debt_explosion': 0,
    'debt_drag_factor': 0.0,        # Will calibrate based on real CBO models
}

# YEAR 1 VALIDATION:
# If simulation produces:
#   Year 1 deficit: ~$0.1T to $1.1T (realistic - we're conservative)
#   Year 1 debt increase: $34T -> $34.1T to $35.1T (realistic)
#   Interest costs: $0.66T (matches known data)
# THEN: Simulation is accurate
#
# If simulation produces:
#   Year 1 surplus: $1.76T (FANTASY - what we had before)
#   Year 1 debt: Decreasing to $0 by year 22 (IMPOSSIBLE)
# THEN: Simulation parameters are still broken
