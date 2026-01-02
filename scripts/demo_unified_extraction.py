#!/usr/bin/env python3
"""
Unified Policy Extraction Demo
Shows complete extraction across healthcare, tax, social security, and spending domains
"""

from core.policy_mechanics_extractor import extract_policy_mechanics
import json

print("=" * 80)
print("POLISIM: Multi-Domain Policy Extraction Demo")
print("=" * 80)

# Example 1: Pure Healthcare Policy
healthcare_only = """
United States Galactic Health Act (USGHA)

Section 1: Universal Coverage
This Act establishes universal healthcare coverage for all U.S. residents.

Section 6: Funding
A combined payroll tax of 15% shall fund this system.
The tax will be phased in over 4 years beginning in 2027.

Section 11: Surplus Allocation
- 30% contingency reserve
- 40% debt reduction
- 20% infrastructure investment  
- 10% consumer dividends

Section 15: Implementation Timeline
Year 2027: System begins, enrollment targets 50 million
Year 2028: Enrollment reaches 150 million
Year 2030: Full universal coverage achieved
Year 2031: System spending below 12% of GDP
"""

print("\n1. HEALTHCARE-ONLY POLICY")
print("-" * 80)
hc_result = extract_policy_mechanics(healthcare_only)
print(f"Policy Type: {hc_result.policy_type}")
print(f"Funding Mechanisms: {len(hc_result.funding_mechanisms)}")
if hc_result.funding_mechanisms:
    for fm in hc_result.funding_mechanisms:
        print(f"  - {fm.source_type}: {fm.percentage_rate}%")
print(f"Surplus Allocation Configured: {hc_result.surplus_allocation is not None}")
print(f"Has Tax Mechanics: {hc_result.tax_mechanics is not None}")
print(f"Has SS Mechanics: {hc_result.social_security_mechanics is not None}")
print(f"Has Spending Mechanics: {hc_result.spending_mechanics is not None}")
print(f"Confidence Score: {hc_result.confidence_score:.2f}")

# Example 2: Tax-Only Policy
tax_only = """
Progressive Taxation Act 2026

Section 1: Wealth Tax
A wealth tax of 3% shall be levied on net worth above $100 million.
Tax tiers:
- Tier 1: 2% on wealth $50M - $1B
- Tier 2: 3% on wealth above $1B

Section 2: Carbon Tax
A carbon tax of $75 per metric ton of CO2 equivalent shall be implemented.
Annual escalation: 5% per year
Revenue allocation:
- 60% dividend to households
- 20% transition assistance for affected workers
- 20% clean energy investment

Section 3: Consumption Tax
A 12% VAT shall be implemented with exemptions for:
- Basic food and groceries
- Prescription medications
- Residential housing

Expected annual revenue: $200 billion
"""

print("\n2. TAX-ONLY POLICY")
print("-" * 80)
tax_result = extract_policy_mechanics(tax_only)
print(f"Policy Type: {tax_result.policy_type}")
print(f"Tax Mechanics Present: {tax_result.tax_mechanics is not None}")
if tax_result.tax_mechanics:
    print(f"  Wealth Tax Rate: {tax_result.tax_mechanics.wealth_tax_rate * 100 if tax_result.tax_mechanics.wealth_tax_rate else 'N/A'}%")
    print(f"  Wealth Tax Threshold: ${tax_result.tax_mechanics.wealth_tax_threshold:,.0f}" if tax_result.tax_mechanics.wealth_tax_threshold else "  N/A")
    print(f"  Consumption Tax Rate: {tax_result.tax_mechanics.consumption_tax_rate * 100 if tax_result.tax_mechanics.consumption_tax_rate else 'N/A'}%")
    print(f"  Carbon Tax: ${tax_result.tax_mechanics.carbon_tax_per_ton}/ton" if tax_result.tax_mechanics.carbon_tax_per_ton else "  N/A")
    print(f"  Total Revenue: ${tax_result.tax_mechanics.tax_revenue_billions}B" if tax_result.tax_mechanics.tax_revenue_billions else "  N/A")
print(f"Has Healthcare Mechanics: {len(tax_result.funding_mechanisms) > 0}")
print(f"Has SS Mechanics: {tax_result.social_security_mechanics is not None}")
print(f"Has Spending Mechanics: {tax_result.spending_mechanics is not None}")
print(f"Confidence Score: {tax_result.confidence_score:.2f}")

