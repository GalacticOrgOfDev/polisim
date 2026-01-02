#!/usr/bin/env python
"""Test dashboard imports in exact order"""

import sys

print('1. streamlit and pandas')
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json
print('✓ Done')

print('2. core.social_security')
from core.social_security import SocialSecurityModel, SocialSecurityReforms, TrustFundAssumptions, BenefitFormula
print('✓ Done')

print('3. core.revenue_modeling')
from core.revenue_modeling import FederalRevenueModel, TaxReforms
print('✓ Done')

print('4. core.medicare_medicaid')
from core.medicare_medicaid import MedicareModel, MedicaidModel
print('✓ Done')

print('5. core.discretionary_spending')
from core.discretionary_spending import DiscretionarySpendingModel
print('✓ Done')

print('6. core.interest_spending')
from core.interest_spending import InterestOnDebtModel
print('✓ Done')

print('7. core.combined_outlook')
from core.combined_outlook import CombinedFiscalOutlookModel
print('✓ Done')

print('8. core.healthcare')
from core.healthcare import get_policy_by_type, PolicyType
print('✓ Done')

print('9. core.economic_engine')
from core.economic_engine import MonteCarloEngine, PolicyScenario, EconomicParameters
print('✓ Done')

print('10. core.data_loader')
from core.data_loader import load_real_data
print('✓ Done')

print('11. core.policy_builder')
from core.policy_builder import PolicyTemplate, PolicyLibrary
print('✓ Done')

print('12. core.pdf_policy_parser')
from core.pdf_policy_parser import PolicyPDFProcessor
print('✓ Done')

print('13. core.policy_enhancements')
from core.policy_enhancements import (
    PolicyRecommendationEngine,
    InteractiveScenarioExplorer,
    PolicyImpactCalculator,
)
print('✓ Done')

print('14. core.monte_carlo_scenarios')
from core.monte_carlo_scenarios import (
    MonteCarloPolicySimulator,
    PolicySensitivityAnalyzer,
    StressTestAnalyzer,
)
print('✓ Done')

print('15. ui.auth')
from ui.auth import StreamlitAuth, show_user_profile_page
print('✓ Done')

print('16. ui.themes')
from ui.themes import apply_theme, get_theme_list, preview_theme, customize_theme_colors, apply_plotly_theme
print('✓ Done')

print('17. ui.animations')
from ui.animations import apply_animation
print('✓ Done')

print('18. ui.tooltip_registry')
from ui.tooltip_registry import get_tooltip as registry_get_tooltip
print('✓ Done')

print('\n✅ All imports successful!')
