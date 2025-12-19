# Policies Module

This module contains **policy definitions, catalogs, and parameter configurations**.

## Components

- **`catalog.json`** - Registry of all available policies
  - Policy metadata (name, description, version)
  - Links to policy implementations
  - Comparison groups (healthcare, tax, defense, etc.)

- **`parameters.json`** - Default parameter values for all policies
  - Economic assumptions (inflation, discount rate, etc.)
  - Healthcare-specific parameters (cost per beneficiary, admin overhead)
  - Demographic data (population, age distribution)
  - Scenario configurations

- **`galactic_health_scenario.json`** - Pre-built scenario for USGHA
  - Complete 10-year economic projection setup
  - Monte Carlo configuration (iterations, seed)
  - Policy parameter overrides

## Usage

```python
from core.policies import load_policy, load_scenario
from core.scenario_loader import ScenarioLoader

# Load a policy definition
policy = load_policy("usgha")

# Load a pre-built scenario
scenario = load_scenario("galactic_health_scenario.json")

# Create custom scenario
loader = ScenarioLoader()
custom_scenario = loader.create_scenario(
    policy="usgha",
    iterations=1000000,
    years=10,
    custom_params={"healthcare_spending_target_gdp": 0.085}
)
```

## Adding New Scenarios

1. Create `new_scenario.json` with structure:
   ```json
   {
     "name": "My Scenario",
     "policy": "policy_key",
     "iterations": 100000,
     "years": 10,
     "parameters": {
       "param1": value1,
       "param2": value2
     }
   }
   ```
2. Register in `catalog.json`
3. Reference in runners with `--scenario new_scenario`

## Parameter Hierarchy

1. **Defaults** - `parameters.json`
2. **Policy-specific** - Policy class attributes
3. **Scenario overrides** - `*.json` scenario files
4. **Runtime args** - Command-line arguments override all

