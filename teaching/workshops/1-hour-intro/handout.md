# PoliSim 1-Hour Workshop Handout

## Workshop Overview 📋

**Title:** Introduction to Federal Budget Simulation with PoliSim  
**Duration:** 1 hour  
**Level:** Beginner - No prior experience required

---

## Quick Reference Card

### Key Concepts

| Term | Definition |
|------|------------|
| **Revenue** | Money the government collects (taxes, fees) |
| **Spending** | Money the government pays out (programs, interest) |
| **Deficit** | When spending exceeds revenue in a year |
| **Debt** | Accumulated deficits over time |
| **Debt-to-GDP** | Debt as a percentage of economic output |
| **CBO** | Congressional Budget Office - official projections |

### FY2024 Federal Budget at a Glance

```
REVENUE (~$4.4 trillion)          SPENDING (~$6.8 trillion)
├── Income Tax (45%)              ├── Social Security (21%)
├── Payroll Tax (36%)             ├── Medicare (14%)
├── Corporate Tax (9%)            ├── Medicaid (10%)
└── Other (10%)                   ├── Defense (13%)
                                  ├── Interest (14%)
                                  └── Other (28%)
```

---

## Workshop Exercises Summary

### Exercise 1: Setup (5 min)
```python
from core.simulation import Simulation
from core.data_loader import DataLoader
print("PoliSim ready!")
```

### Exercise 2: Run Simulation (10 min)
```python
sim = Simulation(start_year=2024, end_year=2034)
results = sim.run()
```

### Exercise 3: Interpret Results (10 min)
- Look at debt-to-GDP ratio
- Identify key spending drivers
- Compare to CBO baseline

### Exercise 4: Policy Change (5 min)
```python
policy_config = {'discretionary_adjustment': -0.10}
policy_results = sim.run(policy_config=policy_config)
```

---

## Key Takeaways

1. **The federal budget is projected to grow** - Mandatory spending (Social Security, Medicare) drives most growth

2. **Debt-to-GDP ratio is increasing** - From ~98% in 2024 to ~126% by 2034 under current policy

3. **Small changes accumulate** - A 10% spending cut saves trillions over 10 years

4. **Projections depend on assumptions** - GDP growth, inflation, and interest rates all matter

---

## Discussion Questions

1. Why does mandatory spending grow automatically?
2. What happens when debt exceeds 100% of GDP?
3. How do interest rates affect the budget?
4. What policy options exist to stabilize the debt?

---

## Resources

- **PoliSim Dashboard:** http://localhost:8501
- **Documentation:** See `docs/` folder
- **Notebooks:** See `notebooks/` folder
- **GitHub:** https://github.com/GalacticOrgOfDev/polisim

---

## Glossary

**Baseline Projection:** What happens if no new laws are passed

**CBO (Congressional Budget Office):** Nonpartisan agency providing budget analysis

**Debt-to-GDP Ratio:** National debt divided by gross domestic product

**Deficit:** Annual shortfall (spending minus revenue)

**Discretionary Spending:** Spending Congress approves annually (defense, agencies)

**Fiscal Year:** October 1 to September 30 (e.g., FY2024 = Oct 2023 - Sep 2024)

**Mandatory Spending:** Spending required by existing law (Social Security, Medicare)

**Monte Carlo Simulation:** Running many scenarios with randomized inputs

**National Debt:** Total accumulated borrowing

**Trust Fund:** Dedicated accounts for specific programs (Social Security, Medicare)

---

*PoliSim - Open Source Federal Budget Simulation*  
*https://github.com/GalacticOrgOfDev/polisim*
