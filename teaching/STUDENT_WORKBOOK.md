# PoliSim Student Workbook

**Hands-On Federal Fiscal Policy Analysis**

---

## Welcome, Student! 🎓

This workbook accompanies the PoliSim Jupyter notebook curriculum. Use it to:
- Take notes during lessons
- Complete exercises
- Track your progress
- Reflect on what you've learned

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Module 1: Budget Fundamentals](#module-1-budget-fundamentals)
3. [Module 2: Healthcare Policy](#module-2-healthcare-policy)
4. [Module 3: Social Security](#module-3-social-security)
5. [Module 4: Uncertainty & Monte Carlo](#module-4-uncertainty--monte-carlo)
6. [Module 5: Tax Policy](#module-5-tax-policy)
7. [Module 6: Advanced Topics](#module-6-advanced-topics)
8. [Capstone Project Guide](#capstone-project-guide)
9. [Glossary Quick Reference](#glossary-quick-reference)
10. [Self-Assessment Checklists](#self-assessment-checklists)

---

## Getting Started

### Your Learning Path

Check off as you complete each notebook:

- [ ] **01** - Welcome to PoliSim (15-20 min)
- [ ] **02** - Federal Budget Basics (30-40 min)
- [ ] **03** - Healthcare Policy Analysis (45-60 min)
- [ ] **04** - Social Security Deep Dive (45-60 min)
- [ ] **05** - Monte Carlo & Uncertainty (60-90 min)
- [ ] **06** - Tax Policy Modeling (45-60 min)
- [ ] **07** - Policy Extraction (30-45 min)
- [ ] **08** - API Integration (30-45 min)
- [ ] **09** - Custom Policy Design (60-90 min)
- [ ] **10** - Capstone Analysis (2-3 hours)

### Setup Checklist

Before starting, ensure you have:

- [ ] Python 3.9+ installed
- [ ] PoliSim repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Jupyter notebook working
- [ ] First notebook (01) opens successfully

---

## Module 1: Budget Fundamentals

**Notebooks**: 01, 02

### Learning Objectives

By completing this module, you will:
- [ ] Explain the components of federal revenue
- [ ] Identify major spending categories
- [ ] Distinguish between deficit and debt
- [ ] Interpret debt-to-GDP ratios
- [ ] Run a basic PoliSim simulation

### Key Concepts

**Revenue Sources** (fill in as you learn):

| Source | % of Total | Description |
|--------|------------|-------------|
| Individual Income Tax | ____% | |
| Payroll Taxes | ____% | |
| Corporate Income Tax | ____% | |
| Other | ____% | |

**Spending Categories** (fill in):

| Category | % of Total | Description |
|----------|------------|-------------|
| Social Security | ____% | |
| Healthcare (Medicare/Medicaid) | ____% | |
| Defense | ____% | |
| Interest on Debt | ____% | |
| Other Discretionary | ____% | |

### Exercise 1.1: Budget Breakdown

After running Notebook 02, answer:

1. What is the current approximate federal revenue? $_____T

2. What is the current approximate federal spending? $_____T

3. What is the current annual deficit? $_____B

4. What is the current debt-to-GDP ratio? _____%

5. According to the baseline projection, what will the debt be in 10 years? $_____T

### Exercise 1.2: Interpretation

Write 2-3 sentences explaining why the debt-to-GDP ratio is more meaningful than raw debt numbers:

```
________________________________________________________________

________________________________________________________________

________________________________________________________________
```

### Reflection Questions

1. What aspect of the federal budget surprised you most?

```
________________________________________________________________

________________________________________________________________
```

2. Why do projections become more uncertain further into the future?

```
________________________________________________________________

________________________________________________________________
```

---

## Module 2: Healthcare Policy

**Notebook**: 03

### Learning Objectives

- [ ] Compare different healthcare policy models
- [ ] Understand coverage vs. cost trade-offs
- [ ] Analyze 30-year fiscal impacts
- [ ] Evaluate political feasibility factors

### Healthcare Policy Comparison Matrix

Fill in as you analyze each policy in Notebook 03:

| Policy | 30-Year Cost | Coverage | Key Mechanism |
|--------|--------------|----------|---------------|
| Current Law | $____T | ____M | |
| ACA Expansion | $____T | ____M | |
| Public Option | $____T | ____M | |
| Medicare for All | $____T | ____M | |

### Exercise 2.1: Policy Trade-offs

For each policy, identify the primary trade-off:

**Medicare for All:**
- Pro: ____________________________________________
- Con: ____________________________________________

**Public Option:**
- Pro: ____________________________________________
- Con: ____________________________________________

**Status Quo:**
- Pro: ____________________________________________
- Con: ____________________________________________

### Exercise 2.2: Critical Analysis

Why might actual costs differ from projected costs? List 3 factors:

1. ________________________________________________

2. ________________________________________________

3. ________________________________________________

---

## Module 3: Social Security

**Notebook**: 04

### Learning Objectives

- [ ] Explain trust fund mechanics
- [ ] Understand demographic pressures
- [ ] Analyze reform scenarios
- [ ] Project solvency timelines

### Key Numbers

Fill in from Notebook 04:

| Metric | Current | Projected (2035) |
|--------|---------|------------------|
| Trust Fund Balance | $____T | $____T |
| Worker-to-Beneficiary Ratio | ____:1 | ____:1 |
| Average Benefit | $____/month | $____/month |
| Full Retirement Age | ____ | ____ |

**Projected Trust Fund Depletion Year**: ________

### Exercise 3.1: Reform Options

For each reform option, calculate the impact:

| Reform | Annual Impact | Extends Solvency By |
|--------|---------------|---------------------|
| Raise Payroll Cap | +$____B | ____ years |
| Reduce Benefits 10% | +$____B | ____ years |
| Raise Retirement Age | +$____B | ____ years |

### Exercise 3.2: Personal Reflection

If you were designing Social Security reform, what combination would you choose and why?

```
________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________
```

---

## Module 4: Uncertainty & Monte Carlo

**Notebook**: 05

### Learning Objectives

- [ ] Explain why point estimates are insufficient
- [ ] Interpret confidence intervals
- [ ] Run Monte Carlo simulations
- [ ] Analyze parameter sensitivity

### Key Concepts

**Monte Carlo Method** — In your own words:
```
________________________________________________________________

________________________________________________________________
```

**Confidence Interval** — In your own words:
```
________________________________________________________________

________________________________________________________________
```

### Exercise 4.1: Running Monte Carlo

Record your simulation results:

| Metric | Mean | 5th Percentile | 95th Percentile |
|--------|------|----------------|-----------------|
| 2034 Debt | $____T | $____T | $____T |
| 2044 Debt | $____T | $____T | $____T |
| 2054 Debt | $____T | $____T | $____T |

### Exercise 4.2: Sensitivity Analysis

Which input parameter had the LARGEST effect on outcomes?

Parameter: ____________________

Why does this parameter matter so much?
```
________________________________________________________________

________________________________________________________________
```

### Exercise 4.3: Convergence

How many simulations did you need before results stabilized?

- 100 runs: Still varying significantly? [ ] Yes [ ] No
- 500 runs: Still varying significantly? [ ] Yes [ ] No
- 1000 runs: Still varying significantly? [ ] Yes [ ] No

Approximately when did convergence occur? ________ runs

---

## Module 5: Tax Policy

**Notebook**: 06

### Learning Objectives

- [ ] Understand federal revenue structure
- [ ] Model tax policy changes
- [ ] Analyze behavioral responses (elasticity)
- [ ] Evaluate reform scenarios

### Tax Revenue Components

Fill in from Notebook 06:

| Source | Current Revenue | % of GDP |
|--------|-----------------|----------|
| Individual Income | $____T | ___% |
| Payroll | $____T | ___% |
| Corporate | $____T | ___% |
| Excise | $____B | ___% |
| Other | $____B | ___% |

### Exercise 5.1: Tax Reform Scenarios

Analyze each reform:

| Reform | 10-Year Revenue Impact | Distributional Effect |
|--------|------------------------|----------------------|
| Carbon Tax ($50/ton) | +$____T | |
| Wealth Tax (2%) | +$____T | |
| Corporate Rate 28% | +$____T | |
| Flat Tax (20%) | +$____T | |

### Exercise 5.2: Behavioral Response

Explain why a 10% tax increase doesn't always yield 10% more revenue:

```
________________________________________________________________

________________________________________________________________

________________________________________________________________
```

---

## Module 6: Advanced Topics

**Notebooks**: 07, 08, 09

### Policy Extraction (07)

What types of information can PoliSim extract from policy documents?

1. ________________________________________________
2. ________________________________________________
3. ________________________________________________

### API Integration (08)

Why would you use the API vs. direct imports?

```
________________________________________________________________

________________________________________________________________
```

### Custom Policy Design (09)

Sketch your custom policy here:

**Policy Name**: _________________________________

**Problem Addressed**: 
```
________________________________________________________________
```

**Revenue Mechanisms**:
| Mechanism | Annual Impact |
|-----------|---------------|
| | $____B |
| | $____B |

**Spending Changes**:
| Change | Annual Impact |
|--------|---------------|
| | $____B |
| | $____B |

**Net Annual Impact**: $________B (deficit increase/reduction)

---

## Capstone Project Guide

### Project Requirements Checklist

- [ ] **Part 1: Baseline Analysis**
  - [ ] 30-year projection generated
  - [ ] Key metrics identified
  - [ ] Baseline visualization created

- [ ] **Part 2: Policy Comparison**
  - [ ] At least 3 policies compared
  - [ ] Fair representation of each
  - [ ] Trade-off analysis completed

- [ ] **Part 3: Monte Carlo**
  - [ ] 500+ simulations run
  - [ ] Confidence intervals calculated
  - [ ] Sensitivity analysis performed

- [ ] **Part 4: Synthesis**
  - [ ] Executive summary written
  - [ ] Recommendations provided
  - [ ] Professional visualizations

### Capstone Notes

Use this space to plan your capstone:

**Research Question**:
```
________________________________________________________________

________________________________________________________________
```

**Policies to Compare**:
1. ________________________________________________
2. ________________________________________________
3. ________________________________________________

**Key Assumptions**:
```
________________________________________________________________

________________________________________________________________
```

**Main Findings** (complete after analysis):
```
________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________
```

---

## Glossary Quick Reference

| Term | Definition |
|------|------------|
| **Deficit** | Annual shortfall (spending > revenue) |
| **Debt** | Cumulative total of past deficits |
| **Debt-to-GDP** | Debt as percentage of economic output |
| **Trust Fund** | Reserves for specific programs (e.g., Social Security) |
| **Discretionary** | Spending requiring annual appropriation |
| **Mandatory** | Spending determined by eligibility rules |
| **Baseline** | Projection under current law |
| **Monte Carlo** | Simulation using random sampling |
| **Confidence Interval** | Range capturing true value with given probability |
| **Elasticity** | Responsiveness of one variable to another |

---

## Self-Assessment Checklists

### Beginner Level ✓

After completing Notebooks 01-02, I can:

- [ ] Explain the difference between deficit and debt
- [ ] Name the top 3 revenue sources
- [ ] Name the top 3 spending categories
- [ ] Run a basic PoliSim simulation
- [ ] Interpret a debt trajectory chart

### Intermediate Level ✓

After completing Notebooks 03-06, I can:

- [ ] Compare healthcare policy fiscal impacts
- [ ] Explain Social Security funding challenges
- [ ] Run and interpret Monte Carlo simulations
- [ ] Analyze tax policy trade-offs
- [ ] Create professional visualizations

### Advanced Level ✓

After completing Notebooks 07-10, I can:

- [ ] Extract policy mechanics from documents
- [ ] Use the PoliSim API programmatically
- [ ] Design and implement custom policies
- [ ] Conduct comprehensive fiscal analysis
- [ ] Produce professional policy reports

---

## Notes Section

Use this space for additional notes:

```
________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________

________________________________________________________________
```

---

*Good luck with your learning journey! Remember: the goal isn't just to run simulations, but to develop critical thinking about fiscal policy.*

---

**Questions?** Ask your instructor or post in the PoliSim community discussions.
