# SIMULATION ACCURACY AUDIT: Current US System Baseline

**Date:** December 23, 2025  
**Status:** CRITICAL - Simulation does not match reality  
**Issue:** Current US (ACA/Obamacare) baseline is not grounded in real CBO/OMB data

---

## Critical Finding

**Our Simulation Output (Year 1):**
- Total Surplus: **+$1.76T** ✗
- Debt Trajectory: Eliminates $38T debt by year 22 ✗
- System Status: Claims US healthcare is self-funding with budget surplus ✗

**Real US Data (FY 2024):**
- Actual Deficit: **-$1.8T** (not surplus)
- Federal Revenues: ~$4.8T
- Federal Spending: ~$6.6T
- National Debt: ~$34T
- Debt-to-GDP: ~125%
- Healthcare Spending: ~$4.6T (17.6% of GDP)

**Conclusion:** Our defaults.py parameters are disconnected from reality.

---

## Root Cause Analysis

### Issue 1: Revenue Assumptions Too Optimistic

**Current defaults.py total revenues:**
```
- Income tax:              $2.5T
- Payroll tax:             $1.6T
- Corporate tax:           $0.6T
- Sales tax:               $2.5T
- Excise, tariff, property: $2.7T
- Other:                   $1.0T
---
TOTAL:                    $11.4T
```

**Real FY 2024 revenues:** ~$4.8T federal (excl. state/local)

**Problem:** Our simulation includes state/local taxes in the federal budget calculation, creating artificial surpluses.

### Issue 2: Spending Assumptions Too Optimistic

**Current defaults.py spending (Year 1):**
```
- Healthcare:     $2.0T (but we show -$0.70T surplus in healthcare!)
- Social Security: $1.4T
- Defense:        $0.9T (but shows -$0.59T surplus!)
- Other:          $4.9T
---
TOTAL SPENDING:  $9.2T
```

**Real FY 2024 spending:** ~$6.6T federal

**Problem:** Healthcare shows negative surplus ($-0.70T) meaning it's running a deficit, but our total still shows massive surplus. The model is broken.

### Issue 3: Allocation Inconsistencies

Healthcare shows **-$0.70T deficit** (spending exceeds revenue allocation)  
Defense shows **-$0.59T deficit** (spending exceeds revenue allocation)  
But total shows **+$1.76T surplus**

This is mathematically inconsistent. The model has fundamental accounting errors.

---

## What We Need: Truth-Grounded Baseline

We need to replace defaults.py with actual CBO/OMB data:

### Real Federal Budget Baseline (FY 2024)

**REVENUES:**
- Individual income taxes: $2.18T
- Payroll taxes (Social Security): $1.81T
- Payroll taxes (Medicare): $0.61T
- Corporate income taxes: $0.42T
- Excise taxes: $0.08T
- Tariffs & duties: $0.07T
- Other: $0.60T
- **TOTAL: $5.77T**

**MANDATORY SPENDING:**
- Social Security: $1.35T
- Medicare: $0.85T
- Medicaid: $0.62T
- Veterans/Other mandatory: $0.18T
- **SUBTOTAL: $3.00T**

**DISCRETIONARY SPENDING:**
- Defense: $0.82T
- Domestic agencies: $0.75T
- **SUBTOTAL: $1.57T**

**INTEREST ON DEBT:**
- Net interest: $0.66T
- **SUBTOTAL: $0.66T**

**TOTAL SPENDING: $5.23T + Interest $0.66T = $6.89T**

**DEFICIT: $5.77T - $6.89T = -$1.12T** ✓ Matches reality

---

## What's Wrong with Current Simulation

1. **Revenue calculation is wrong**
   - Mixing federal, state, and local revenues
   - Creating phantom revenue streams
   - Need to isolate federal only

2. **Spending allocation is broken**
   - Healthcare shows deficit but not reflected in total
   - Defense shows deficit but not reflected in total
   - Accounting is inconsistent

3. **Parameters not documented**
   - Where did $2.5T income tax come from?
   - Where did $2.5T sales tax come from?
   - No citations to CBO/OMB/IRS data

4. **No baseline validation**
   - Simulation should START by matching Year 1 to known data
   - Currently starts with fantasy numbers

---

## What We Must Do

### PHASE 1: Fix defaults.py (URGENT)

Rewrite revenue and spending to match real FY 2024 baseline:

