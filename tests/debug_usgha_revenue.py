#!/usr/bin/env python3
"""Debug USGHA revenue calculation."""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pdf_policy_parser import PolicyPDFProcessor
from core.policy_mechanics_extractor import extract_policy_mechanics, PolicyMechanicsExtractor
from core import simulate_healthcare_years
from core.scenario_loader import load_scenario

# Load USGHA
usgha_path = Path("project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf")
processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(usgha_path)

print("=" * 80)
print("USGHA REVENUE DEBUGGING")
print("=" * 80)

# Test 1: Standard extraction
print("\n1. STANDARD EXTRACTION")
print("-" * 80)
standard_mechs = PolicyMechanicsExtractor.extract_generic_healthcare_mechanics(text, "USGHA")
print(f"Mechanisms found: {len(standard_mechs.funding_mechanisms)}")
total_gdp_pct = sum(m.percentage_gdp or 0 for m in standard_mechs.funding_mechanisms)
print(f"Total revenue: {total_gdp_pct:.2f}% GDP")

# Test 2: Context-aware extraction  
print("\n2. CONTEXT-AWARE EXTRACTION")
print("-" * 80)
context_mechs = extract_policy_mechanics(text, policy_type="healthcare")
print(f"Mechanisms found: {len(context_mechs.funding_mechanisms)}")
total_gdp_pct = sum(m.percentage_gdp or 0 for m in context_mechs.funding_mechanisms)
print(f"Total revenue: {total_gdp_pct:.2f}% GDP")

# Test 3: Scenario loader
print("\n3. SCENARIO LOADER")
print("-" * 80)
try:
    policy = load_scenario("policies/galactic_health_scenario.json")
    print(f"Policy type: {policy.policy_type}")
    if hasattr(policy, 'mechanics') and policy.mechanics:
        print(f"Has mechanics: Yes")
        print(f"Mechanisms: {len(policy.mechanics.funding_mechanisms)}")
        total_gdp_pct = sum(m.percentage_gdp or 0 for m in policy.mechanics.funding_mechanisms)
        print(f"Total revenue: {total_gdp_pct:.2f}% GDP")
    else:
        print(f"Has mechanics: No (using legacy attributes)")
except Exception as e:
    print(f"Error loading scenario: {e}")

# Test 4: Run short simulation
print("\n4. SIMULATION TEST (First 3 Years)")
print("-" * 80)
df = simulate_healthcare_years(
    policy=standard_mechs,
    base_gdp=29e12,
    initial_debt=35e12,
    years=3,
    population=335e6,
    gdp_growth=0.025,
    start_year=2025
)

print(f"\n{'Year':<6} {'GDP':<8} {'Revenue':<8} {'Spending':<8} {'Surplus':<8} {'Debt':<8}")
print("-" * 60)
for _, row in df.iterrows():
    year = int(row['Year'])
    gdp = row['GDP'] / 1e12
    revenue = row['Total Revenue'] / 1e12
    spending = row['Healthcare Spending'] / 1e12
    surplus = row['Surplus/Deficit'] / 1e12
    debt = row['National Debt'] / 1e12
    print(f"{year:<6} ${gdp:<7.1f}T ${revenue:<7.1f}T ${spending:<7.1f}T ${surplus:+<7.1f}T ${debt:<7.1f}T")

print("\n" + "=" * 80)
