# PoliSim Full-Day Technical Workshop Handout

## Workshop Overview 📋

**Title:** Advanced Fiscal Simulation with PoliSim  
**Duration:** 8 hours (including breaks and lunch)  
**Level:** Advanced - Python proficiency, statistics background required

---

## Agenda

| Time | Session | Topic |
|------|---------|-------|
| 9:00 - 9:30 | Introduction | Workshop objectives, environment setup |
| 9:30 - 11:00 | **Session 1** | Advanced Monte Carlo Techniques |
| 11:00 - 11:15 | Break | |
| 11:15 - 12:45 | **Session 2** | Custom Policy Design Framework |
| 12:45 - 1:45 | Lunch | |
| 1:45 - 2:45 | **Session 3** | API Integration & Automation |
| 2:45 - 3:00 | Break | |
| 3:00 - 4:00 | **Session 4** | Sensitivity Analysis & Reporting |
| 4:00 - 5:00 | **Capstone** | Complete Policy Analysis Project |

---

## Session 1: Monte Carlo Reference

### Distribution Types

| Variable | Distribution | Parameters | Rationale |
|----------|--------------|------------|-----------|
| GDP Growth | Normal | μ=2.2%, σ=0.8% | Symmetric around trend |
| Inflation | Normal | μ=2.5%, σ=0.5% | Fed target with variance |
| Healthcare Inflation | Lognormal | s=0.2, scale=4% | Right-skewed, cannot be negative |
| Recession Probability | Beta | α=2, β=8 | Bounded [0,1], concentrated at low end |
| Interest Rate Shock | Student's t | df=5, scale=0.5% | Fat tails for tail risk |

### Correlation Matrix

```
                 GDP    Infl   HCare  Unemp  IntRate
GDP Growth      1.00  -0.30   0.20  -0.60    0.40
Inflation      -0.30   1.00   0.60   0.30   -0.20
Healthcare      0.20   0.60   1.00   0.10    0.10
Unemployment   -0.60   0.30   0.10   1.00   -0.50
Interest Rate   0.40  -0.20   0.10  -0.50    1.00
```

### Convergence Guidelines

| Metric | 1K iter | 10K iter | 100K iter |
|--------|---------|----------|-----------|
| Mean | ±0.5% | ±0.15% | ±0.05% |
| 90% CI | ±2% | ±0.6% | ±0.2% |
| Tail (5th %ile) | ±5% | ±1.5% | ±0.5% |

**Recommendation:** Use 10K for exploratory, 100K for final analysis.

---

## Session 2: Policy Builder Reference

### Policy Component Structure

```python
@dataclass
class PolicyComponent:
    name: str               # Component name
    domain: PolicyDomain    # REVENUE, HEALTHCARE, etc.
    description: str        # Human-readable description
    parameters: Dict        # Domain-specific parameters
    start_year: int         # Implementation year
    end_year: int           # Optional sunset
    phase_in_years: int     # Gradual implementation
    confidence: float       # Estimation confidence (0-1)
```

### Available Policy Domains

| Domain | Key Parameters | Impact Mechanism |
|--------|----------------|------------------|
| REVENUE | rate_change, elasticity | Tax rate × Base × Elasticity |
| HEALTHCARE | federal_cost_change, admin_savings | Base × Change × Phase |
| SOCIAL_SECURITY | payroll_tax_increase, benefit_reduction | Separate revenue/spending |
| DEFENSE | spending_change | Direct spending adjustment |
| DISCRETIONARY | cut_percentage | Percentage reduction |
| INTEREST | N/A | Calculated from debt level |

### Phase-In Calculation

```
Phase Factor = min(1.0, years_since_start / phase_in_years)
Impact = Base Impact × Phase Factor
```

---

## Session 3: API Quick Reference

### Authentication

```bash
# Header-based authentication
Authorization: Bearer <api_key>
```

### Core Endpoints

```bash
# Run simulation
POST /api/v1/simulate
{
  "iterations": 10000,
  "start_year": 2024,
  "end_year": 2034,
  "policy_config": {...}
}

# Get baseline data
GET /api/v1/data/baseline

# Compare policies
POST /api/v1/policies/compare
{
  "policies": ["baseline", "usgha", "m4a"]
}
```

### Response Format