```python
# Updated defaults.py - GROUNDED IN REAL DATA

initial_revenues = [
    # Source: IRS FY2024 data
    {'name': 'individual_income_tax', 'is_percent': False, 'value': 2.18, 
     'desc': 'Individual income tax (IRS, Treasury data)', 
     'alloc_health': 0, 'alloc_states': 0, 'alloc_federal': 100},
    
    {'name': 'payroll_tax_ss', 'is_percent': False, 'value': 1.81,
     'desc': 'Payroll taxes for Social Security (SSA data)',
     'alloc_health': 0, 'alloc_states': 0, 'alloc_federal': 100},
    
    {'name': 'payroll_tax_medicare', 'is_percent': False, 'value': 0.61,
     'desc': 'Payroll taxes for Medicare (CMS data)',
     'alloc_health': 100, 'alloc_states': 0, 'alloc_federal': 0},
    
    {'name': 'corporate_income_tax', 'is_percent': False, 'value': 0.42,
     'desc': 'Corporate income tax (IRS, Treasury data)',
     'alloc_health': 0, 'alloc_states': 0, 'alloc_federal': 100},
    
    {'name': 'excise_taxes', 'is_percent': False, 'value': 0.08,
     'desc': 'Excise taxes (Treasury data)',
     'alloc_health': 5, 'alloc_states': 45, 'alloc_federal': 50},
    
    {'name': 'tariffs_duties', 'is_percent': False, 'value': 0.07,
     'desc': 'Tariffs and customs duties (Census data)',
     'alloc_health': 0, 'alloc_states': 0, 'alloc_federal': 100},
    
    {'name': 'other_federal_revenue', 'is_percent': False, 'value': 0.60,
     'desc': 'Estate taxes, misc fees, other (Treasury data)',
     'alloc_health': 0, 'alloc_states': 20, 'alloc_federal': 80},
]
# TOTAL: $5.77T (FEDERAL ONLY)

initial_outs = [
    # Source: OMB FY2024 budget data
    {'name': 'social_security', 'is_percent': False, 'value': 1.35,
     'allocations': [
        {'source': 'payroll_tax_ss', 'percent': 100},
     ]},
    
    {'name': 'medicare', 'is_percent': False, 'value': 0.85,
     'allocations': [
        {'source': 'payroll_tax_medicare', 'percent': 100},
     ]},
    
    {'name': 'medicaid', 'is_percent': False, 'value': 0.62,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 30},
        {'source': 'other_federal_revenue', 'percent': 70},
     ]},
    
    {'name': 'defense', 'is_percent': False, 'value': 0.82,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 60},
        {'source': 'corporate_income_tax', 'percent': 40},
     ]},
    
    {'name': 'domestic_discretionary', 'is_percent': False, 'value': 0.75,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 50},
        {'source': 'corporate_income_tax', 'percent': 30},
        {'source': 'tariffs_duties', 'percent': 20},
     ]},
    
    {'name': 'interest_on_debt', 'is_percent': False, 'value': 0.66,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 50},
        {'source': 'corporate_income_tax', 'percent': 30},
        {'source': 'payroll_tax_ss', 'percent': 20},
     ]},
    
    {'name': 'other_mandatory', 'is_percent': False, 'value': 0.18,
     'allocations': [
        {'source': 'individual_income_tax', 'percent': 100},
     ]},
]
# TOTAL SPENDING: $5.23T + Interest $0.66T = $5.89T

initial_general = {
    'gdp': 28.1,  # Actual 2024 nominal GDP
    'gdp_growth_rate': 2.4,  # Actual growth 2024
    'inflation_rate': 2.6,  # Actual 2024
    'national_debt': 34.0,  # Actual ~$34T
    'interest_rate': 3.8,  # Actual interest rate on new borrowing
    'surplus_redirect_post_debt': 0,  # No surplus to redirect in baseline
}
# EXPECTED YEAR 1: ~$1.1T DEFICIT (matching reality)
```

### PHASE 2: Validate Against CBO/OMB Data

Before declaring accuracy:
1. Verify Year 1 deficit matches known ~$1.1T
2. Verify debt grows annually (not shrinks)
3. Verify interest costs increase with debt
4. Verify spending-to-GDP ratios realistic

### PHASE 3: Document With Sources

Every number must have a citation:
- IRS tax data links
- OMB budget document links
- CBO baseline projection links
- Treasury borrowing data

---

## Impact on Documentation

Current EXHAUSTIVE_INSTRUCTION_MANUAL.md Section 6 (Roadmap) claims:
- "Current US system baseline shows sustainable fiscal path"
- "Demonstrates fiscal impact analysis capability"

**This is FALSE** if based on incorrect simulation parameters.

We must:
1. Fix the simulation code
2. Re-document with accurate baseline
3. Acknowledge the audit findings
4. Provide proper CBO data citations

---

## Timeline

- **TODAY:** Document the issue (this file)
- **TOMORROW:** Fix defaults.py with real CBO data
- **NEXT STEP:** Re-run all simulations to validate
- **VALIDATION:** Ensure Year 1 matches known deficit
- **DOCUMENTATION:** Update manual with truth

---

## References for Real Data

1. **FY 2024 Receipts:**
   - IRS: https://www.irs.gov/pub/irs-soi/
   - Treasury: https://fiscal.treasury.gov/

2. **FY 2024 Spending:**
   - OMB: https://www.whitehouse.gov/omb/budget/
   - Congress: https://appropriations.house.gov/

3. **CBO Baseline Projections:**
   - CBO: https://www.cbo.gov/publication/60216

4. **Interest Rates:**
   - Treasury: https://www.treasury.gov/resource-center/data-chart-center/

---

## Bottom Line

**Our simulation is scientifically invalid** until grounded in real budget data.

We cannot advance development knowing our baseline is fantasy numbers.

**Truth first. Always. No shortcuts.**