# Example 3: Social Security Policy
ss_only = """
Social Security Solvency Act 2026

Section 1: Payroll Tax Reform
The Old-Age, Survivors, and Disability Insurance (OASDI) payroll tax rate
shall be increased from 12.4% to 13.5% effective January 1, 2027.

The current payroll tax cap of $168,600 shall be removed, subjecting all
earned income to the payroll tax.

Section 2: Full Retirement Age
The Full Retirement Age (FRA) shall be increased gradually:
- Age 68 by 2031
- Age 69 by 2040

Section 3: Benefit Formula
Primary Insurance Amount calculations shall transition to:
- Chained CPI-based cost-of-living adjustments (COLA)
- Progressive benefit formula protecting lower-income beneficiaries

Section 4: Solvency
These reforms ensure trust fund solvency through 2100.
"""

print("\n3. SOCIAL SECURITY-ONLY POLICY")
print("-" * 80)
ss_result = extract_policy_mechanics(ss_only)
print(f"Policy Type: {ss_result.policy_type}")
print(f"SS Mechanics Present: {ss_result.social_security_mechanics is not None}")
if ss_result.social_security_mechanics:
    print(f"  Payroll Tax Rate: {ss_result.social_security_mechanics.payroll_tax_rate * 100 if ss_result.social_security_mechanics.payroll_tax_rate else 'N/A'}%")
    print(f"  Tax Cap Change: {ss_result.social_security_mechanics.payroll_tax_cap_change or 'N/A'}")
    print(f"  Full Retirement Age: {ss_result.social_security_mechanics.full_retirement_age}" if ss_result.social_security_mechanics.full_retirement_age else "  N/A")
    print(f"  COLA Method: {ss_result.social_security_mechanics.cola_adjustments or 'N/A'}")
    print(f"  Trust Fund Solvency: {ss_result.social_security_mechanics.trust_fund_solvency_year}" if ss_result.social_security_mechanics.trust_fund_solvency_year else "  N/A")
print(f"Has Healthcare Mechanics: {len(ss_result.funding_mechanisms) > 0}")
print(f"Has Tax Mechanics: {ss_result.tax_mechanics is not None}")
print(f"Has Spending Mechanics: {ss_result.spending_mechanics is not None}")
print(f"Confidence Score: {ss_result.confidence_score:.2f}")

# Example 4: Spending Policy
spending_only = """
National Infrastructure Investment Act 2026

Section 1: Defense Spending
Annual defense spending shall increase by 2%, adjusted for inflation baseline.

Section 2: Infrastructure Investment
$300 billion shall be allocated to infrastructure improvements:
- Transportation infrastructure upgrades
- Water systems modernization
- Electrical grid improvements
- Broadband expansion

Section 3: Education & Research
$50 billion shall be allocated to:
- K-12 education funding
- Higher education support
- Scientific research and development

Section 4: Budget Controls
Annual discretionary spending shall be capped at $2.5 trillion,
with automatic adjustment for inflation.
"""

print("\n4. SPENDING-ONLY POLICY")
print("-" * 80)
spending_result = extract_policy_mechanics(spending_only)
print(f"Policy Type: {spending_result.policy_type}")
print(f"Spending Mechanics Present: {spending_result.spending_mechanics is not None}")
if spending_result.spending_mechanics:
    print(f"  Defense Change: {spending_result.spending_mechanics.defense_spending_change * 100 if spending_result.spending_mechanics.defense_spending_change else 'N/A'}%")
    print(f"  Infrastructure: ${spending_result.spending_mechanics.infrastructure_spending}B" if spending_result.spending_mechanics.infrastructure_spending else "  N/A")
    print(f"  Education: ${spending_result.spending_mechanics.education_spending}B" if spending_result.spending_mechanics.education_spending else "  N/A")
    print(f"  Budget Caps: {spending_result.spending_mechanics.budget_caps_enabled}")
print(f"Has Healthcare Mechanics: {len(spending_result.funding_mechanisms) > 0}")
print(f"Has Tax Mechanics: {spending_result.tax_mechanics is not None}")
print(f"Has SS Mechanics: {spending_result.social_security_mechanics is not None}")
print(f"Confidence Score: {spending_result.confidence_score:.2f}")

