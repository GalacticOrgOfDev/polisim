# PoliSim Half-Day Policy Workshop Handout

## Workshop Overview 📋

**Title:** Policy Analysis with PoliSim  
**Duration:** 4 hours (including breaks)  
**Level:** Intermediate - Basic Python and economics knowledge

---

## Agenda

| Time | Topic | Exercise |
|------|-------|----------|
| 0:00 - 0:30 | Introduction & Setup | Environment verification |
| 0:30 - 1:15 | **Part 1:** Advanced Baseline | Revenue & spending decomposition |
| 1:15 - 1:30 | Break | |
| 1:30 - 2:30 | **Part 2:** Healthcare Policy | Compare 4 healthcare systems |
| 2:30 - 2:45 | Break | |
| 2:45 - 3:30 | **Part 3:** Social Security | Trust fund & reform scenarios |
| 3:30 - 4:00 | **Part 4:** Synthesis | Design your policy package |

---

## Key Concepts Reference

### Federal Budget Structure

```
REVENUE (FY2024: ~$4.4T)              SPENDING (FY2024: ~$6.8T)
─────────────────────────             ─────────────────────────
Individual Income Tax 45%   →→→→→→   Social Security     21%
Payroll Taxes        36%   →→→→→→   Medicare            14%  MANDATORY
Corporate Tax         9%   →→→→→→   Medicaid            10%    (65%)
Other                10%   →→→→→→   Other Mandatory      8%
                                    ─────────────────────
                                    Defense             13%  DISCRETIONARY
                                    Non-Defense         10%    (23%)
                                    ─────────────────────
                                    Net Interest        14%   (13%)
```

### Growth Rate Drivers

| Component | Growth Rate | Primary Drivers |
|-----------|-------------|-----------------|
| Social Security | ~5.5% | Aging population, COLA adjustments |
| Medicare | ~6.5% | Healthcare inflation, aging |
| Medicaid | ~4.5% | Healthcare costs, eligibility |
| Defense | ~2.5% | Policy-constrained |
| Interest | ~8% | Rising rates, growing debt |

---

## Healthcare Policy Comparison Matrix

| Policy | Coverage | Federal Cost | Total Cost | Admin | Timeline |
|--------|----------|--------------|------------|-------|----------|
| Current US | 92% | 5.8% GDP | 17.3% GDP | 15% | - |
| USGHA | 100% | 8.5% GDP | 12.0% GDP | 4% | 5 years |
| M4A | 100% | 10.5% GDP | 13.0% GDP | 3% | 4 years |
| UK NHS | 100% | 9.0% GDP | 11.0% GDP | 2% | 8 years |

### Key Trade-offs
- **USGHA:** Higher federal cost → Lower total system cost
- **M4A:** Highest federal cost → Eliminates private insurance
- **UK NHS:** Longest transition → Lowest admin overhead

---

## Social Security Quick Reference

### Trust Fund Mechanics
1. **Income Sources:**
   - Payroll taxes (12.4% split worker/employer)
   - Interest on trust fund reserves
   - Taxation of benefits

2. **Outgo:**
   - Monthly benefit payments
   - Administrative costs

3. **Trust Fund Status:**
   - Current balance: ~$2.8 trillion
   - Running annual deficit since 2021
   - Projected depletion: ~2033-2035

### Reform Levers

| Reform Type | Examples | Impact |
|-------------|----------|--------|
| **Revenue** | Raise payroll tax rate | +$15B per 0.1% |
| **Revenue** | Raise/eliminate cap | +$100B+ |
| **Benefits** | Reduce COLA | -$8B per 0.1% |
| **Benefits** | Raise retirement age | -$5B per month |
| **Mixed** | Means-testing | Variable |

---

## Monte Carlo Interpretation Guide

### Understanding Distributions

```
                      ┌──────────────────────────────────┐
                      │        DISTRIBUTION SHAPE        │
                      │                                  │
Probability ▲         │         ▄▄██████▄▄              │
           │          │       ▄█████████████▄            │
           │          │     ▄███████████████████▄        │
           │          │   ▄███████████████████████▄      │
           │──────────│▄▄███████████████████████████▄▄──│
                      │   5th     Mean    95th          │
                      │  percentile  │   percentile     │
                      │              │                  │
                      │        90% Confidence           │
                      │           Interval              │
                      └──────────────────────────────────┘
```

### Interpreting Results

- **Mean:** Expected average outcome
- **90% CI:** Range containing 90% of scenarios
- **Narrow distribution:** Lower uncertainty
- **Wide distribution:** Higher risk/uncertainty
- **Tail risk:** 5th percentile = "bad case" scenario

---

## Policy Design Framework

### Step 1: Identify Objectives
- [ ] Deficit reduction?
- [ ] Coverage expansion?
- [ ] Cost control?
- [ ] Program solvency?

### Step 2: Choose Instruments
- Healthcare model changes
- Social Security reforms
- Tax policy changes
- Discretionary adjustments

### Step 3: Evaluate Trade-offs
- Short-term vs long-term
- Federal cost vs total cost
- Political feasibility
- Distributional effects

### Step 4: Run Scenarios
- Baseline comparison
- Uncertainty analysis
- Sensitivity testing

---

## Discussion Questions

### Part 1: Baseline Analysis
1. Why is interest growing faster than any other category?
2. What happens if discretionary spending is frozen indefinitely?
3. How does the aging population affect revenue vs spending?

### Part 2: Healthcare
1. Why does USGHA lower total costs but raise federal costs?
2. What administrative functions could be eliminated?
3. How does healthcare policy affect overall deficit projections?

### Part 3: Social Security
1. What happens to benefits after trust fund depletion?
2. Why is raising the retirement age politically difficult?
3. How do demographic trends affect 75-year projections?

### Part 4: Synthesis
1. What constraints limit policy options?
2. How do you balance competing objectives?
3. What role does uncertainty play in policy design?

---

## Resources

- **PoliSim Dashboard:** http://localhost:8501
- **Full Documentation:** `docs/` directory
- **Jupyter Notebooks:** `notebooks/` directory
- **CBO Projections:** https://cbo.gov/topics/budget
- **SSA Trustees Report:** https://ssa.gov/oact/tr/

---

## Formulas Reference

### Deficit Calculation
```
Deficit = Spending - Revenue
```

### Debt-to-GDP Ratio
```
Debt-to-GDP = (Total Debt / GDP) × 100
```

### Trust Fund Balance
```
Balance(t+1) = Balance(t) + Income + Interest - Benefits
```

### Compound Growth
```
Future = Present × (1 + rate)^years
```

---

*PoliSim - Open Source Federal Budget Simulation*  
*https://github.com/GalacticOrgOfDev/polisim*
