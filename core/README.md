# Core Module

This module contains the **simulation engine** for polisim.

## Components

- **`healthcare.py`** - Healthcare policy models and specifications
  - 8 pre-built policy implementations (USGHA, Current US, Medicare-for-All, etc.)
  - Data classes for comprehensive policy specifications
  - Policy factory for easy access

- **`economics.py`** - Economic modeling and Monte Carlo engine
  - Monte Carlo simulator for uncertainty quantification
  - Sensitivity analysis
  - Economic projection logic

- **`comparison.py`** - Multi-scenario comparison framework
  - Compare policies across key dimensions
  - Aggregate metrics and reporting
  - Difference calculations

- **`simulation.py`** - Unified simulation runner
  - Orchestrates healthcare + economic simulations
  - Manages scenario loading and execution
  - Result aggregation

- **`metrics.py`** - Key performance indicators
  - Cost projections
  - Coverage metrics
  - Healthcare outcome calculations
  - Fiscal impact analysis

- **`policies.py`** - Policy management utilities
  - Load/save policies
  - Parameter validation
  - Policy registry

- **`scenario_loader.py`** - Scenario configuration loading
  - YAML/JSON scenario import
  - Parameter mapping
  - Validation framework

## Usage

```python
from core import (
    get_policy_by_type,
    run_simulation,
    compare_scenarios,
    PolicyType
)

# Load a policy
usgha = get_policy_by_type(PolicyType.USGHA)

# Run simulation
results = run_simulation(usgha, iterations=100000, years=10)

# Compare scenarios
comparison = compare_scenarios([usgha, current_us_policy])
```

## Adding New Policies

1. Create a new policy class in `healthcare.py` inheriting from base
2. Implement required methods (validate, get_spending, get_outcomes)
3. Add to policy factory
4. Register in catalog.json

