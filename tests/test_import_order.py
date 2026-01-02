#!/usr/bin/env python
"""Test if core modules hang when imported BEFORE streamlit"""

print('1. All core modules (before streamlit)')
from core.social_security import SocialSecurityModel
from core.revenue_modeling import FederalRevenueModel
from core.medicare_medicaid import MedicareModel
from core.discretionary_spending import DiscretionarySpendingModel
from core.interest_spending import InterestOnDebtModel
from core.combined_outlook import CombinedFiscalOutlookModel
from core.healthcare import get_policy_by_type
from core.economic_engine import MonteCarloEngine
from core.data_loader import load_real_data
from core.policy_builder import PolicyTemplate
from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_enhancements import PolicyRecommendationEngine
from core.monte_carlo_scenarios import MonteCarloPolicySimulator
print('✓ All core modules loaded')

print('2. NOW importing streamlit')
import streamlit as st
print('✓ Streamlit loaded')

print('3. UI modules')
from ui.auth import StreamlitAuth
from ui.themes import apply_theme
from ui.animations import apply_animation
from ui.tooltip_registry import get_tooltip
print('✓ UI modules loaded')

print('\n✅ Success - imports work when core modules load first!')
