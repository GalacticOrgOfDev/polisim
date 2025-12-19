# Tests Module

This module contains **pytest unit and integration tests** for polisim.

## Test Files

- **`test_simulation_healthcare.py`** - Healthcare simulation tests
  - Policy loading and validation
  - Baseline vs. USGHA comparison (Excel tolerance validation)
  - Monte Carlo convergence
  - Economic metric accuracy

- **`test_comparison.py`** - Scenario comparison tests
  - Multi-policy comparison logic
  - Difference calculations
  - Report generation

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=core --cov-report=html

# Run specific test file
pytest tests/test_simulation_healthcare.py -v

# Run specific test
pytest tests/test_simulation_healthcare.py::test_usgha_loads -v
```

## Test Coverage Goals

- **Core simulation**: >90% coverage
- **Economics engine**: >85% coverage
- **Comparison logic**: >80% coverage
- **Overall target**: >85% project coverage

## Adding New Tests

1. Create `test_*.py` file in this directory
2. Use pytest conventions (function names start with `test_`)
3. Import fixtures and utilities from existing tests
4. Add docstrings explaining test purpose
5. Run `pytest` to validate

Example:

```python
def test_my_feature():
    """Test that my_feature works correctly."""
    result = my_function(input_data)
    assert result == expected_output
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Nightly schedule (planned)