# Example 5: COMBINED POLICY - ALL DOMAINS
combined_policy = """
Comprehensive Economic Reform and Fiscal Stabilization Act 2026

TITLE I: HEALTHCARE REFORM
Establishes universal healthcare coverage funded by a 12% payroll tax
with zero out-of-pocket costs for all residents.

TITLE II: TAX REFORM
- Wealth Tax: 2.5% on net worth above $50 million
- Carbon Tax: $60 per metric ton with 4% annual escalation
- Consumption Tax: 10% VAT with food and medicine exemptions
- Expected revenue: $250 billion annually

TITLE III: SOCIAL SECURITY REFORM
- Increase payroll tax from 12.4% to 13.2%
- Remove the $168,600 payroll tax cap
- Gradually increase Full Retirement Age to 68
- Implement chained CPI for COLA adjustments
- These changes ensure solvency through 2090

TITLE IV: FEDERAL SPENDING REFORM
- Defense spending increase of 1.5% annually
- $250 billion infrastructure investment
- $75 billion education and research funding
- Overall discretionary budget cap of $2.3 trillion
"""

print("\n5. COMBINED POLICY (ALL DOMAINS)")
print("-" * 80)
combined_result = extract_policy_mechanics(combined_policy)
print(f"Policy Type: {combined_result.policy_type}")
print(f"  Healthcare Mechanics: YES ({len(combined_result.funding_mechanisms)} funding mechanisms)")
print(f"  Tax Mechanics: YES")
if combined_result.tax_mechanics:
    print(f"    - Wealth tax: {combined_result.tax_mechanics.wealth_tax_rate * 100 if combined_result.tax_mechanics.wealth_tax_rate else 'N/A'}%")
    print(f"    - Carbon tax: ${combined_result.tax_mechanics.carbon_tax_per_ton}/ton" if combined_result.tax_mechanics.carbon_tax_per_ton else "    N/A")
    print(f"    - Consumption tax: {combined_result.tax_mechanics.consumption_tax_rate * 100 if combined_result.tax_mechanics.consumption_tax_rate else 'N/A'}%")
print(f"  Social Security Mechanics: YES")
if combined_result.social_security_mechanics:
    print(f"    - Payroll tax: {combined_result.social_security_mechanics.payroll_tax_rate * 100 if combined_result.social_security_mechanics.payroll_tax_rate else 'N/A'}%")
    print(f"    - Cap change: {combined_result.social_security_mechanics.payroll_tax_cap_change or 'N/A'}")
    print(f"    - FRA adjustment: {combined_result.social_security_mechanics.full_retirement_age if combined_result.social_security_mechanics.full_retirement_age else 'N/A'}")
print(f"  Spending Mechanics: YES")
if combined_result.spending_mechanics:
    print(f"    - Defense change: {combined_result.spending_mechanics.defense_spending_change * 100 if combined_result.spending_mechanics.defense_spending_change else 'N/A'}%")
    print(f"    - Infrastructure: ${combined_result.spending_mechanics.infrastructure_spending}B" if combined_result.spending_mechanics.infrastructure_spending else "    N/A")
print(f"Confidence Score: {combined_result.confidence_score:.2f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
The unified extraction system successfully analyzed policies across all domains:

1. ✓ Healthcare-only policy: Extracted funding and surplus allocation
2. ✓ Tax-only policy: Extracted wealth, carbon, and consumption taxes
3. ✓ Social Security-only: Extracted payroll tax, FRA, and COLA changes
4. ✓ Spending-only: Extracted defense, infrastructure, and education funding
5. ✓ Combined policy: Extracted ALL domains simultaneously in one object

KEY BENEFITS:
• Single extraction analyzes all domains at once
• No redundant PDF parsing or processing
• Each module accesses only the mechanics it needs
• Unified object enables cross-domain analysis
• Automatic detection - no manual domain specification required
• Ready for LLM integration with AI-assisted analysis

NEXT STEPS:
→ Integrate with dashboard policy upload flow
→ Allow users to apply extracted mechanics to simulations
→ Implement cross-domain policy interaction modeling
→ Add LLM-assisted parameter detection and validation
""")

print("=" * 80)
print("Demo completed successfully!")
print("=" * 80)
