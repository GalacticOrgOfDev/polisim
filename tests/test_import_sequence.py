#!/usr/bin/env python
"""Test imports sequentially to find hang"""

print('1. Basic imports')
import streamlit as st
import pandas as pd
import numpy as np
print('✓ Done')

print('2. Plotly')
import plotly.graph_objects as go
import plotly.express as px
print('✓ Done')

print('3. Pathlib and json')
from pathlib import Path
import json
print('✓ Done')

print('4. social_security')
from core.social_security import SocialSecurityModel
print('✓ Done')

print('5. revenue_modeling')
from core.revenue_modeling import FederalRevenueModel
print('✓ Done')

print('6. medicare_medicaid')
from core.medicare_medicaid import MedicareModel
print('✓ Done')

print('7. discretionary_spending')
from core.discretionary_spending import DiscretionarySpendingModel
print('✓ Done')

print('8. interest_spending')
from core.interest_spending import InterestOnDebtModel
print('✓ Done')

print('9. combined_outlook')
from core.combined_outlook import CombinedFiscalOutlookModel
print('✓ Done')

print('10. healthcare')
from core.healthcare import get_policy_by_type
print('✓ Done')

print('11. economic_engine')
from core.economic_engine import MonteCarloEngine
print('✓ Done')

print('12. data_loader')
from core.data_loader import load_real_data
print('✓ Done')

print('13. policy_builder')
from core.policy_builder import PolicyTemplate
print('✓ Done')

print('14. pdf_policy_parser')
from core.pdf_policy_parser import PolicyPDFProcessor
print('✓ Done')

print('15. policy_enhancements')
from core.policy_enhancements import PolicyRecommendationEngine
print('✓ Done')

print('16. monte_carlo_scenarios')
from core.monte_carlo_scenarios import MonteCarloPolicySimulator
print('✓ Done')

print('17. ui.auth')
from ui.auth import StreamlitAuth
print('✓ Done')

print('18. ui.themes')
from ui.themes import apply_theme
print('✓ Done')

print('19. ui.animations')
from ui.animations import apply_animation
print('✓ Done')

print('20. ui.tooltip_registry')
from ui.tooltip_registry import get_tooltip
print('✓ Done')

print('\n✅ All imports successful!')
