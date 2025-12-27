# Polisim Naming Conventions

## Established Conventions (As Of 2025-12-24)

This document codifies the naming conventions used throughout the polisim codebase to ensure consistency in future development.

### Function Naming

**Projection Functions:**
- Use `project_` prefix for forward-looking calculations
- Examples: `project_trust_funds()`, `project_population()`, `project_revenues()`

**Calculation Functions:**
- Use `calculate_` prefix for derived metrics
- Examples: `calculate_confidence()`, `calculate_metrics()`

**Data Loading/Retrieval:**
- Use `get_` prefix for data retrieval
- Examples: `get_ss_spending()`, `get_medicare_spending()`

### Variable Naming

**Monetary Values:**
- Use `_billions` suffix for values in billions of dollars
- Examples: `healthcare_spending_billions`, `debt_billions`, `revenue_billions`
- Exception: When column names or dictionary keys, context makes units clear

**Percentages:**
- Use `_pct` suffix for decimal percentages (0.05 = 5%)
- Use `_percent` suffix when displaying to users (5 = 5%)
- Examples: `target_spending_pct_gdp`, `admin_pct_now`

**GDP-Related:**
- Use `pct_gdp` for values as percentage of GDP
- Examples: `spending_pct_gdp`, `deficit_pct_gdp`

### Module Naming

**Models:**
- Descriptive names ending in purpose
- Examples: `SocialSecurityModel`, `FederalRevenueModel`, `MedicareModel`

**Data Classes:**
- End with `Assumptions` for input parameters
- Examples: `DemographicAssumptions`, `TrustFundAssumptions`
- End with `Mechanics` for policy structures
- Examples: `PolicyMechanics`, `FundingMechanism`

### Constants

**Naming:**
- ALL_CAPS_WITH_UNDERSCORES
- Examples: `MONTHS_PER_YEAR`, `POPULATION_CONVERSION_TO_MILLIONS`

**Organization:**
- Define at module level, immediately after imports
- Group related constants together
- Include inline comments explaining meaning

### Type Annotations

**Preferred Patterns:**
- `Optional[type]` for nullable values
- `List[type]` for homogeneous lists
- `Dict[key_type, value_type]` for dictionaries
- `Tuple[type, ...]` for tuples

### File Naming

**Scripts:**
- Use snake_case
- Descriptive action names
- Examples: `scripts/run_dashboard.py`, `scripts/extract_policy_parameters.py`

**Modules:**
- Use snake_case
- Noun-based for data/models
- Examples: `social_security.py`, `revenue_modeling.py`, `healthcare.py`

### DataFrame Column Naming

**Standard Columns:**
- Use title case with parentheses for units
- Examples: `"Health Spending ($)"`, `"Health % GDP"`, `"Year"`
- For internal use: lowercase with underscores
- Examples: `"spending_billions"`, `"debt_to_gdp_ratio"`

## Future Development Guidelines

### When Adding New Code:

1. **Functions:** Choose appropriate prefix (`project_`, `calculate_`, `get_`)
2. **Variables:** Be explicit with units (`_billions`, `_pct`, `_percent`)
3. **Constants:** Extract magic numbers to named constants
4. **Types:** Add type hints to all new functions
5. **Documentation:** Include docstrings with parameter descriptions

### When Refactoring:

1. Prioritize consistency within a module before cross-module changes
2. Update tests when changing function names
3. Use IDE refactoring tools to ensure all references are updated
4. Document breaking changes in CHANGELOG.md

## Cross-Reference

See also:
- `documentation/EXHAUSTIVE_INSTRUCTION_MANUAL.md` - Overall project structure
- `documentation/CONTEXT_FRAMEWORK.md` - Policy mechanics documentation
- Individual module docstrings for specific conventions
