# Scenario Regeneration Script

## Purpose
Regenerates scenario JSON files from PDF policy documents with full extraction of all funding mechanisms and their GDP revenue percentages.

## Usage

```powershell
# Basic usage (auto-detects output path)
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf"

# Specify output path
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf" -o policies/my_scenario.json

# Specify policy name and type
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf" --policy-name "My Policy" --policy-type USGHA

# Use standard extraction (non-context-aware)
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf" --use-standard
```

## Example: USGHA

```powershell
python scripts/regenerate_scenario_from_pdf.py "project guidelines/policies and legislation/V1.22 United States Galactic Health Act of 2025.pdf"
```

**Output:**
- 11 funding mechanisms extracted
- Total revenue: 22.19% GDP (~$6.44T for 2025)
- Includes: payroll tax (7.95% GDP), converted premiums (5.5% GDP), redirected federal (3.5% GDP), efficiency gains (3% GDP), and 7 additional mechanisms

## Features

- ✅ Extracts all funding mechanisms with percentage rates and GDP estimates
- ✅ Captures surplus allocation rules
- ✅ Identifies circuit breakers and fiscal safeguards
- ✅ Extracts timeline milestones
- ✅ Validates JSON output
- ✅ Context-aware extraction (uses improved regex patterns)
- ✅ Automatic GDP percentage estimation for mechanisms

## Why This Matters

**Problem:** Old scenario files had incomplete mechanisms (4 mechanisms, 16% GDP revenue)  
**Solution:** Fresh extraction finds all mechanisms (11 mechanisms, 22% GDP revenue)  
**Impact:** Fixes 103T debt simulation error caused by 6% GDP revenue gap

## Output Format

Generated JSON includes:
```json
{
  "policy_name": "...",
  "policy_type": "USGHA",
  "description": "Generated from PDF extraction - 11 funding mechanisms",
  "mechanics": {
    "funding_mechanisms": [...],
    "surplus_allocation": {...},
    "circuit_breakers": [...],
    "innovation_fund": {...},
    "timeline_milestones": [...],
    "target_spending_pct_gdp": 7.0,
    "target_spending_year": 2047,
    "universal_coverage": true,
    "zero_out_of_pocket": true,
    "confidence_score": 0.87
  }
}
```

## Integration

After regeneration, use the scenario in simulations:

```python
from core.scenario_loader import load_scenario
from core import simulate_healthcare_years

policy = load_scenario("policies/my_regenerated_scenario.json")
df = simulate_healthcare_years(policy, base_gdp=29e12, initial_debt=35e12, years=22)
```

## Notes

- Context-aware extraction is default (more accurate, finds all mechanisms)
- Use `--use-standard` flag for simpler extraction (faster, may miss some mechanisms)
- GDP percentages are automatically estimated based on economic research when not explicitly stated in text
- Inflation escalator and EITC expansion mechanisms may not have GDP% (conditional/offsetting mechanisms)
