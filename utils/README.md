# Utils Module

This module contains **utility functions and helpers** for I/O, data processing, and common operations.

## Components

- **`io.py`** - Input/output utilities
  - Load/save JSON, YAML, CSV files
  - Excel export (workbook creation)
  - Directory management

- **`__init__.py`** - Public API exports
  - Re-exports commonly used utilities
  - Convenience functions

## Usage

```python
from utils import load_json, save_csv, export_to_excel

# Load configuration
config = load_json("policies/parameters.json")

# Save results
save_csv(results, "reports/comparison.csv")

# Export to Excel
export_to_excel(
    dataframes={"Summary": df_summary, "Details": df_details},
    filename="reports/full_report.xlsx"
)
```

## Planned Utilities

- **Data validation** - Schema checking for policies/scenarios
- **Error logging** - Structured logging with context
- **Performance metrics** - Benchmarking and profiling
- **Cache management** - Local caching of expensive computations