```json
{
  "status": "success",
  "simulation_id": "sim_abc123",
  "results": {
    "mean": {...},
    "percentiles": {...},
    "distributions": {...}
  }
}
```

### Rate Limits

| Tier | Requests/min | Iterations/day |
|------|--------------|----------------|
| Free | 10 | 100K |
| Basic | 60 | 1M |
| Pro | 300 | 10M |

---

## Session 4: Sensitivity Analysis

### Tornado Diagram Interpretation

```
                    Impact on 2034 Debt-to-GDP
                    ←  Reduces  |  Increases  →
                    ─────────────┼─────────────
GDP Growth         ████████████|              (±9 pp)
Healthcare Infl               ██|██████████   (±7 pp)
Interest Rate              ████|████████     (±7 pp)
SS COLA                      ██|████         (±3 pp)
Defense                       █|██           (±2 pp)
Discretionary                 █|█            (±1 pp)
```

**Reading the Diagram:**
- Longer bars = Higher sensitivity
- Left = Lower parameter value
- Right = Higher parameter value
- Focus policy on top 3 drivers

### Scenario Definitions

| Scenario | GDP Growth | Inflation | Unemployment |
|----------|------------|-----------|--------------|
| Baseline | 2.2% | 2.5% | 4.5% |
| Optimistic | 3.0% | 2.0% | 3.5% |
| Pessimistic | 1.5% | 3.5% | 6.0% |
| Stagflation | 0.5% | 5.0% | 7.0% |
| Recession | -2.0% | 1.0% | 9.0% |

---

## Capstone Project Guidelines

### Requirements

1. **Define Policy Package** (3+ components from 2+ domains)
2. **Run Monte Carlo** (10K+ iterations)
3. **Sensitivity Analysis** (tornado diagram)
4. **Comparative Analysis** (vs baseline and alternative)
5. **Professional Report** (executive summary, methodology, results)

### Evaluation Criteria

| Criterion | Weight |
|-----------|--------|
| Technical Correctness | 30% |
| Policy Realism | 25% |
| Analysis Depth | 25% |
| Report Quality | 20% |

### Sample Policy Ideas

1. **Deficit Hawk:** Revenue + spending cuts
2. **Progressive:** Tax wealthy + expand healthcare
3. **Conservative:** Cut spending + reduce taxes
4. **Technocratic:** Efficiency + structural reforms
5. **Hybrid:** Pick best from each approach

---

## Code Templates

### Monte Carlo with Correlation

```python
from scipy import stats
import numpy as np

# Cholesky decomposition
L = np.linalg.cholesky(correlation_matrix)
samples = np.random.standard_normal((n, k)) @ L.T
scaled = samples * stds + means
```

### Policy Package Builder

```python
policy = PolicyPackage(
    name="My Policy",
    description="Description"
)
policy.add_component(TaxRateChange(...))
policy.add_component(SpendingCut(...))
impact = project_policy_impact(policy, years)
```

### API Client Usage

```python
client = PoliSimClient(api_key="...")
baseline = client.get_baseline()
results = client.run_simulation(
    iterations=10000,
    policy_config=my_policy
)
```

---

## Resources

### Documentation
- API Reference: `docs/API_ENDPOINTS.md`
- Monte Carlo Methods: `docs/MONTE_CARLO.md`
- Policy Builder: `docs/POLICY_BUILDER.md`

### External Resources
- CBO Budget Outlook: https://cbo.gov/topics/budget
- SSA Trustees Report: https://ssa.gov/oact/tr/
- FRED Economic Data: https://fred.stlouisfed.org/

### Support
- GitHub Issues: https://github.com/GalacticOrgOfDev/polisim/issues
- Documentation: `docs/` directory
- Slack Community: (link TBD)

---

## Formulas Quick Reference

### Debt Dynamics
```
Debt(t+1) = Debt(t) + Deficit(t) + Interest(t)
Interest(t) = Debt(t) × Average_Rate
```

### Monte Carlo Standard Error
```
SE(mean) = σ / √n
SE(percentile) ≈ √(p(1-p)/(n×f(x)²))
```

### Elasticity Impact
```
Revenue_Change = Base × Rate_Change × Elasticity
```

### NPV of Policy
```
NPV = Σ Impact(t) / (1 + r)^t
```

---

*PoliSim - Open Source Federal Budget Simulation*  
*https://github.com/GalacticOrgOfDev/polisim*
