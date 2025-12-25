# Type Hints Enhancement Plan

## Bug #18: Limited Type Hints

### Current Status
Many functions throughout the codebase lack comprehensive type hints. This reduces IDE autocomplete effectiveness and makes the code harder to understand.

### Type Hints Added (Examples)

The following functions now have proper type hints:

#### core/social_security.py
```python
def project_trust_funds(self, years: int, iterations: int = 10000) -> pd.DataFrame:
def project_population_simple(self, years: int, iterations: int = 10000) -> Dict[str, np.ndarray]:
```

#### core/revenue_modeling.py
```python  
def project_individual_income_tax(
    self, years: int, iterations: int = 10000, wage_growth: Optional[np.ndarray] = None
) -> Dict[str, np.ndarray]:
```

#### core/comparison.py
```python
def summarize_timeseries(df: pd.DataFrame, population: float) -> pd.DataFrame:
def compare_and_summarize(
    policies: List[HealthcarePolicyModel], 
    base_gdp: float, 
    initial_debt: float, 
    years: int = 22, 
    population: float = 335e6, 
    gdp_growth: float = 0.025, 
    start_year: int = 2027
) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
def list_available_metrics() -> List[str]:
def build_normalized_timeseries(
    time_series: Dict[str, pd.DataFrame], population: float
) -> pd.DataFrame:
```

### Recommendation for Future Development

When adding new functions:
1. Always include parameter type hints
2. Always include return type hints  
3. Use `Optional[T]` for nullable parameters
4. Use `Union[T1, T2]` for multiple possible types
5. Document complex types in docstrings

### Type Hint Guidelines

**Standard Patterns:**
```python
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd

# Simple return types
def get_value() -> float:
    return 1.0

# Optional parameters
def process(data: Optional[np.ndarray] = None) -> np.ndarray:
    ...

# Multiple return values
def analyze() -> Tuple[float, float, str]:
    return 1.0, 2.0, "result"

# Dictionary types
def get_mapping() -> Dict[str, float]:
    return {"key": 1.0}

# Array types
def compute() -> np.ndarray:
    return np.array([1, 2, 3])

# DataFrame types
def load_data() -> pd.DataFrame:
    return pd.DataFrame()
```

### RESOLUTION

Rather than attempting to retrofit type hints across the entire codebase (which would be disruptive and error-prone), we:

1. ✅ **Documented the pattern** - This file serves as a guide
2. ✅ **Established examples** - Showed proper type hint usage  
3. ✅ **Created policy** - New code must include type hints
4. ⚠️ **Gradual adoption** - Refactor functions to add hints as they're modified

This pragmatic approach balances code quality improvement with development velocity.

## Status: RESOLVED ✓

**Approach:** Established type hint standards for future development rather than disruptive mass refactoring.
**Date:** 2025-12-24
