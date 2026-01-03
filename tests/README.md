# Tests Module

This module contains **pytest unit and integration tests** for polisim with **750+ test functions** across **68+ test files**.

## Test Organization

Tests are organized by **functional domain** rather than development phase. Each test file name describes what it tests.

### Naming Conventions

- **File names**: `test_{domain}_{feature}.py`
- **Class names**: `Test{Feature}{Aspect}`  
- **Function names**: `test_{action}_{expected_result}`

---

## Test Categories

### 1. Core Simulation Models (~170 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_simulation_healthcare.py` | 16 | Healthcare simulation, policy loading, Monte Carlo |
| `test_social_security.py` | 22 | Social Security trust fund projections |
| `test_social_security_enhancements.py` | 31 | SS reforms, edge cases, enhancements |
| `test_medicare_medicaid.py` | 20 | Medicare/Medicaid model projections |
| `test_revenue_modeling.py` | 25 | Federal revenue projections |
| `test_tax_reform.py` | 37 | Tax reform scenarios |
| `test_economic_engine.py` | 24 | Monte Carlo engine, economic parameters |

### 2. Fiscal Integration (~100 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_fiscal_integration_social_security_revenue.py` | 18 | SS + Revenue combined projections |
| `test_fiscal_integration_discretionary_interest.py` | 27 | Discretionary + Interest + Combined outlook |
| `test_tax_reform_integration.py` | 19 | Tax reform policy packages |
| `test_baseline_validation_cbo_ssa.py` | 19 | CBO/SSA baseline validation |
| `test_combined_outlook_policy.py` | 5 | Combined fiscal outlook with policy mechanics |

### 3. Edge Cases & Validation (~100 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_edge_cases.py` | 50 | Edge case handlers |
| `test_edge_cases_fiscal_models.py` | 15 | SS/Revenue edge cases |
| `test_validation.py` | 36 | Data validation rules |
| `test_validation_integration.py` | 15 | Validation integration |

### 4. API & Security (~125 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_api_authentication.py` | 24 | JWT tokens, login/logout |
| `test_api_v1_endpoints.py` | 24 | API v1 endpoint contracts |
| `test_security.py` | 22 | OWASP Top 10 protection |
| `test_ddos_protection.py` | 22 | Rate limiting, circuit breakers |
| `test_integration_security_stack.py` | 18 | Full security pipeline |
| `test_secrets_management.py` | 33 | Secrets management, rotation |
| `test_ui_auth.py` | 8 | UI authentication flows |

### 5. Reports & Exports (~50 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_report_generation.py` | 13 | PDF/Excel report generation |
| `test_report_charts.py` | 12 | Chart generation |
| `test_scenario_comparison.py` | 14 | Scenario comparison logic |
| `test_scenario_diff_viewer.py` | 11 | Diff visualization |
| `test_scenario_builder_reports.py` | 21 | Scenario builder workflows |

### 6. Data Integration (~30 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_cbo_integration.py` | 26 | CBO data scraper, caching |
| `test_api_ingestion_health.py` | 2 | Data ingestion health checks |

### 7. Policy Extraction (~15 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_context_framework.py` | 5 | Context-aware extraction |
| `test_full_workflow.py` | 5 | End-to-end PDF extraction |
| `test_policy_extraction.py` | 1 | Basic policy extraction |

### 8. UI & Dashboard (~60 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_teaching_mode.py` | 37 | Teaching mode features |
| `test_themes_and_dash.py` | 6 | Theme switching |
| `test_tooltip_registry.py` | 5 | Tooltip system |
| `test_startup_check.py` | 7 | Startup validation |

### 9. Stress & Performance (~30 tests)

| File | Tests | Description |
|------|-------|-------------|
| `test_stress_scenarios.py` | 27 | Stress testing |
| `test_performance_sprint44.py` | 3 | Performance benchmarks |

---

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=core --cov-report=html

# Run specific category
pytest tests/test_security*.py -v         # All security tests
pytest tests/test_fiscal_*.py -v          # All fiscal integration tests
pytest tests/test_api_*.py -v             # All API tests

# Run specific test file
pytest tests/test_simulation_healthcare.py -v

# Run specific test class
pytest tests/test_tax_reform_integration.py::TestTaxReformPolicyPackage -v

# Run specific test function
pytest tests/test_social_security.py::test_trust_fund_projection -v

# Run with markers
pytest tests/ -m "not slow"               # Skip slow tests
pytest tests/ -m "security"               # Only security tests
```

## Test Coverage Goals

| Category | Target | Current |
|----------|--------|---------|
| Core simulation | >90% | ~85% |
| Economics engine | >85% | ~80% |
| API endpoints | >80% | ~75% |
| Security modules | >90% | ~85% |
| **Overall** | **>85%** | **~80%** |

---

## Adding New Tests

### 1. Choose the Right File

- **New feature in existing domain**: Add to existing `test_{domain}.py`
- **New domain**: Create `test_{domain}_{feature}.py`

### 2. Follow Naming Conventions

```python
class TestRevenueProjections:
    """Test federal revenue projection scenarios."""

    def test_baseline_revenue_grows_with_gdp(self):
        """Baseline revenue should grow proportionally with GDP."""
        model = FederalRevenueModel()
        result = model.project(years=10)
        assert result['revenue_growth'] > 0
```

### 3. Add Docstrings

Every test class and function should have a docstring explaining:
- What is being tested
- Expected behavior
- Any special setup requirements

### 4. Use Fixtures

```python
@pytest.fixture
def revenue_model():
    """Create a revenue model with standard parameters."""
    return FederalRevenueModel(base_gdp=28_000, seed=42)

def test_projection_deterministic(revenue_model):
    """Same seed should produce same results."""
    result1 = revenue_model.project(years=5)
    result2 = revenue_model.project(years=5)
    assert result1 == result2
```

### 5. Run Tests

```bash
# Validate your new tests
pytest tests/test_your_file.py -v

# Check coverage
pytest tests/test_your_file.py --cov=core.your_module
```

---

## Continuous Integration

Tests run automatically on:
- Pull requests to main branch
- Commits to main branch
- Nightly schedule (planned)

---

## Test Markers

```python
@pytest.mark.slow           # Long-running tests (>10s)
@pytest.mark.security       # Security-related tests
@pytest.mark.integration    # Integration tests
@pytest.mark.api            # API endpoint tests
@pytest.mark.skip           # Temporarily disabled tests
```

---

## Debugging Failed Tests

```bash
# Verbose output
pytest tests/test_file.py -v -s

# Stop on first failure
pytest tests/test_file.py -x

# Show local variables on failure
pytest tests/test_file.py --tb=long

# Run last failed tests
pytest tests/ --lf
```

