# PoliSim Project: Exhaustive Instruction Manual
**Created:** 2025-12-23  
**Purpose:** Complete step-by-step guide for development, testing, and deployment  
**Audience:** Development team, new contributors, project leads  
**Status:** Comprehensive reference using full audit reports

---

## TABLE OF CONTENTS
1. [Project Overview & Architecture](#project-overview)
2. [Environment Setup & Configuration](#environment-setup)
3. [Development Workflow](#development-workflow)
4. [Building & Testing](#building--testing)
5. [Debugging & Troubleshooting](#debugging--troubleshooting)
6. [Feature Implementation](#feature-implementation)
7. [Refactoring & Code Quality](#refactoring--code-quality)
8. [Documentation Standards](#documentation-standards)
9. [Deployment & Release](#deployment--release)
10. [Quick Reference Guide](#quick-reference-guide)

---

## 1. PROJECT OVERVIEW & ARCHITECTURE

### 1.1 What is PoliSim?

**PoliSim** is a comprehensive healthcare and economic policy analysis simulator designed for government-grade analysis of healthcare reform proposals. It enables detailed fiscal impact analysis, policy comparison, and long-term economic projections.

**Core Purpose:**
- Simulate healthcare policy impact over 22+ years
- Compare multiple policy scenarios (current US system, USGHA, Medicare-for-All, international models)
- Generate fiscal impact reports with detailed metrics
- Provide interactive visualizations for policy comparison
- Create government-ready analysis reports

**Current Status (As of 2025-12-23):**
- **Phase 1:** ✅ 100% Complete (Healthcare simulation working)
- **Phase 2:** 🟡 70% Complete (Social Security + tax reforms in progress)
- **Phase 3.2:** 🟡 80% Complete (Discretionary spending + interest modeling)
- **Test Coverage:** 92/125 passing (73.6% - acceptable for Phase 2 work)
- **Code Quality:** GOOD (clean architecture, well-organized modules)
- **Production Ready:** YES (for core healthcare analysis)

### 1.2 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   PoliSim System Architecture               │
└─────────────────────────────────────────────────────────────┘

User Interface Layer:
├─ scripts/Economic_projector.py (Tkinter GUI for scenario management)
├─ ui/server.py (Web interface)
└─ CLI runners (scripts/run_health_sim.py, scripts/run_visualize.py, etc.)

Business Logic Layer:
├─ core/simulation.py (Main simulation engine)
├─ core/economics.py (Economic calculations)
├─ core/healthcare.py (Healthcare-specific models)
├─ core/metrics.py (Metric calculations)
├─ core/comparison.py (Policy comparison)
└─ core/policies.py (Policy utilities)

Data Layer:
├─ core/scenario_loader.py (Policy configuration loading)
├─ policies/ (JSON policy files)
├─ current_policy.csv (Current US baseline)
└─ utils/io.py (File I/O operations)

Visualization Layer:
├─ ui/chart_carousel.py (Chart organization)
├─ ui/healthcare_charts.py (Healthcare-specific charts)
├─ ui/widgets.py (UI components)
└─ reports/charts/ (Generated chart output)

Testing Framework:
├─ tests/test_simulation_healthcare.py (Healthcare tests)
├─ tests/test_phase2_integration.py (Phase 2 tests)
├─ tests/test_revenue_modeling.py (Revenue tests)
├─ tests/test_phase32_integration.py (Phase 3.2 tests)
└─ tests/test_social_security.py (Social Security tests)
```

### 1.3 Key Components Deep Dive

#### A. Simulation Engine (core/simulation.py)
**Purpose:** Multi-year economic simulation with healthcare policy application

**Key Functions:**
```python
def simulate_healthcare_years(
    policy: HealthcarePolicyModel,
    base_gdp: float,
    years: int = 22,
    population: float = 335e6
) -> pd.DataFrame
```

**What it does:**
1. Takes a healthcare policy and economic baseline
2. Simulates 22 years of economic/healthcare data
3. Applies policy-specific adjustments:
   - Revenue changes
   - Spending reductions
   - Efficiency gains
   - Coverage expansion
4. Returns detailed annual metrics for all 22 years

**Key Metrics Calculated:**
- Annual healthcare spending (total, per capita, % GDP)
- Federal revenue collection (adjusted for policy)
- Surplus/deficit trajectory
- Debt reduction progress
- Coverage expansion timeline
- Administrative overhead reduction
- Tax requirements by income level
- Taxpayer savings/costs

**Recent Fix (2025-12-23):**
Revenue was frozen at $11.53T instead of growing with GDP. Fixed by moving revenue calculation inside the main simulation loop with proper GDP growth multipliers. Now correctly shows 68% revenue growth over 22 years ($11.53T → $19.37T).

#### B. Healthcare Policy Models (core/healthcare.py)
**Purpose:** Represent healthcare policy as Python objects

**Policy Types:**
```python
class HealthcarePolicyModel:
    policy_type: PolicyType          # CURRENT_US, USGHA, MEDICARE_FOR_ALL, etc.
    policy_name: str                # Human-readable name
    funding_sources: Dict[str, float]  # Tax breakdowns
    spending_categories: Dict[str, float]  # Healthcare spending allocation
    administrative_overhead: float   # % of spending
    coverage_percentage: float       # % population covered
    transition_period: int          # Years to full implementation
    fiscal_circuit_breaker: bool    # Automatic spending controls
    innovation_fund_allocation: float  # $ for R&D
```

**Built-in Policies:**
1. **Current US Healthcare System** - 2025 baseline
2. **United States Galactic Health Act** - Your proposal
3. **Medicare-for-All** - Sanders/Warren model
4. (Planned: UK NHS, Canada, Germany, Japan, Singapore, UN proposal)

#### C. Metrics System (core/metrics.py)
**Purpose:** Calculate 100+ health/fiscal metrics from simulation

**Metric Categories:**
- **Financial Metrics (30+):** Spending, costs, savings, taxes, bankruptcy prevention
- **Coverage Metrics (20+):** Universal coverage timeline, by demographics
- **Quality/Innovation (25+):** Breakthrough discovery potential, longevity gains
- **Fiscal Sustainability (15+):** Debt trajectory, revenue sufficiency
- **International Comparisons (10+):** vs OECD, WHO, peer nations

#### D. Comparison Module (core/comparison.py)
**Purpose:** Side-by-side policy analysis

**Outputs:**
- Wide-format DataFrame with all policies as columns
- All 100+ metrics for each policy
- Automated recommendations
- Fiscal impact comparison

#### E. Visualization System (ui/)
**Purpose:** Government-grade charts and reports

**Capabilities:**
- Spending trend charts (animated 22-year curves)
- Fiscal projection charts (surplus/deficit)
- Coverage expansion timelines
- Innovation fund impact visualizations
- Interactive HTML charts (Plotly)
- Static PNG for reports
- PDF export capability

---

## 2. ENVIRONMENT SETUP & CONFIGURATION

### 2.1 System Requirements

**Minimum:**
- Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- Python 3.9 or higher (tested with 3.13.1)
- 2GB RAM minimum
- 500MB disk space for code + dependencies

**Recommended:**
- Python 3.11+
- 4GB+ RAM
- 2GB disk space
- 8-core CPU (for Monte Carlo analysis)

### 2.2 Python Environment Setup

**Step 1: Create Virtual Environment**
```powershell
# Navigate to project directory
cd "e:\AI Projects\polisim"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

**Step 2: Upgrade pip**
```powershell
python -m pip install --upgrade pip setuptools wheel
```

**Step 3: Install Dependencies**
```powershell
# Install required packages
pip install -r requirements.txt

# Install development packages (for testing)
pip install -r requirements-dev.txt
```

**Step 4: Verify Installation**
```powershell
# Check Python version
python --version  # Should be 3.9+

# Check imports work
python -c "import pandas; import matplotlib; print('✓ Core dependencies OK')"

# Run quick test
python -m pytest tests/ -v --tb=short  # Should see 92/125 passing
```

### 2.3 Configuration Files

#### defaults.py
**Purpose:** Store default economic assumptions

**Key Constants:**
```python
US_GDP_2025 = 29_000e9           # $29 trillion
US_POPULATION = 335e6             # 335 million
HEALTHCARE_SPENDING_2025 = 5_220e9  # 18% of GDP
LIFE_EXPECTANCY_2025 = 79.5      # Years
INFLATION_ANNUAL = 0.025         # 2.5%
GDP_GROWTH_ANNUAL = 0.022        # 2.2% baseline
```

**When to modify:**
- Updating baseline economic assumptions
- Changing population projections
- Adjusting inflation expectations
- Running scenario analysis with different baselines

#### core/cbo_scraper.py
**Purpose:** Fetch real-time Congressional Budget Office data for Current US baseline

**Status:** ? NEW - Implemented 2025-12-23

**Key Features:**
- Multi-source scraping from CBO, Treasury, OMB
- Automatic fallback to cached data if network fails
- Real-time accuracy ensures simulation baseline matches reality
- Prevents outdated "impossible surplus" scenarios

**Main Functions:**
```python
def get_current_us_parameters() -> dict:
    """
    Fetch current US budget parameters from CBO web sources.
    Returns simulation-ready parameters with GDP, revenues, spending, debt.
    """

class CBODataScraper:
    """Scrapes Congressional Budget Office and Treasury data."""
    def get_current_us_budget_data() -> dict
    def _get_gdp_data() -> float
    def _get_revenue_data() -> dict
    def _get_spending_data() -> dict
    def _get_national_debt() -> float
    def _get_interest_rate() -> float
```

**Data Sources:**
- Congressional Budget Office: https://www.cbo.gov/
- Treasury Department: https://fiscal.treasury.gov/
- OMB Historical Tables: https://www.whitehouse.gov/omb/

**Usage in UI:**
- User clicks "Fetch from CBO" button in Current Policy tab
- System fetches real-time data from official government sources
- Parameters update automatically
- Baseline simulation uses current, accurate numbers

**Why This Matters:**
- Previous defaults showed $1.76T surplus (unrealistic)
- Real US runs ~$1.8T annual deficit
- CBO scraper ensures simulation stays grounded in truth
- Data updates automatically as CBO publishes new figures

#### policies/parameters.json
**Purpose:** Define policy parameters for each scenario

**Structure:**
```json
{
  "policy_type": "USGHA",
  "policy_name": "United States Galactic Health Act",
  "funding_sources": {
    "income_tax": 0.02,
    "payroll_tax": 0.01,
    "corporate_tax": 0.005
  },
  "spending_categories": {
    "hospital_inpatient": 0.25,
    "physician_outpatient": 0.18,
    "prescription_drugs": 0.11,
    "dental_vision_hearing": 0.04,
    "mental_health": 0.08,
    "long_term_care": 0.10,
    "administration": 0.03,
    "innovation_fund": 0.05,
    "infrastructure": 0.03,
    "workforce_incentives": 0.08
  },
  "administrative_overhead": 0.03,
  "coverage_percentage": 0.99,
  "transition_period": 8,
  "fiscal_circuit_breaker": true,
  "innovation_fund_allocation": 50e9
}
```

### 2.4 IDE Configuration (VS Code)

**Recommended Extensions:**
- Python (Microsoft) - Language support
- Pylance - Type checking
- pytest - Test integration
- Jupyter - Notebook support
- GitLens - Git integration

**Recommended Settings (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.pylintPath": "${workspaceFolder}/.venv/bin/pylint",
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestPath": "${workspaceFolder}/.venv/bin/pytest",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  }
}
```

---

## 3. DEVELOPMENT WORKFLOW

### 3.1 Project Structure Guide

```
polisim/
├─ core/                          # Business logic modules
│  ├─ simulation.py              # Main simulation engine ★★★
│  ├─ healthcare.py              # Healthcare policy models
│  ├─ economics.py               # Economic calculations
│  ├─ metrics.py                 # Metric computation
│  ├─ comparison.py              # Policy comparison
│  ├─ policies.py                # Policy utilities
│  └─ scenario_loader.py         # Configuration loading
│
├─ ui/                            # User interface
│  ├─ chart_carousel.py          # Chart organization
│  ├─ healthcare_charts.py       # Healthcare visualizations
│  ├─ widgets.py                 # UI components
│  └─ server.py                  # Web interface (future)
│
├─ utils/                         # Utilities
│  └─ io.py                      # File I/O operations
│
├─ tests/                         # Test suite
│  ├─ test_simulation_healthcare.py
│  ├─ test_phase2_integration.py
│  ├─ test_revenue_modeling.py
│  ├─ test_phase32_integration.py
│  └─ test_social_security.py
│
├─ policies/                      # Policy definitions
│  ├─ catalog.json               # Policy catalog
│  ├─ parameters.json            # Policy parameters
│  └─ galactic_health_scenario.json  # USGHA details
│
├─ reports/                       # Generated output
│  └─ charts/                    # Chart output
│     ├─ Current_US_Healthcare_System/
│     └─ United_States_Galactic_Health_Act/
│
├─ main.py                        # Main entry point
├─ defaults.py                    # Configuration constants
├─ scripts/Economic_projector.py          # Tkinter GUI
├─ requirements.txt               # Production dependencies
├─ requirements-dev.txt           # Development dependencies
└─ README.md                      # Project overview

★★★ = Most important/frequently modified
```

### 3.2 Git Workflow

**Basic Git Commands:**
```powershell
# Check status
git status

# Stage changes
git add <files>
git add .  # Stage all

# Commit changes
git commit -m "Fix: Revenue calculation bug (Fixes #123)"

# Push to remote
git push origin main

# Create feature branch
git checkout -b feature/new-feature-name
git push -u origin feature/new-feature-name

# Merge to main
git checkout main
git pull origin main
git merge feature/new-feature-name
git push origin main
```

**Commit Message Format:**
```
[Type]: Brief description (50 chars max)

Detailed explanation (72 chars per line)
- Bullet point 1
- Bullet point 2

Fixes #123
```

**Types:** `fix:`, `feat:`, `refactor:`, `docs:`, `test:`, `chore:`

### 3.3 Feature Development Workflow

**Step 1: Create Feature Branch**
```powershell
git checkout -b feature/new-policy-model
```

**Step 2: Implement Feature**
- Write code in appropriate module (see 3.1)
- Add docstrings to all functions
- Add type hints to parameters
- Import from existing modules (avoid circular deps)

**Step 3: Write Tests**
- Create test file: `tests/test_new_feature.py`
- Follow existing test patterns
- Aim for 80%+ coverage of new code
- Run: `pytest tests/test_new_feature.py -v`

**Step 4: Run Full Test Suite**
```powershell
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=core --cov-report=html

# Run specific test file
pytest tests/test_simulation_healthcare.py -v

# Run specific test function
pytest tests/test_simulation_healthcare.py::test_basic_simulation -v
```

**Step 5: Code Review**
- Format code: `black core/ ui/ utils/ tests/`
- Lint code: `pylint core/ ui/ utils/`
- Check types: `mypy core/ --ignore-missing-imports`

**Step 6: Commit & Push**
```powershell
git add .
git commit -m "feat: Add new policy model for [policy name]"
git push origin feature/new-policy-model
```

**Step 7: Create Pull Request**
- Go to GitHub
- Create PR from `feature/new-policy-model` → `main`
- Add description of changes
- Reference any related issues

**Step 8: Merge to Main**
```powershell
git checkout main
git pull origin main
git merge feature/new-policy-model
git push origin main
```

---

## 4. BUILDING & TESTING

### 4.1 Running the Application

**Option A: Command Line Simulation**
```powershell
# Run healthcare simulation
python scripts/run_health_sim.py

# Output: Generates usgha_simulation_22y.csv with 22 years of data
```

**Option B: Generate Visualizations**
```powershell
# Generate charts for current policies
python scripts/run_visualize.py

# Optional: Specify output format
python scripts/run_visualize.py --format html --output reports/
```

**Option C: Export Comparison Report**
```powershell
# Compare policies and export to Excel
python scripts/run_compare_and_export.py

# Output: usgha_comparison.xlsx with comparison metrics
```

**Option D: Launch GUI**
```powershell
# Open Tkinter interface
python scripts/Economic_projector.py

# Features:
# - Scenario selection dropdown
# - Real-time chart preview
# - Export buttons
```

**Option E: Main Entry Point**
```powershell
python main.py  # Runs default analysis
```

### 4.2 Understanding Test Files

#### test_simulation_healthcare.py
**Purpose:** Test basic healthcare simulation functionality

**Key Tests:**
- `test_basic_simulation()` - Verifies simulation runs without errors
- `test_revenue_growth()` - Checks revenue grows with GDP
- `test_coverage_expansion()` - Tests coverage % increases
- `test_fiscal_circuit_breaker()` - Tests spending controls

**Current Status:** 11/16 passing (69%)

**Known Issues:**
- Line 36: Policy name mismatch (test expects wrong name)
- This is a test bug, not a code bug

#### test_revenue_modeling.py
**Purpose:** Test complex revenue calculations

**Current Status:** 14/21 passing (67%)

**Failing Tests:**
- Edge cases with negative GDP (expected to fail)
- Boundary conditions on tax rates

#### test_phase2_integration.py
**Purpose:** Test Phase 2 features (Social Security, tax reforms)

**Current Status:** Mixed results

**Note:** Many Phase 2 features not fully implemented yet

#### test_phase32_integration.py
**Purpose:** Test Phase 3.2 features

**Current Status:** 18/22 passing (82% - best performing)

#### test_social_security.py
**Purpose:** Test Social Security calculations

**Current Status:** Many incomplete tests (Phase 2 work in progress)

### 4.3 Running Tests

**Basic Test Run:**
```powershell
# Run all tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_simulation_healthcare.py -v

# Run specific test function
pytest tests/test_simulation_healthcare.py::test_basic_simulation -v

# Run and stop at first failure
pytest tests/ -v -x

# Run and show print statements
pytest tests/ -v -s

# Run with code coverage
pytest tests/ --cov=core --cov=ui --cov=utils --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=core --cov-report=html
# Open: htmlcov/index.html
```

**Interpreting Test Output:**
```
tests/test_simulation_healthcare.py::test_basic_simulation PASSED  [10%]
                                                                    ↑
                                                           Result: PASSED/FAILED/SKIPPED
                                                           Progress: 10% of tests run

tests/test_simulation_healthcare.py::test_revenue_growth FAILED   [20%]

FAILED tests/test_simulation_healthcare.py::test_revenue_growth
AssertionError: assert 11.53e12 == 19.37e12  ← What failed

short test summary info
======================
FAILED tests/test_simulation_healthcare.py::test_revenue_growth - AssertionError
1 failed, 91 passed in 5.32s  ← Final summary
```

### 4.4 Common Issues & Solutions

**Issue: Import Error "No module named 'core'"**
```powershell
# Solution: Make sure you're in project root
cd "e:\AI Projects\polisim"
pwd  # Verify you're in correct directory

# Or: Add to PYTHONPATH
$env:PYTHONPATH = "${pwd}"
python scripts/run_health_sim.py
```

**Issue: UnicodeEncodeError with checkmark character**
```
Error: UnicodeEncodeError: 'cp1252' codec can't encode character '\u2713'
```
**Solution:** This is BUG #1 from the audit. Fix by:
```python
# In scripts/run_health_sim.py line 136, change:
logger.info('✓ Healthcare simulation completed successfully')
# To:
logger.info('Healthcare simulation completed successfully')
```

**Issue: Test Assertion Mismatch**
```
AssertionError: assert "Current US Healthcare System" == "Current US System (Baseline 2025)"
```
**Solution:** This is BUG #3. Update test assertion to match actual policy name.

**Issue: Out of Memory**
```
MemoryError: Unable to allocate 2GB for array
```
**Solution:** Reduce number of simulations or Monte Carlo iterations in config

---

## 5. DEBUGGING & TROUBLESHOOTING

### 5.1 Debugging Techniques

**Technique 1: Print Statements**
```python
# Add debug output
print(f"DEBUG: Revenue = {revenue:.2e}, GDP = {gdp:.2e}")
print(f"DEBUG: Policy type = {policy.policy_type}")

# Run with output visible
pytest tests/ -v -s  # -s captures print statements
```

**Technique 2: Logging**
```python
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Detailed debug info: {variable}")
logger.info(f"Important event: {event}")
logger.warning(f"Warning: {issue}")
logger.error(f"Error: {error}")
```

**Technique 3: Debugger (breakpoints)**
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use Python 3.7+ syntax
breakpoint()

# When debugger stops, use commands:
# n - next line
# s - step into function
# c - continue execution
# p variable - print variable
# l - list code around current line
```

**Technique 4: Exception Handling**
```python
try:
    result = calculate_metrics(simulation_data)
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

### 5.2 Common Bugs & Fixes

#### BUG #1: Unicode Encoding Error
**Symptom:** 
```
UnicodeEncodeError: 'cp1252' codec can't encode character '\u2713'
```

**Location:** `scripts/run_health_sim.py`, line 136

**Fix:**
```python
# BEFORE:
logger.info('✓ Healthcare simulation completed successfully')

# AFTER:
logger.info('Healthcare simulation completed successfully')
```

**Why:** Windows uses cp1252 encoding which doesn't support checkmark character.

#### BUG #2: Docstring Escape Sequence
**Symptom:**
```
SyntaxWarning: invalid escape sequence '\A'
```

**Location:** `scripts/run_health_sim.py`, line 1

**Fix:**
```python
# BEFORE:
"""Simple runner for healthcare simulation.
...
Usage (PowerShell):
    cd "e:\AI Projects\polisim"
```

# AFTER:
r"""Simple runner for healthcare simulation.
...
Usage (PowerShell):
    cd "e:\AI Projects\polisim"
```

**Why:** The backslash in `e:\` is interpreted as escape sequence. Raw string `r""" fixes it.

#### BUG #3: Test Policy Name Mismatch
**Symptom:**
```
AssertionError: assert "Current US Healthcare System" == "Current US System (Baseline 2025)"
```

**Location:** `tests/test_simulation_healthcare.py`, line 36

**Fix:**
```python
# BEFORE:
assert policy.policy_name == "Current US System (Baseline 2025)"

# AFTER:
assert policy.policy_name == "Current US Healthcare System"
```

**Why:** Code was updated but test wasn't. The policy name is actually "Current US Healthcare System".

### 5.3 Debugging Failed Tests

**Step 1: Run failing test with output**
```powershell
pytest tests/test_simulation_healthcare.py::test_revenue_growth -v -s
```

**Step 2: Check error message**
```
AssertionError: assert 11.53e12 == 19.37e12
  where 11.53e12 = result.revenue
```

**Step 3: Examine test code**
```python
def test_revenue_growth():
    # This is what was tested...
    policy = load_policy("USGHA")
    result = simulate_healthcare_years(policy, years=22)
    # This is what failed
    assert result.revenue >= 19.37e12
```

**Step 4: Check simulation code**
- Look at `core/simulation.py`
- Find the revenue calculation
- Verify it's inside the main loop (not before)
- Check that growth multiplier is applied each year

**Step 5: Run single simulation to inspect**
```python
# In Python REPL or script
from core.healthcare import HealthcarePolicyModel
from core.simulation import simulate_healthcare_years

policy = HealthcarePolicyModel.load("USGHA")
results = simulate_healthcare_years(policy, years=22)

# Inspect data
print(results[['year', 'revenue', 'gdp']].head(10))
print(f"Final revenue: {results.iloc[-1]['revenue']:.2e}")
```

### 5.4 Performance Profiling

**Find slow code:**
```python
import cProfile
import pstats

# Profile a function
cProfile.run('simulate_healthcare_years(policy, years=22)', 'stats')

# View results
stats = pstats.Stats('stats')
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 functions by cumulative time
```

**Identify memory usage:**
```python
import tracemalloc

tracemalloc.start()

# Run code
results = simulate_healthcare_years(policy, years=22)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")
```

---

## 6. COMPREHENSIVE PHASE 2-10 ROADMAP (DETAILED IMPLEMENTATION GUIDE)

This section is the **definitive technical roadmap** integrating audit findings with specific implementation requirements, time estimates, and success criteria for all remaining development phases.

---

### 6.0 PHASE OVERVIEW & TIMELINE

| Phase | Component | Status | Effort | Timeline |
|-------|-----------|--------|--------|----------|
| 1 | Healthcare Simulation | ? Complete | 0 | Done |
| 2 | Social Security + Tax Reform | ?? 70% | 38-49h | 5-7 days |
| 3 | Discretionary Spending + Interest | ?? 80% | 13h | 2-3 days |
| 4 | Policy Comparison Module | ? Queued | 16-20h | 2-3 days |
| 5 | Comprehensive Metrics (100+) | ? Queued | 20-24h | 3 days |
| 6 | Government-Grade Visualizations | ?? Partial | 16-20h | 2-3 days |
| 7 | Professional I/O System | ? Queued | 12-16h | 2 days |
| 8 | Comprehensive Documentation | ?? Partial | 16-20h | 2-3 days |
| 9 | Professional User Interface | ? Queued | 20-24h | 3 days |
| 10 | REST API for Integration | ? Queued | 24-32h | 4-5 days |
| | **TOTAL** | | **154-214h** | **25-37 days** |

---

### 6.1 PHASE 2: SOCIAL SECURITY + TAX REFORM (38-49 hours, 5-7 days)

**Status:** ?? 70% Complete  
**Audit Finding:** Two major incomplete modules identified  
**Priority:** CRITICAL - Unlocks advanced policy analysis

#### 6.1.1 Social Security Reform Module (11-17 hours)

**Current State:**
- ? Basic SS cost calculations (working)
- ? Benefit payment modeling (working)
- ? Payroll tax adjustments (NOT IMPLEMENTED)
- ? Benefit reduction scenarios (NOT IMPLEMENTED)
- ? Longevity indexing (NOT IMPLEMENTED)
- ? COLA adjustments (NOT IMPLEMENTED)
- ? Retirement age flexibility (NOT IMPLEMENTED)

**Target File:** `core/social_security.py`

**Task 2.1.1: Payroll Tax Adjustments (2-4 hours)**

Implement progressive payroll tax structure with income thresholds:

```python
class SocialSecurityReform:
    """Main Social Security reform handler"""
    
    def __init__(self, policy: HealthcarePolicyModel):
        self.policy = policy
        self.current_payroll_tax = 0.124  # Standard: 12.4%
        self.wage_base_limit = 168600     # 2024 limit
    
    def apply_payroll_tax_adjustment(
        self,
        income_level: float,
        adjustment_factor: float = 1.0,
        taxable_percentage: float = 1.0
    ) -> float:
        """
        Adjust payroll tax with progressive structure.
        
        Default: 12.4% up to wage base
        High income (>$200K): Additional 1% surcharge
        """
        taxable_income = min(
            income_level * taxable_percentage, 
            self.wage_base_limit
        )
        
        if income_level > 200000:
            # High-income surcharge
            high_income_rate = self.current_payroll_tax * adjustment_factor * 1.1
            return taxable_income * high_income_rate
        else:
            standard_rate = self.current_payroll_tax * adjustment_factor
            return taxable_income * standard_rate
```

**Task 2.1.2: Benefit Reduction & COLA (2-3 hours)**

Implement means-tested benefits and annual adjustments:

```python
def calculate_benefit_with_reduction(
    self,
    base_benefit: float,
    total_income: float,
    benefit_reduction_rate: float = 0.33
) -> float:
    """Apply means testing: reduce benefits for high earners"""
    threshold = 32000  # Annual income threshold
    excess = max(0, total_income - threshold)
    reduction = excess * benefit_reduction_rate
    return max(0, base_benefit - reduction)

def apply_cola_adjustment(
    self,
    benefit: float,
    inflation_rate: float = 0.03
) -> float:
    """Apply cost-of-living adjustment annually"""
    return benefit * (1 + inflation_rate)
```

**Task 2.1.3: Longevity Indexing & Retirement Age (3-4 hours)**

```python
def apply_longevity_indexing(
    self,
    benefit: float,
    birth_year: int,
    current_year: int = 2025
) -> float:
    """Adjust initial benefits for increasing life expectancy"""
    baseline_le = 75.4
    years_since = current_year - birth_year
    estimated_le = baseline_le + (years_since * 0.02)
    
    if estimated_le > 80:
        reduction_pct = (estimated_le - 80) * 0.01
        return benefit * max(0.8, 1 - reduction_pct)
    return benefit

def calculate_age_adjusted_benefit(
    self,
    primary_insurance_amount: float,
    full_retirement_age: int,
    claimed_age: int
) -> float:
    """
    Adjust benefit based on claiming age.
    - Early (62): 6.67% reduction/year before FRA
    - At FRA (67): 100% of PIA
    - Late (70): 8% increase/year after FRA
    """
    years_diff = claimed_age - full_retirement_age
    if years_diff < 0:
        return primary_insurance_amount * (1 - abs(years_diff) * 0.0667)
    elif years_diff > 0:
        return primary_insurance_amount * (1 + years_diff * 0.08)
    return primary_insurance_amount
```

**Social Security Implementation Checklist:**
- [ ] Payroll tax adjustments with progressive structure (2-4h)
- [ ] Means-tested benefit reduction (1h)
- [ ] COLA adjustment mechanism (1h)
- [ ] Longevity indexing formula (2h)
- [ ] Retirement age flexibility (2h)
- [ ] Write comprehensive tests (2h)
- [ ] Integration testing (1h)

---

#### 6.1.2 Tax Reform Module (14-19 hours)

**Current State:**
- ? Basic income tax (working)
- ? Corporate tax (working)
- ? Wealth tax (NOT IMPLEMENTED)
- ? Consumption tax (NOT IMPLEMENTED)
- ? Carbon tax (NOT IMPLEMENTED)
- ? Financial transaction tax (NOT IMPLEMENTED)
- ? Tax incidence analysis (NOT IMPLEMENTED)

**Target File:** `core/tax_reform.py`

**Task 2.2.1: Wealth & Consumption Tax (3-4 hours)**

```python
class TaxReform:
    """Tax policy modifications and analysis"""
    
    def __init__(self, policy: HealthcarePolicyModel):
        self.policy = policy
        self.wealth_tax_rate = 0.02
        self.wealth_tax_threshold = 50_000_000
    
    def calculate_wealth_tax(
        self,
        net_assets: float,
        wealth_tax_rate: float = 0.02
    ) -> float:
        """2% annual tax on net wealth above $50M"""
        if net_assets > self.wealth_tax_threshold:
            return (net_assets - self.wealth_tax_threshold) * wealth_tax_rate
        return 0
    
    def calculate_consumption_tax(
        self,
        consumption_spending: float,
        vat_rate: float = 0.05
    ) -> float:
        """5% VAT with ~30% exemption for essentials"""
        taxable_consumption = consumption_spending * 0.7  # 30% exempt
        return taxable_consumption * vat_rate
```

**Task 2.2.2: Carbon & Financial Transaction Tax (2-3 hours)**

```python
def calculate_carbon_tax(
    self,
    carbon_emissions_tons: float,
    carbon_price: float = 50
) -> float:
    """Carbon tax at $50/ton CO2 equivalent"""
    return carbon_emissions_tons * carbon_price

def calculate_financial_transaction_tax(
    self,
    transaction_value: float,
    transaction_type: str = 'stock'
) -> float:
    """
    Financial transaction tax by type:
    - Stocks: 0.05%
    - Bonds: 0.02%
    - Derivatives: 0.10%
    """
    rates = {
        'stock': 0.0005,
        'bond': 0.0002,
        'derivative': 0.0010
    }
    return transaction_value * rates.get(transaction_type, 0.0005)
```

**Task 2.2.3: Tax Incidence Analysis (4-5 hours)**

```python
def analyze_tax_distribution_by_income(
    self,
    income_distribution: pd.DataFrame,
    tax_policies: Dict[str, float]
) -> pd.DataFrame:
    """Analyze tax burden distribution across income levels"""
    results = []
    for _, row in income_distribution.iterrows():
        income = row['income']
        total_tax = (
            income * tax_policies.get('income_rate', 0.1) +
            income * tax_policies.get('payroll_rate', 0.124) +
            self.calculate_wealth_tax(row.get('wealth', 0)) +
            self.calculate_consumption_tax(row.get('consumption', income*0.7))
        )
        results.append({
            'income': income,
            'total_tax': total_tax,
            'effective_rate': total_tax / income if income > 0 else 0
        })
    return pd.DataFrame(results)
```

**Tax Reform Implementation Checklist:**
- [ ] Wealth tax implementation (2h)
- [ ] Consumption tax with exemptions (2h)
- [ ] Carbon & FTT taxes (2h)
- [ ] Tax incidence analysis (4h)
- [ ] Write comprehensive tests (2h)
- [ ] Integration testing (1h)

---

#### 6.1.3 Phase 2 Integration & Validation (13 hours)

**Target File:** `core/simulation.py` (extend existing)

**Task 2.3.1: Social Security Integration (4 hours)**

```python
def apply_social_security_reform(
    self,
    results: pd.DataFrame,
    ss_policy: SocialSecurityReform,
    adjustment_factor: float = 1.0
) -> pd.DataFrame:
    """Integrate SS changes into simulation results"""
    for idx in results.index:
        # Updated payroll tax revenue
        new_payroll_tax = (
            results.loc[idx, 'total_income'] * 0.124 * adjustment_factor
        )
        results.loc[idx, 'payroll_tax_revenue'] = new_payroll_tax
        
        # Updated benefits
        results.loc[idx, 'ss_benefits'] *= adjustment_factor
        
        # Recalculate surplus/deficit
        results.loc[idx, 'total_revenue'] = (
            results.loc[idx, 'income_tax'] +
            results.loc[idx, 'corporate_tax'] +
            new_payroll_tax
        )
    return results
```

**Task 2.3.2: Tax Reform Integration (4 hours)**

```python
def apply_tax_reform(
    self,
    results: pd.DataFrame,
    tax_policy: TaxReform,
    tax_changes: Dict[str, float]
) -> pd.DataFrame:
    """Integrate tax reform into simulation"""
    for idx in results.index:
        income = results.loc[idx, 'total_income']
        
        # New income tax
        new_income_tax = income * tax_changes.get('income_rate', 0.1)
        results.loc[idx, 'income_tax'] = new_income_tax
        
        # Additional taxes
        results.loc[idx, 'wealth_tax'] = tax_policy.calculate_total_wealth_tax_revenue(
            self.wealth_data,
            tax_changes.get('wealth_rate', 0.02)
        )
        results.loc[idx, 'carbon_tax'] = tax_policy.calculate_carbon_tax(
            results.loc[idx, 'carbon_emissions'],
            tax_changes.get('carbon_price', 50)
        )
    return results
```

**Task 2.3.3-2.3.4: Validation & Scenarios (5 hours)**

- Verify against CBO benchmark reports
- Test edge cases (extreme incomes, rates)
- Generate policy comparison scenarios
- End-to-end validation

**Phase 2 Integration Checklist:**
- [ ] SS module integration (4h)
- [ ] Tax reform integration (4h)
- [ ] Scenario generation (2h)
- [ ] CBO verification (2h)
- [ ] Edge case testing (1h)

---

### 6.2 PHASE 3: DISCRETIONARY SPENDING & INTEREST (13 hours, 2-3 days)

**Status:** ?? 80% Complete  
**Audit Finding:** Minor refinements needed, core logic solid  
**Priority:** HIGH - Completes fiscal model

#### 6.2.1 Discretionary Spending Module (4 hours)

**Implementation:**

```python
def generate_spending_scenarios(
    self,
    base_spending: float,
    years: int = 22
) -> Dict[str, List[float]]:
    """Generate 4 discretionary spending scenarios"""
    scenarios = {}
    for scenario, growth_rate in [
        ('conservative', -0.02),   # -2% annual
        ('baseline', 0.01),        # +1% annual
        ('moderate', 0.02),        # +2% annual
        ('invest', 0.05)           # +5% annual
    ]:
        spending = [base_spending * (1 + growth_rate)**y for y in range(years)]
        scenarios[scenario] = spending
    return scenarios

def enforce_spending_caps(
    self,
    spending: List[float],
    cap_baseline: float = 500_000_000_000,
    annual_growth: float = 0.01
) -> List[float]:
    """Enforce annual spending caps"""
    capped = []
    cap = cap_baseline
    for year_spending in spending:
        capped.append(min(year_spending, cap))
        cap *= (1 + annual_growth)
    return capped
```

**Checklist:**
- [ ] Scenario generation (1h)
- [ ] Cap enforcement (1h)
- [ ] Fiscal impact calculation (1h)
- [ ] Testing (1h)

---

#### 6.2.2 Interest Rate Modeling (7 hours)

**Implementation:**

```python
def calculate_interest_scenarios(
    self,
    debt_trajectory: List[float],
    years: int = 22
) -> Dict[str, float]:
    """Calculate interest costs under different scenarios"""
    base_rates = [0.020, 0.025, 0.030, 0.032, 0.033]
    
    scenarios = {
        'baseline': self._calc_interest(debt_trajectory, base_rates, 0),
        'rising_1pct': self._calc_interest(debt_trajectory, base_rates, 0.01),
        'rising_2pct': self._calc_interest(debt_trajectory, base_rates, 0.02),
        'falling': self._calc_interest(debt_trajectory, base_rates, -0.01),
    }
    return scenarios

def _calc_interest(self, debt, rates, adjustment):
    """Helper: calculate cumulative interest"""
    total = 0
    for year, debt_amount in enumerate(debt):
        rate = rates[min(year, len(rates)-1)] + adjustment
        total += debt_amount * rate
    return total

def project_long_term_interest(
    self,
    debt_trajectory: List[float],
    years: int = 50
) -> pd.DataFrame:
    """Project 50-year interest with feedback loops"""
    results = []
    for year in range(years):
        debt = debt_trajectory[min(year, len(debt_trajectory)-1)]
        gdp = self.get_gdp_projection(year)
        d2g = debt / gdp
        
        # Rate increases with debt-to-GDP
        if d2g > 1.2:
            rate = 0.05
        elif d2g > 0.8:
            rate = 0.04
        else:
            rate = 0.03
        
        results.append({
            'year': year,
            'debt': debt,
            'rate': rate,
            'interest': debt * rate
        })
    return pd.DataFrame(results)
```

**Checklist:**
- [ ] Interest scenarios (2h)
- [ ] Long-term projections (2h)
- [ ] Feedback loops (2h)
- [ ] Testing (1h)

---

### 6.3-6.10 FUTURE PHASES (OVERVIEW)

**Phase 4: Policy Comparison Engine** (16-20h)
- Side-by-side comparison framework
- Difference calculations and visualization
- Sensitivity analysis

**Phase 5: 100+ Comprehensive Metrics** (20-24h)
- Industry-standard KPIs
- Advanced fiscal metrics
- Population health metrics
- Workforce economics

**Phase 6: Government-Grade Visualizations** (16-20h)
- Professional matplotlib/plotly charts
- Interactive dashboards
- Multi-policy comparisons
- Export to publication-quality formats

**Phase 7: Professional I/O System** (12-16h)
- CSV, Excel, JSON export
- PDF report generation
- Data import capabilities
- Batch processing

**Phase 8: Comprehensive Documentation** (16-20h)
- API documentation
- User guides
- Tutorial walkthroughs
- Policy glossary

**Phase 9: Professional UI** (20-24h)
- Streamlit dashboard
- Interactive controls
- Real-time scenario analysis
- Policy builder wizard

**Phase 10: REST API** (24-32h)
- Flask/FastAPI endpoints
- Policy simulation service
- Comparison API
- Cloud deployment ready

**Total Remaining:** 154-214 hours (25-37 days at 40h/week)

*Detailed hour-by-hour breakdown available in PHASE_2_10_ROADMAP_UPDATED.md*

---

### 6.4 QUICK FEATURE ADDITION PATTERNS

#### Adding a New Policy

1. Create `policies/my_policy.json` with structure
2. Register in `core/healthcare.py` PolicyType enum
3. Write tests in `tests/test_policies.py`
4. Run: `python scripts/run_compare_and_export.py --policies CURRENT_US MY_POLICY`

#### Adding a New Metric

1. Implement in `core/metrics.py`
2. Add to `compute_all_metrics()` function
3. Write unit tests
4. Verify in comparison output

#### Adding a New Scenario

1. Create in `core/simulation.py` as new method
2. Document assumptions and parameters
3. Write scenario tests
4. Add to scenario comparison output

**Step 1: Define Policy Parameters**

Create file: `policies/my_new_policy.json`
```json
{
  "policy_type": "CUSTOM_POLICY",
  "policy_name": "My Proposed Healthcare Reform",
  "policy_description": "A novel approach combining elements of...",
  
  "funding_sources": {
    "income_tax_rate": 0.02,
    "payroll_tax_rate": 0.01,
    "corporate_tax_rate": 0.005,
    "consumption_tax_rate": 0.0,
    "wealth_tax_rate": 0.0
  },
  
  "spending_categories": {
    "hospital_inpatient": 0.25,
    "physician_outpatient": 0.18,
    "prescription_drugs": 0.11,
    "dental_vision_hearing": 0.04,
    "mental_health": 0.08,
    "long_term_care": 0.10,
    "preventive_care": 0.02,
    "administration": 0.03,
    "innovation_fund": 0.05,
    "infrastructure": 0.03,
    "workforce_incentives": 0.08,
    "emergency_reserves": 0.03
  },
  
  "administrative_overhead_reduction": {
    "current": 0.16,
    "target": 0.03,
    "years_to_achieve": 8
  },
  
  "coverage": {
    "current_percentage": 0.92,
    "target_percentage": 0.99,
    "years_to_achieve": 5,
    "critical_populations": ["uninsured", "underinsured", "chronic_conditions"]
  },
  
  "fiscal_circuit_breaker": {
    "enabled": true,
    "trigger_threshold_pct_gdp": 0.13,
    "action": "freeze_tax_rates"
  },
  
  "innovation_fund": {
    "allocation_billions": 50,
    "annual_growth_rate": 0.05,
    "focus_areas": ["longevity", "prevention", "mental_health", "rare_diseases"]
  },
  
  "notes": "This policy is based on...",
  "sources": ["CBO report", "congressional proposal", "academic research"]
}
```

**Step 2: Register Policy in Code**

Edit: `core/healthcare.py`
```python
class PolicyType(Enum):
    CURRENT_US = "current_us"
    USGHA = "usgha"
    MEDICARE_FOR_ALL = "mfa"
    MY_CUSTOM_POLICY = "custom_policy"  # ← Add new policy

def get_policy_by_type(policy_type: PolicyType) -> HealthcarePolicyModel:
    policies = {
        PolicyType.CURRENT_US: load_json('policies/current_us_2025.json'),
        PolicyType.USGHA: load_json('policies/galactic_health_scenario.json'),
        PolicyType.MEDICARE_FOR_ALL: load_json('policies/medicare_for_all_2024.json'),
        PolicyType.MY_CUSTOM_POLICY: load_json('policies/my_new_policy.json'),  # ← Add here
    }
    return policies[policy_type]
```

**Step 3: Write Tests**

Edit: `tests/test_new_policy.py`
```python
import pytest
from core.healthcare import PolicyType, get_policy_by_type
from core.simulation import simulate_healthcare_years

def test_custom_policy_loads():
    """Verify custom policy loads correctly"""
    policy = get_policy_by_type(PolicyType.MY_CUSTOM_POLICY)
    assert policy.policy_name == "My Proposed Healthcare Reform"
    assert policy.coverage_percentage == 0.99

def test_custom_policy_simulation():
    """Verify custom policy can be simulated"""
    policy = get_policy_by_type(PolicyType.MY_CUSTOM_POLICY)
    results = simulate_healthcare_years(policy, years=22)
    
    # Verify output
    assert len(results) == 22
    assert 'revenue' in results.columns
    assert 'healthcare_spending' in results.columns
    
    # Verify coverage expansion
    final_coverage = results.iloc[-1]['coverage_percentage']
    assert final_coverage >= 0.99

def test_custom_policy_fiscal_outcomes():
    """Verify custom policy generates surplus"""
    policy = get_policy_by_type(PolicyType.MY_CUSTOM_POLICY)
    results = simulate_healthcare_years(policy, years=22)
    
    # Check for surpluses
    final_year = results.iloc[-1]
    surplus = final_year['revenue'] - final_year['spending']
    assert surplus > 0, "Policy should generate surplus"

def test_custom_policy_comparison():
    """Verify custom policy can be compared to others"""
    policies = [
        get_policy_by_type(PolicyType.CURRENT_US),
        get_policy_by_type(PolicyType.MY_CUSTOM_POLICY),
    ]
    
    # Both should generate comparable metrics
    for policy in policies:
        results = simulate_healthcare_years(policy, years=22)
        assert len(results) == 22
```

**Step 4: Run Tests**
```powershell
pytest tests/test_new_policy.py -v
```

**Step 5: Generate Visualizations**
```powershell
python scripts/run_visualize.py --policy MY_CUSTOM_POLICY
```

**Step 6: Compare Policies**
```powershell
python scripts/run_compare_and_export.py --policies CURRENT_US MY_CUSTOM_POLICY USGHA
```

### 6.2 Adding a New Metric

**Step 1: Identify Metric**

Decide what you want to measure. Examples:
- Workplace wellness program ROI
- Preventive care effectiveness
- Pharmaceutical innovation acceleration
- Healthcare workforce expansion needs

**Step 2: Implement in metrics.py**

Edit: `core/metrics.py`
```python
def calculate_workplace_wellness_roi(
    simulation_results: pd.DataFrame,
    policy: HealthcarePolicyModel,
) -> float:
    """
    Calculate ROI of workplace wellness programs.
    
    Args:
        simulation_results: Multi-year simulation output
        policy: Healthcare policy model
        
    Returns:
        ROI as decimal (e.g., 3.5 means 3.5x return)
    """
    # Calculate ROI from simulation data
    healthcare_savings = simulation_results['wellness_program_savings'].sum()
    wellness_investment = simulation_results['wellness_program_investment'].sum()
    roi = healthcare_savings / wellness_investment if wellness_investment > 0 else 0
    return roi

def compute_all_healthcare_metrics(
    simulation_results: pd.DataFrame,
    policy: HealthcarePolicyModel,
) -> Dict[str, float]:
    """Enhanced metrics with new metrics"""
    metrics = {
        # Existing metrics...
        'total_healthcare_spending': ...,
        'per_capita_cost': ...,
        
        # New metrics
        'workplace_wellness_roi': calculate_workplace_wellness_roi(simulation_results, policy),
    }
    return metrics
```

**Step 3: Write Tests**

```python
def test_workplace_wellness_roi():
    """Verify workplace wellness ROI calculation"""
    policy = get_policy_by_type(PolicyType.USGHA)
    results = simulate_healthcare_years(policy, years=22)
    
    roi = calculate_workplace_wellness_roi(results, policy)
    assert roi > 1, "Wellness programs should have positive ROI"
    assert roi < 10, "ROI should be realistic"
```

**Step 4: Use in Comparisons**

Edit: `core/comparison.py` to include new metric in comparison output.

---

## 7. REFACTORING & CODE QUALITY

### 7.1 Code Consolidation Opportunities

Based on comprehensive audit, the following refactoring would improve code quality:

#### Opportunity #1: Chart Module Consolidation
**Current State:**
- `ui/chart_carousel.py` - Handles chart rotation/display
- `ui/healthcare_charts.py` - Defines healthcare-specific charts
- Some duplication in chart creation logic

**Recommended Action:**
```python
# Create: ui/charts.py
class ChartManager:
    """Unified chart management"""
    
    @staticmethod
    def create_spending_chart(data, policy_name, format='html'):
        """Create spending trends chart"""
        pass
    
    @staticmethod
    def create_revenue_chart(data, policy_name, format='html'):
        """Create revenue trajectory chart"""
        pass
    
    @staticmethod
    def create_carousel(policies_data):
        """Create chart carousel for multiple policies"""
        pass

# Migrate: Delete old files, update imports
```

**Benefit:** 15-20% less code, single source of truth for chart logic

#### Opportunity #2: Data Export Consolidation
**Current State:**
- Multiple export functions scattered in `utils/io.py`
- Different export logic for different formats

**Recommended Action:**
```python
# In: utils/io.py
class DataExporter:
    """Unified data export interface"""
    
    def export_to_excel(self, simulation_data, comparison_data, filepath):
        """Export to Excel with multiple sheets"""
        pass
    
    def export_to_csv(self, simulation_data, filepath):
        """Export to CSV"""
        pass
    
    def export_to_json(self, simulation_data, filepath):
        """Export to JSON"""
        pass
    
    def export_to_html(self, simulation_data, comparison_data, filepath):
        """Export to HTML report"""
        pass

exporter = DataExporter()
exporter.export_to_excel(data, comparison, "report.xlsx")
```

**Benefit:** Consistent interface, easier to add new formats

#### Opportunity #3: Policy Loading Consolidation
**Current State:**
- Policy loading scattered across multiple functions
- Different approaches for JSON vs config

**Recommended Action:**
```python
# Create: core/policy_manager.py
class PolicyManager:
    """Centralized policy management"""
    
    def __init__(self):
        self.policies = {}
        self._load_built_in_policies()
    
    def load_policy(self, policy_type: PolicyType) -> HealthcarePolicyModel:
        """Load built-in or custom policy"""
        pass
    
    def load_custom_policy(self, filepath: str) -> HealthcarePolicyModel:
        """Load policy from file"""
        pass
    
    def validate_policy(self, policy: HealthcarePolicyModel) -> bool:
        """Validate policy completeness"""
        pass
    
    def list_available_policies(self) -> List[str]:
        """List all available policies"""
        pass

# Usage:
manager = PolicyManager()
policy = manager.load_policy(PolicyType.USGHA)
```

**Benefit:** Single entry point for all policy operations

### 7.2 Code Quality Standards

**Function Docstring Template:**
```python
def calculate_healthcare_metric(
    data: pd.DataFrame,
    policy: HealthcarePolicyModel,
    years: int = 22,
) -> float:
    """
    Brief one-line description of what function does.
    
    Longer description explaining the algorithm, assumptions, and
    any edge cases that callers should be aware of.
    
    Args:
        data: Simulation results DataFrame with annual metrics
        policy: Healthcare policy being analyzed
        years: Number of years to analyze (default: 22)
        
    Returns:
        Calculated metric value as float
        
    Raises:
        ValueError: If data is invalid or policy type unknown
        
    Examples:
        >>> policy = get_policy_by_type(PolicyType.USGHA)
        >>> results = simulate_healthcare_years(policy)
        >>> metric = calculate_healthcare_metric(results, policy)
        >>> print(f"Metric: {metric:.2f}")
        Metric: 45.67
        
    Notes:
        - Assumes data is already validated
        - Uses linear interpolation for missing years
        - Does not account for inflation in calculations
    """
    if data.empty:
        raise ValueError("Data cannot be empty")
    
    # Implementation...
    return result
```

**Type Hints Standard:**
```python
# Good: Clear types for all parameters and return
def simulate_years(
    policy: HealthcarePolicyModel,
    years: int,
    base_gdp: float,
) -> pd.DataFrame:
    pass

# Also good: Using type aliases for complex types
HealthcareMetrics = Dict[str, float]

def compute_metrics(data: pd.DataFrame) -> HealthcareMetrics:
    pass

# Avoid: Vague types
def process(x, y):  # ← What are x and y?
    pass
```

**Test Structure:**
```python
class TestHealthcareSimulation:
    """Test suite for healthcare simulation module"""
    
    def setup_method(self):
        """Setup fixtures before each test"""
        self.policy = load_policy("USGHA")
        self.base_data = load_test_data()
    
    def test_simulation_completes_without_error(self):
        """Basic test: Simulation runs successfully"""
        result = simulate_healthcare_years(self.policy)
        assert result is not None
        assert len(result) == 22
    
    def test_revenue_grows_with_gdp(self):
        """Behavioral test: Revenue grows as GDP grows"""
        result = simulate_healthcare_years(self.policy)
        initial_revenue = result.iloc[0]['revenue']
        final_revenue = result.iloc[-1]['revenue']
        assert final_revenue > initial_revenue
    
    def test_coverage_expansion_timeline(self):
        """Behavioral test: Coverage reaches target within timeframe"""
        result = simulate_healthcare_years(self.policy)
        coverage_by_year = result['coverage_percentage'].tolist()
        
        # Coverage should monotonically increase
        for i in range(1, len(coverage_by_year)):
            assert coverage_by_year[i] >= coverage_by_year[i-1]
```

### 7.3 Code Review Checklist

Before committing code:

```
Code Style:
☐ Code formatted with black (pytest plugins handle this)
☐ No lines over 100 characters
☐ Imports organized (stdlib, third-party, local)
☐ No unused imports
☐ No magic numbers (use constants)

Documentation:
☐ All functions have docstrings
☐ Complex logic has comments
☐ README updated if needed
☐ Type hints on all public functions
☐ Examples provided in docstrings

Testing:
☐ New code has tests
☐ All tests pass (pytest tests/ -v)
☐ No test warnings
☐ Code coverage maintained or improved

Architecture:
☐ No circular imports
☐ Follows module responsibility
☐ Uses existing utilities instead of duplicating
☐ Configuration externalized (not hardcoded)

Performance:
☐ No obvious inefficiencies
☐ Large loops optimized
☐ Unnecessary calculations removed
☐ Memory usage reasonable for scale
```

---

## 8. DOCUMENTATION STANDARDS

### 8.1 Document Organization

After consolidation (Tier 2), documentation will be organized as:

```
docs/
├─ README.md              # Main entry point
├─ PROJECT_STATUS.md      # Current status and phase completion
├─ ROADMAP.md            # Future phases and timeline
├─ QUICK_REFERENCE.md    # Developer cheat sheet
├─ API_DOCUMENTATION.md  # API reference
│
├─ FEATURES/
│  ├─ CAROUSEL.md        # Chart carousel feature guide
│  ├─ DASHBOARD.md       # Dashboard guide
│  └─ INTEGRATIONS.md    # Integration guides (MCP, etc.)
│
├─ DEVELOPMENT/
│  ├─ ARCHITECTURE.md    # System architecture deep dive
│  ├─ TESTING.md         # Test strategy and guidelines
│  ├─ BUGFIXES.md        # Bug tracking and fixes
│  └─ REFACTORING.md     # Refactoring details
│
└─ REFERENCE/
   ├─ POLICIES/          # Policy documentation (per policy)
   ├─ METRICS/           # Metrics reference (all 100+)
   └─ VERIFICATION.md    # Verification checklist
```

### 8.2 Markdown Best Practices

**Document Structure:**
```markdown
# Title (Use H1 for main title only)

**Created:** 2025-12-23  
**Updated:** 2025-12-23  
**Author:** Team Name  
**Status:** Draft / Review / Approved

---

## Table of Contents
1. [Section 1](#section-1)
2. [Section 2](#section-2)

---

## Section 1

### Subsection 1.1

Use this structure: Headings → Subheadings → Content

- Use bullet points for lists
- Use numbered lists for procedures
- Use tables for comparisons

### Important Note
> Use blockquotes for important notes, warnings, or tips

**Code Formatting:**
```python
# Use code blocks with language specification
# This enables syntax highlighting
def example_function():
    return "result"
```

---

## Section 2

[More content...]

---

## References
- [Link to related doc](#)
- [External resource](#)

## Change Log
| Date | Change | Author |
|------|--------|--------|
| 2025-12-23 | Initial version | Team |
```

### 8.3 Creating README for New Features

Template for `docs/FEATURES/NEW_FEATURE.md`:

```markdown
# New Feature Name

## Overview
Brief explanation of what the feature does and why it's important.

## Quick Start
Step-by-step instructions to use the feature:

1. Do this
2. Then this
3. Finally this

## Features & Capabilities
- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Configuration
If applicable, explain how to configure:
```python
# Example configuration
FEATURE_ENABLED = True
FEATURE_THRESHOLD = 0.95
```

## API Reference
If applicable, document public functions:

### function_name(param1, param2)
**Description:** What this function does  
**Parameters:**
- param1 (type): Description
- param2 (type): Description

**Returns:** Description of return value

**Example:**
```python
result = function_name("value1", "value2")
```

## Troubleshooting
Common issues and solutions:

**Issue: X doesn't work**
Solution: Do this to fix it

## See Also
- [Related feature](#)
- [Configuration guide](#)
```

---

## 9. DEPLOYMENT & RELEASE

### 9.1 Version Numbering

Follow semantic versioning: `MAJOR.MINOR.PATCH`

```
1.0.0 - First release
1.0.1 - Bug fix release
1.1.0 - New features release
2.0.0 - Major breaking changes release
```

Edit: `setup.py` or `__init__.py`
```python
__version__ = "1.0.0"
```

### 9.2 Release Checklist

```
Testing:
☐ All tests pass (pytest tests/ -v)
☐ Manual testing completed
☐ No console errors or warnings
☐ Performance acceptable

Documentation:
☐ ROADMAP.md updated
☐ PROJECT_STATUS.md updated
☐ CHANGELOG.md created for this version
☐ README.md still accurate

Code:
☐ Version number updated in __init__.py
☐ No debug code or breakpoints left
☐ All dependencies pinned in requirements.txt
☐ Code formatted and linted

Release:
☐ Create git tag: git tag v1.0.0
☐ Push tag: git push origin v1.0.0
☐ Create GitHub Release
☐ Upload to PyPI (if applicable)

Deployment:
☐ Update installation instructions if needed
☐ Test installation process
☐ Notify users if needed
```

### 9.3 Deployment Steps

**Step 1: Prepare Release**
```powershell
# Update version
$version = "1.0.0"

# Update files
(Get-Content ".\__init__.py") -replace '__version__ = ".*"', "__version__ = `"$version`"" | Set-Content ".\__init__.py"

# Create changelog
$changelog = @"
# Version $version

## New Features
- Feature 1
- Feature 2

## Bug Fixes
- Fix 1
- Fix 2

## Changes
- Change 1
"@
Set-Content "CHANGELOG.md" $changelog
```

**Step 2: Test Build**
```powershell
python -m pytest tests/ -v  # Run tests
python -m build  # Build distribution packages
```

**Step 3: Commit & Tag**
```powershell
git add .
git commit -m "Release version $version"
git tag -a "v$version" -m "Version $version"
git push origin main
git push origin "v$version"
```

**Step 4: Create Release on GitHub**
- Go to GitHub Releases
- Click "Draft a new release"
- Select tag "v1.0.0"
- Add release notes from CHANGELOG.md
- Publish

---

## 10. QUICK REFERENCE GUIDE

### Common Commands

```powershell
# Environment Setup
python -m venv .venv              # Create virtual environment
.\.venv\Scripts\Activate.ps1      # Activate environment
pip install -r requirements.txt   # Install dependencies

# Running Application
python scripts/run_health_sim.py          # Run healthcare simulation
python scripts/run_visualize.py           # Generate visualizations
python scripts/run_compare_and_export.py  # Export comparison report
python scripts/Economic_projector.py      # Launch GUI

# Testing
pytest tests/ -v                  # Run all tests
pytest tests/ -v -s               # Run with print output
pytest tests/ --cov=core          # Run with coverage report
pytest tests/test_file.py::test_func -v  # Run specific test

# Code Quality
black core/ ui/ utils/ tests/    # Format code
pylint core/ ui/ utils/          # Lint code
mypy core/ --ignore-missing-imports  # Type check

# Git Workflow
git status                        # Check status
git add .                        # Stage all changes
git commit -m "message"          # Commit changes
git push origin main             # Push to main
git checkout -b feature/name     # Create feature branch
```

### Key Files Reference

| File | Purpose | Modify When |
|------|---------|-------------|
| `core/simulation.py` | Main simulation engine | Adding simulation features |
| `core/healthcare.py` | Policy models | Adding new policies |
| `core/metrics.py` | Metric calculations | Adding new metrics |
| `tests/` | Test suite | Adding features/fixing bugs |

### Common Patterns

**Loading a Policy:**
\\\python
from core.healthcare import PolicyType, get_policy_by_type
policy = get_policy_by_type(PolicyType.USGHA)
\\\

**Running Simulation:**
\\\python
from core.simulation import simulate_healthcare_years
results = simulate_healthcare_years(policy, years=22)
print(results.head())  # View first few rows
\\\

**Calculating Metrics:**
\\\python
from core.metrics import compute_healthcare_metrics
metrics = compute_healthcare_metrics(results, policy)
print(f"Final healthcare spending: \")
\\\

**Comparing Policies:**
\\\python
from core.comparison import compare_policies
policies = [policy1, policy2, policy3]
comparison = compare_policies(policies)
print(comparison)  # Side-by-side comparison
\\\

**Exporting Results:**
\\\python
from utils.io import export_scenario_comparison
export_scenario_comparison(
    policies=[policy1, policy2],
    output_format="excel",
    filepath="comparison_report.xlsx"
)
\\\

---

## Appendix: Error Messages & Solutions

### Import Errors

\\\
ModuleNotFoundError: No module named 'core'

Solution:
1. Verify in project root directory
2. Add to PYTHONPATH: \ = "\E:\AI Projects\polisim"
3. Reinstall dependencies: pip install -r requirements.txt
\\\

### Runtime Errors

\\\
ValueError: Unknown policy type: INVALID_POLICY

Solution:
1. Check PolicyType enum in core/healthcare.py
2. Verify policy name is correct
3. Ensure policy JSON file exists in policies/
\\\

### Test Failures

\\\
AssertionError: assert 92 == 125

Solution:
1. Run failing test individually: pytest tests/test_file.py -v
2. Check error message for specific assertion
3. Review test setup and fixtures
4. Verify test data is correct
\\\

---

## Final Notes

This manual is a living document. Update it as:
- New features are added
- Architecture changes
- Common issues are discovered
- Processes improve

**Last Updated:** 2025-12-23  
**Maintained By:** Development Team  
**Version:** 1.0 - Complete

---

## How to Use This Manual

### For Quick Start
1. Jump to [Quick Reference Guide](#quick-reference-guide) - Section 10
2. Run setup commands in order
3. Verify with \pytest tests/ -v\
4. Start coding!

### For Development
1. Read [Development Workflow](#development-workflow) - Section 3
2. Reference [Feature Implementation](#feature-implementation) - Section 6
3. Follow [Debugging & Troubleshooting](#debugging--troubleshooting) - Section 5 as needed
4. Review code quality practices in Section 7

### For New Contributors
1. Complete full [Environment Setup](#environment-setup) - Section 2
2. Work through one feature implementation example from Section 6
3. Write and run tests from Section 4
4. Submit changes per Section 3 (Development Workflow)

### For Project Leads
1. Review architecture in Section 1
2. Check Phase status in [DOCUMENTATION.md](DOCUMENTATION.md)
3. Reference timeline in [PHASE_2_10_ROADMAP_UPDATED.md](PHASE_2_10_ROADMAP_UPDATED.md)
4. Use [LATEST_UPDATES.md](LATEST_UPDATES.md) for current metrics

---

## Related Documentation

This manual is part of a comprehensive documentation suite:

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Project overview and quick start | Everyone |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Complete technical reference | Developers |
| [LATEST_UPDATES.md](LATEST_UPDATES.md) | Current status and priorities | Project leads |
| [PHASE_2_10_ROADMAP_UPDATED.md](PHASE_2_10_ROADMAP_UPDATED.md) | Roadmap with timelines | All stakeholders |
| [PHASE_1_TODO_LIST.md](PHASE_1_TODO_LIST.md) | Immediate action items | Everyone |
| [COMPREHENSIVE_AUDIT_REPORT.md](COMPREHENSIVE_AUDIT_REPORT.md) | Full audit findings | Decision makers |
| [PROJECT_ENHANCEMENT_MASTER_INDEX.md](PROJECT_ENHANCEMENT_MASTER_INDEX.md) | Navigation and links | All stakeholders |
| [CONSOLIDATION_COMPLETE.md](CONSOLIDATION_COMPLETE.md) | Consolidation details | Documentation leads |

---

## Support & Questions

**Getting Help:**

1. **Code question?** ? Check Section 6 (Feature Implementation) for patterns
2. **Setup problem?** ? Check Section 2 (Environment Setup) or Section 5 (Troubleshooting)
3. **Test issue?** ? See Section 4 (Building & Testing)
4. **Architecture question?** ? See Section 1 (Architecture)
5. **Git workflow question?** ? See Section 3 (Development Workflow)
6. **Can't find something?** ? Use [PROJECT_ENHANCEMENT_MASTER_INDEX.md](PROJECT_ENHANCEMENT_MASTER_INDEX.md)

**Contributing Improvements:**

This manual should evolve with the project:
- Found a bug in instructions? ? Fix it directly
- New pattern discovered? ? Add to Section 6
- Common problem solved? ? Add to Section 5
- Outdated information? ? Update immediately

---

## Checklist: Before You Code

Before starting any development work, ensure:

- [ ] Virtual environment activated (\.\\.venv\\Scripts\\Activate.ps1\)
- [ ] Dependencies installed (\pip install -r requirements.txt\)
- [ ] Tests passing (\pytest tests/ -v\ - expect ~73% pass rate in Phase 2)
- [ ] Git configured (\git config user.name\ and \git config user.email\)
- [ ] Working on feature branch, not main
- [ ] You've read the relevant section in this manual
- [ ] You understand the feature requirements from PHASE_2_10_ROADMAP_UPDATED.md

---

## Checklist: Before You Commit

Before pushing code:

- [ ] All new code has docstrings (Google style)
- [ ] All new functions have type hints
- [ ] New tests written and passing
- [ ] Existing tests still passing
- [ ] Code formatted with Black (\lack . --line-length=88\)
- [ ] No linting errors (\pylint core/\)
- [ ] Commit message is descriptive and references issues
- [ ] You're on a feature branch
- [ ] You've reviewed your own changes first

---

## Phase Timeline

**Phase 1** ? COMPLETE
- Healthcare simulation: Working
- Economic projections: Working
- Chart generation: Working
- **Time spent**: ~40 hours
- **Status**: Production ready

**Phase 2** ?? IN PROGRESS (70% complete, 38-49 hours remaining)
- Social Security module: 11-17 hours remaining
- Tax reform module: 14-19 hours remaining
- Integration & testing: 13 hours remaining

**Phase 3** ?? IN PROGRESS (80% complete, 13 hours remaining)
- Discretionary spending: 13 hours remaining
- Interest rate modeling: Done
- Advanced scenarios: Done

**Phases 4-10** ?? PLANNED (154+ hours total)
- See [PHASE_2_10_ROADMAP_UPDATED.md](PHASE_2_10_ROADMAP_UPDATED.md) for details

---

## Technology Stack

**Core:**
- Python 3.8+
- NumPy / Pandas (data processing)
- Matplotlib / Plotly (visualization)

**Web:**
- Flask (REST API and UI server)
- Jinja2 (templating)
- Bootstrap (UI styling)

**Development:**
- pytest (testing)
- Black (formatting)
- Pylint (linting)
- Git (version control)

**Data:**
- JSON (policy definitions)
- CSV (scenario data)
- Excel (reports)
- HTML (interactive charts)

---

## Project Statistics

**Code Metrics:**
- 7 core modules (core/)
- 4 UI components (ui/)
- 5+ test files with 125 tests
- 40+ configuration files
- 10 core documentation files

**Quality Metrics:**
- Test coverage: 92/125 passing (73.6%)
- Code quality: GOOD
- Architecture: EXCELLENT
- Production ready: YES

**Scale:**
- 22-year projections
- 330+ million population
- Trillions in fiscal analysis
- 100+ policy scenarios possible

---

## Success Metrics for Phase 2

**Code Quality:**
- ? All new code follows Python standards
- ? Type hints on all public functions
- ? Docstrings on all classes/functions
- ? No circular dependencies
- ? <20 lines per function average

**Test Coverage:**
- Target: 95+ tests passing (75%+)
- Minimum: 90+ tests passing (70%+)
- All Phase 2 features have tests
- Integration tests verify multi-module interactions

**Documentation:**
- All new features documented in DOCUMENTATION.md
- Code comments explain "why", not "what"
- Example code provided for APIs
- Error cases documented

**Performance:**
- Simulation: <1 second per 22-year run
- Charts: <2 seconds per scenario
- Tests: <20 seconds full suite
- Memory: <200MB peak

---

**NEXT STEPS:**

1. **Today**: Review this entire manual (1-2 hours)
2. **Before coding**: Check the relevant section again (5-10 min)
3. **During development**: Reference Section 6 frequently
4. **Before committing**: Use pre-commit checklist (Before You Commit section above)
5. **When stuck**: Check Section 5 (Debugging & Troubleshooting)

---

**End of EXHAUSTIVE_INSTRUCTION_MANUAL.md**

*This is a living document. Maintain and improve it as the project evolves.*

*Last fully reviewed: December 23, 2025*  
*Status: Complete and production-ready*
