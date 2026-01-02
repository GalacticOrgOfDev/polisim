#!/usr/bin/env python3
"""
Test unified policy extraction across all domains.
"""

from core.policy_mechanics_extractor import extract_policy_mechanics, PolicyMechanics

# Test 1: Healthcare policy
healthcare_text = """
United States Galactic Health Act
Section 1: Purpose
This Act establishes universal healthcare coverage for all residents.

Section 6: Funding
A combined payroll tax of 15% shall be implemented to fund this system.
The tax will be phased in over 4 years beginning in 2027.

Section 11: Surplus Allocation
30% reserve, 40% debt reduction, 20% infrastructure, 10% dividends
"""

print("=" * 60)
print("TEST 1: Healthcare Policy Extraction")
print("=" * 60)
hc_mechanics = extract_policy_mechanics(healthcare_text, policy_type="combined")
print(f"Policy Type: {hc_mechanics.policy_type}")
print(f"Funding Mechanisms: {len(hc_mechanics.funding_mechanisms)}")
print(f"Has Tax Mechanics: {hc_mechanics.tax_mechanics is not None}")
print(f"Has SS Mechanics: {hc_mechanics.social_security_mechanics is not None}")
print(f"Has Spending Mechanics: {hc_mechanics.spending_mechanics is not None}")
if hc_mechanics.funding_mechanisms:
    print(f"First mechanism: {hc_mechanics.funding_mechanisms[0].source_type} - {hc_mechanics.funding_mechanisms[0].percentage_rate}%")

# Test 2: Tax policy
tax_text = """
Comprehensive Tax Reform Act
This bill implements multiple tax reforms including:
- A wealth tax of 2% on net worth above $50 million
- A consumption/VAT tax of 10% with exemptions for food and medicine
- A carbon tax of $50 per ton of CO2
- These measures are expected to raise $300 billion annually
"""

print("\n" + "=" * 60)
print("TEST 2: Tax Policy Extraction")
print("=" * 60)
tax_mechanics = extract_policy_mechanics(tax_text, policy_type="combined")
print(f"Policy Type: {tax_mechanics.policy_type}")
print(f"Has Healthcare Mechanics: {len(tax_mechanics.funding_mechanisms) > 0}")
print(f"Has Tax Mechanics: {tax_mechanics.tax_mechanics is not None}")
if tax_mechanics.tax_mechanics:
    print(f"  Wealth Tax Rate: {tax_mechanics.tax_mechanics.wealth_tax_rate}")
    print(f"  Consumption Tax Rate: {tax_mechanics.tax_mechanics.consumption_tax_rate}")
    print(f"  Carbon Tax: ${tax_mechanics.tax_mechanics.carbon_tax_per_ton}/ton")
    print(f"  Tax Revenue: ${tax_mechanics.tax_mechanics.tax_revenue_billions}B")

# Test 3: Social Security policy
ss_text = """
Social Security Reform Act
Section 1: Payroll Tax Changes
The payroll tax rate shall increase to 13% to address trust fund solvency.
The payroll tax cap shall be removed to increase coverage.

Section 2: Benefit Formula
The full retirement age shall be increased to 69.
COLA adjustments shall be calculated using chained CPI.

Section 3: Solvency
These changes ensure trust fund solvency through 2085.
"""

print("\n" + "=" * 60)
print("TEST 3: Social Security Policy Extraction")
print("=" * 60)
ss_mechanics = extract_policy_mechanics(ss_text, policy_type="combined")
print(f"Policy Type: {ss_mechanics.policy_type}")
print(f"Has Social Security Mechanics: {ss_mechanics.social_security_mechanics is not None}")
if ss_mechanics.social_security_mechanics:
    print(f"  Payroll Tax Rate: {ss_mechanics.social_security_mechanics.payroll_tax_rate}")
    print(f"  Tax Cap Change: {ss_mechanics.social_security_mechanics.payroll_tax_cap_change}")
    print(f"  Full Retirement Age: {ss_mechanics.social_security_mechanics.full_retirement_age}")
    print(f"  COLA Method: {ss_mechanics.social_security_mechanics.cola_adjustments}")
    print(f"  Solvency Year: {ss_mechanics.social_security_mechanics.trust_fund_solvency_year}")

# Test 4: Spending policy
spending_text = """
National Infrastructure and Defense Spending Act
Section 1: Defense Budget
The defense budget shall be increased by 2% annually.

Section 2: Infrastructure Investment
$200 billion shall be invested in infrastructure improvements.
$100 billion shall be allocated to education and research.

Section 3: Budget Caps
Annual spending caps shall be set at $2.5 trillion total.
"""

print("\n" + "=" * 60)
print("TEST 4: Spending Policy Extraction")
print("=" * 60)
spending_mechanics = extract_policy_mechanics(spending_text, policy_type="combined")
print(f"Policy Type: {spending_mechanics.policy_type}")
print(f"Has Spending Mechanics: {spending_mechanics.spending_mechanics is not None}")
if spending_mechanics.spending_mechanics:
    print(f"  Defense Spending Change: {spending_mechanics.spending_mechanics.defense_spending_change}%")
    print(f"  Infrastructure Spending: ${spending_mechanics.spending_mechanics.infrastructure_spending}B")
    print(f"  Education Spending: ${spending_mechanics.spending_mechanics.education_spending}B")
    print(f"  Budget Caps Enabled: {spending_mechanics.spending_mechanics.budget_caps_enabled}")

# Test 5: Combined policy
combined_text = """
Comprehensive Economic Reform Act 2026

This bill addresses healthcare, taxation, social security, and spending:

HEALTHCARE REFORMS:
- Universal coverage for all residents
- Zero out-of-pocket costs
- Funded by a 12% payroll tax

TAX REFORMS:
- Wealth tax of 3% on net worth above $100 million
- Carbon tax of $75 per ton
- Expected revenue of $150 billion

SOCIAL SECURITY:
- Increase payroll tax to 12.4%
- Raise full retirement age to 68
- Enable means testing above $150,000 income

SPENDING REFORMS:
- $300 billion infrastructure investment
- $50 billion education funding increase
- 1% annual defense spending growth
"""

print("\n" + "=" * 60)
print("TEST 5: Combined Policy Extraction")
print("=" * 60)
combined_mechanics = extract_policy_mechanics(combined_text, policy_type="combined")
print(f"Policy Type: {combined_mechanics.policy_type}")
print(f"Detected Fields:")
print(f"  Healthcare Mechanics: {len(combined_mechanics.funding_mechanisms) > 0}")
print(f"  Tax Mechanics: {combined_mechanics.tax_mechanics is not None}")
print(f"  SS Mechanics: {combined_mechanics.social_security_mechanics is not None}")
print(f"  Spending Mechanics: {combined_mechanics.spending_mechanics is not None}")
print(f"Confidence Score: {combined_mechanics.confidence_score:.2f}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
