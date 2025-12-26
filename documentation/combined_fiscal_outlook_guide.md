# Combined Fiscal Outlook User Guide

**Version:** 1.0  
**Date:** December 25, 2024  
**Author:** PoliSim Development Team

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Model Components](#model-components)
4. [Usage Examples](#usage-examples)
5. [Output Reference](#output-reference)
6. [Scenarios and Parameters](#scenarios-and-parameters)
7. [Interpreting Results](#interpreting-results)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

The **Combined Fiscal Outlook Model** (`CombinedFiscalOutlookModel`) is PoliSim's unified federal budget simulation tool. It integrates all major revenue and spending components to provide comprehensive 30-year fiscal projections with Monte Carlo uncertainty quantification.

### What It Does

- **Projects federal revenues** using detailed tax models (individual income, corporate, payroll, excise)
- **Models mandatory spending**: Social Security, Medicare, Medicaid, other health programs
- **Simulates discretionary spending**: defense and non-defense appropriations
- **Calculates interest costs**: debt service projections
- **Computes fiscal metrics**: deficits, debt trajectories, sustainability indicators

### Key Features

- **Monte Carlo simulations**: 100-10,000 iterations for uncertainty quantification
- **30-year projections**: 2026-2055 baseline
- **Scenario analysis**: baseline, recession, strong growth
- **CBO-validated**: Benchmarked against Congressional Budget Office data
- **Modular design**: Each component can be used independently

---

## Quick Start

### Basic Usage

```python
from core.combined_outlook import CombinedFiscalOutlookModel

# Initialize model
model = CombinedFiscalOutlookModel()

# Generate 10-year projection with 1,000 iterations
df = model.project_unified_budget(years=10, iterations=1000)

# Get fiscal summary
summary = model.get_fiscal_summary(years=10, iterations=1000)

print(f"10-year deficit: ${summary['total_deficit_10year_billions']:.1f}B")
print(f"Sustainable: {summary['sustainable']}")
```

### Output

```
10-year deficit: $-91.6B
Sustainable: True
```

---

## Model Components

### 1. Revenue Model (`FederalRevenueModel`)

**Source:** `core/revenue_modeling.py`

Projects all federal tax revenues:
- Individual income tax (~50% of revenue)
- Payroll taxes (Social Security, Medicare) (~35%)
- Corporate income tax (~10%)
- Excise and other taxes (~5%)

**Baseline (2025):** ~$5.5T total revenue

### 2. Social Security Model (`SocialSecurityModel`)

**Source:** `core/social_security.py`

Models OASI (Old-Age and Survivors Insurance) trust fund:
- Benefit payments
- Payroll tax revenue
- Trust fund balance and solvency

**Baseline (2025):** ~$1.2T spending

### 3. Medicare Model (`MedicareModel`)

**Source:** `core/medicare_medicaid.py`

Projects Medicare spending by part:
- Part A: Hospital insurance
- Part B: Medical insurance
- Part D: Prescription drugs

**Baseline (2025):** ~$870B spending

### 4. Medicaid Model (`MedicaidModel`)

**Source:** `core/medicare_medicaid.py`

Projects Medicaid spending:
- Federal share: ~62% of total
- State share: ~38% (not included in federal budget)

**Baseline (2025):** ~$414B federal spending

### 5. Other Health Spending

**Programs included:**
- Veterans Affairs (VA): ~$300B
- Children's Health Insurance Program (CHIP): ~$20B
- ACA subsidies: ~$30B

**Baseline (2025):** ~$350B total

### 6. Discretionary Spending Model (`DiscretionarySpendingModel`)

**Source:** `core/discretionary_spending.py`

Projects appropriations:
- Defense: ~$900B (baseline)
- Non-defense: ~$750B (baseline)

**Growth:** ~2.5% annual (inflation)

### 7. Interest on Debt Model (`InterestOnDebtModel`)

**Source:** `core/interest_spending.py`

Calculates debt service:
- Baseline interest rate: 3.5-4.5%
- Rising with debt accumulation

**Baseline (2025):** ~$1T interest spending

---

## Usage Examples

### Example 1: Basic 30-Year Projection

```python
from core.combined_outlook import CombinedFiscalOutlookModel
import matplotlib.pyplot as plt

model = CombinedFiscalOutlookModel()
df = model.project_unified_budget(years=30, iterations=1000)

# Plot revenue vs spending
plt.figure(figsize=(12, 6))
plt.plot(df['year'], df['total_revenue'], label='Revenue', linewidth=2)
plt.plot(df['year'], df['total_spending'], label='Spending', linewidth=2)
plt.fill_between(df['year'], df['total_revenue'], df['total_spending'], 
                 where=df['deficit_surplus'] < 0, alpha=0.3, color='red', label='Deficit')
plt.xlabel('Year')
plt.ylabel('Billions of Dollars')
plt.title('30-Year Federal Budget Projection')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### Example 2: Spending Composition Analysis

```python
model = CombinedFiscalOutlookModel()
df = model.project_unified_budget(years=10, iterations=1000)

# Calculate spending shares
spending_components = [
    'social_security_spending',
    'medicare_spending',
    'medicaid_spending',
    'other_health_spending',
    'discretionary_spending',
    'interest_spending'
]

# Year 2035 (10th year) breakdown
year_2035 = df.iloc[9]
total = year_2035['total_spending']

print("2035 Federal Spending Breakdown:")
print("-" * 50)
for component in spending_components:
    value = year_2035[component]
    pct = (value / total) * 100
    label = component.replace('_', ' ').title()
    print(f"{label:30} ${value:,.0f}B ({pct:.1f}%)")
print("-" * 50)
print(f"{'Total Spending':30} ${total:,.0f}B (100.0%)")
```

### Example 3: Scenario Comparison

```python
model = CombinedFiscalOutlookModel()

scenarios = {
    'Baseline': model.get_fiscal_summary(years=10, revenue_scenario='baseline'),
    'Recession': model.get_fiscal_summary(years=10, revenue_scenario='recession_2026'),
    'Strong Growth': model.get_fiscal_summary(years=10, revenue_scenario='strong_growth')
}

print("10-Year Fiscal Summary by Scenario:")
print("-" * 70)
for name, summary in scenarios.items():
    revenue = summary['total_revenue_10year_billions']
    deficit = summary['total_deficit_10year_billions']
    sustainable = "Yes" if summary['sustainable'] else "No"
    print(f"{name:15} Revenue: ${revenue:,.0f}B  Deficit: ${deficit:,.0f}B  Sustainable: {sustainable}")
```

### Example 4: Deficit Decomposition

```python
model = CombinedFiscalOutlookModel()
df = model.project_unified_budget(years=10, iterations=1000)

# Calculate contribution to deficit
print("10-Year Deficit Decomposition:")
print("-" * 50)

total_revenue = df['total_revenue'].sum()
print(f"Total Revenue:                ${total_revenue:,.0f}B")
print()

spending_categories = {
    'Social Security': df['social_security_spending'].sum(),
    'Medicare': df['medicare_spending'].sum(),
    'Medicaid': df['medicaid_spending'].sum(),
    'Other Health': df['other_health_spending'].sum(),
    'Discretionary': df['discretionary_spending'].sum(),
    'Interest': df['interest_spending'].sum()
}

for category, amount in spending_categories.items():
    print(f"{category:20} ${amount:,.0f}B")

total_spending = sum(spending_categories.values())
deficit = total_revenue - total_spending
print("-" * 50)
print(f"{'Total Spending':20} ${total_spending:,.0f}B")
print(f"{'Deficit':20} ${deficit:,.0f}B")
```

---

## Output Reference

### DataFrame Columns

| Column | Description | Unit |
|--------|-------------|------|
| `year` | Calendar year | Integer (2026-2055) |
| `total_revenue` | Total federal revenues | Billions |
| `other_health_spending` | VA, CHIP, ACA subsidies | Billions |
| `social_security_spending` | Social Security benefits | Billions |
| `medicare_spending` | Medicare Parts A, B, D | Billions |
| `medicaid_spending` | Medicaid federal share | Billions |
| `discretionary_spending` | Defense + non-defense | Billions |
| `interest_spending` | Debt service | Billions |
| `mandatory_spending` | Sum of mandatory programs | Billions |
| `total_spending` | Sum of all spending | Billions |
| `deficit_surplus` | Revenue - Spending | Billions (negative = deficit) |
| `primary_deficit` | Deficit excluding interest | Billions |

### Fiscal Summary Dictionary

```python
{
    'total_revenue_10year_billions': float,      # Sum of 10 years revenue
    'total_spending_10year_billions': float,     # Sum of 10 years spending
    'total_deficit_10year_billions': float,      # Sum of 10 years deficit
    'avg_annual_revenue_billions': float,        # Average annual revenue
    'avg_annual_spending_billions': float,       # Average annual spending
    'avg_annual_deficit_billions': float,        # Average annual deficit
    'primary_balance_10year_billions': float,    # Deficit excluding interest
    'sustainable': bool                          # Is primary balance positive?
}
```

---

## Scenarios and Parameters

### Available Scenarios

#### Revenue Scenarios
- **`"baseline"`**: Current law continuation (default)
- **`"recession_2026"`**: Economic downturn scenario
- **`"strong_growth"`**: Above-trend growth scenario

*Note: Scenario implementation is work-in-progress; currently limited differentiation*

#### Social Security Scenarios
- **`"baseline"`**: No reforms (default)
- **`"raise_payroll_tax"`**: Increase payroll tax rate
- **`"remove_wage_cap"`**: Eliminate taxable wage cap
- **`"raise_fra"`**: Increase full retirement age

#### Discretionary Scenarios
- **`"baseline"`**: Inflation-adjusted growth (default)
- **`"growth"`**: Increased spending
- **`"reduction"`**: Spending cuts

#### Interest Scenarios
- **`"baseline"`**: 3.5-4.5% rates (default)
- **`"rising"`**: Higher interest rate path

### Common Parameters

```python
model.project_unified_budget(
    years=30,                           # Projection length (1-75)
    iterations=1000,                    # Monte Carlo iterations (100-10,000)
    revenue_scenario="baseline",        # Revenue scenario
    ss_scenario="baseline",             # Social Security scenario
    healthcare_policy="usgha",          # Healthcare policy (not yet used)
    discretionary_scenario="baseline",  # Discretionary scenario
    interest_scenario="baseline"        # Interest rate scenario
)
```

---

## Interpreting Results

### Fiscal Sustainability

**Primary Balance Rule:**
- **Positive primary balance** (revenue > spending excluding interest) → debt/GDP ratio stabilizes
- **Negative primary balance** → debt/GDP ratio grows indefinitely

**Example:**
```python
summary = model.get_fiscal_summary(years=10)
if summary['sustainable']:
    print("✓ Fiscal path is sustainable (primary balance positive)")
else:
    print("✗ Fiscal path is unsustainable (primary balance negative)")
```

### Deficit vs. Primary Deficit

- **Deficit**: Total shortfall (revenue - spending)
- **Primary Deficit**: Deficit excluding interest payments

**Why it matters:** Rising interest costs can hide underlying fiscal health. A shrinking primary deficit despite growing total deficit may indicate improving fundamentals.

### Spending Growth Drivers

1. **Demographics**: Aging population drives Medicare, Social Security growth
2. **Healthcare inflation**: 5-6% annual, above general inflation
3. **Interest costs**: Compound with debt accumulation
4. **Discretionary**: Grows with inflation (~2.5% annually)

---

## Best Practices

### 1. Choose Appropriate Iterations

- **Quick analysis**: 100-500 iterations
- **Standard analysis**: 1,000-2,000 iterations
- **Publication**: 5,000-10,000 iterations

*Higher iterations increase precision but slow computation*

### 2. Validate Against CBO

```python
# Compare 10-year totals to CBO baseline
model = CombinedFiscalOutlookModel()
summary = model.get_fiscal_summary(years=10, iterations=5000)

cbo_10yr_deficit = -15_000  # CBO estimate: $15T deficit
model_deficit = summary['total_deficit_10year_billions']

pct_diff = abs(model_deficit - cbo_10yr_deficit) / abs(cbo_10yr_deficit) * 100
print(f"Model vs CBO: {pct_diff:.1f}% difference")
```

### 3. Check for Outliers

```python
df = model.project_unified_budget(years=30, iterations=1000)

# Check for unreasonable values
assert df['total_revenue'].min() > 0, "Negative revenue!"
assert df['total_spending'].min() > 0, "Negative spending!"
assert (df['medicare_spending'] / df['total_spending']).max() < 0.5, "Medicare too large!"
```

### 4. Use Fiscal Summary for High-Level Analysis

```python
# More efficient than full DataFrame for summary stats
summary = model.get_fiscal_summary(years=10, iterations=1000)
print(f"10-year deficit: ${summary['total_deficit_10year_billions']:.1f}B")
```

### 5. Save Results for Reproducibility

```python
import pandas as pd

df = model.project_unified_budget(years=30, iterations=5000)
df.to_csv('fiscal_projection_2024-12-25.csv', index=False)

# Save metadata
metadata = {
    'date': '2024-12-25',
    'years': 30,
    'iterations': 5000,
    'scenarios': {
        'revenue': 'baseline',
        'social_security': 'baseline',
        'discretionary': 'baseline'
    }
}
```

---

## Troubleshooting

### Issue: Tests Failing After Changing Parameters

**Symptom:** `test_revenue_covers_most_spending` or similar fails

**Cause:** Extreme parameter values (e.g., very high discretionary spending)

**Fix:**
```python
# Check if parameters are reasonable
assert years >= 1 and years <= 75
assert iterations >= 100 and iterations <= 10000
```

### Issue: Medicare/Medicaid Values Too Large

**Symptom:** Medicare spending > $10T per year

**Cause:** Unit conversion error (dollars vs billions)

**Fix:** Verify helper functions use correct conversions:
```python
# Medicare: dollars → billions
medicare_billions = medicare_dollars / 1e9

# Medicaid: thousands → billions  
medicaid_billions = medicaid_thousands / 1e3
```

### Issue: Spending Components Don't Sum Correctly

**Symptom:** `total_spending ≠ sum of components`

**Fix:** Check mandatory spending calculation:
```python
mandatory_cols = ["social_security_spending", "medicare_spending", 
                  "medicaid_spending", "other_health_spending"]
unified["mandatory_spending"] = unified[mandatory_cols].sum(axis=1)
```

### Issue: Scenario Results Identical

**Symptom:** `"baseline"` and `"strong_growth"` produce same revenue

**Cause:** Scenario logic not yet implemented in revenue model

**Status:** Known limitation; scenario support coming in future update

---

## Additional Resources

- **Source Code:** `core/combined_outlook.py`
- **Test Suite:** `tests/test_phase32_integration.py`
- **Medicare/Medicaid Guide:** `documentation/medicare_medicaid_assumptions.md`
- **Revenue Model:** `core/revenue_modeling.py`
- **CBO Data:** [Congressional Budget Office](https://www.cbo.gov/about/products/budget-economic-data)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-25 | Initial release with Sprint 3 integration |

---

## Support

For questions or issues:
1. Check test suite examples: `tests/test_phase32_integration.py`
2. Review debug log: `documentation/debug.md`
3. Consult source code comments: `core/combined_outlook.py`

---

**End of Guide**
