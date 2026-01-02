#!/usr/bin/env python
"""Test all dashboard imports"""

print('Starting imports...')

try:
    from core.social_security import SocialSecurityModel, SocialSecurityReforms
    print('✓ social_security')
except Exception as e:
    print(f'✗ social_security: {e}')
    
try:
    from core.revenue_modeling import FederalRevenueModel, TaxReforms
    print('✓ revenue_modeling')
except Exception as e:
    print(f'✗ revenue_modeling: {e}')
    
try:
    from core.medicare_medicaid import MedicareModel, MedicaidModel
    print('✓ medicare_medicaid')
except Exception as e:
    print(f'✗ medicare_medicaid: {e}')
    
try:
    from core.discretionary_spending import DiscretionarySpendingModel
    print('✓ discretionary_spending')
except Exception as e:
    print(f'✗ discretionary_spending: {e}')
    
try:
    from core.interest_spending import InterestOnDebtModel
    print('✓ interest_spending')
except Exception as e:
    print(f'✗ interest_spending: {e}')
    
try:
    from core.combined_outlook import CombinedFiscalOutlookModel
    print('✓ combined_outlook')
except Exception as e:
    print(f'✗ combined_outlook: {e}')
    
try:
    from core.healthcare import get_policy_by_type, PolicyType
    print('✓ healthcare')
except Exception as e:
    print(f'✗ healthcare: {e}')
    
try:
    from core.economic_engine import MonteCarloEngine, PolicyScenario, EconomicParameters
    print('✓ economic_engine')
except Exception as e:
    print(f'✗ economic_engine: {e}')
    
try:
    from core.data_loader import load_real_data
    print('✓ data_loader')
except Exception as e:
    print(f'✗ data_loader: {e}')
    
try:
    from core.policy_builder import PolicyTemplate, PolicyLibrary
    print('✓ policy_builder')
except Exception as e:
    print(f'✗ policy_builder: {e}')
    
try:
    from core.pdf_policy_parser import PolicyPDFProcessor
    print('✓ pdf_policy_parser')
except Exception as e:
    print(f'✗ pdf_policy_parser: {e}')
    
try:
    from core.policy_enhancements import PolicyRecommendationEngine
    print('✓ policy_enhancements')
except Exception as e:
    print(f'✗ policy_enhancements: {e}')
    
try:
    from core.monte_carlo_scenarios import MonteCarloPolicySimulator
    print('✓ monte_carlo_scenarios')
except Exception as e:
    print(f'✗ monte_carlo_scenarios: {e}')

print('All imports tested!')
