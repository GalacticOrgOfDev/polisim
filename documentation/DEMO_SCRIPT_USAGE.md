# Phase 2 Demo Script Usage

## Overview
The `demo_phase2_scenarios.py` script provides a comprehensive demonstration of Phase 2A capabilities including:
- Social Security trust fund projections with Monte Carlo simulation
- Tax reform revenue analysis (wealth, consumption, carbon, FTT)
- Combined fiscal outlook
- Multi-scenario comparison
- CSV export for further analysis

## Quick Start

### Run Baseline Scenario
```powershell
python scripts/demo_phase2_scenarios.py --scenarios baseline
```

### Run Multiple Scenarios
```powershell
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive moderate revenue climate
```

### Export Results to CSV
```powershell
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive --output results.csv
```

### Custom Projection Parameters
```powershell
python scripts/demo_phase2_scenarios.py --years 20 --iterations 100 --scenarios baseline progressive
```

## Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--years` | int | 10 | Number of years to project |
| `--iterations` | int | 100 | Monte Carlo iterations for Social Security |
| `--scenarios` | list | all | Scenarios to run (baseline, progressive, moderate, revenue, climate) |
| `--output` | path | None | CSV file path to save results |

## Available Scenarios

### 1. Baseline (Current Law)
- No reforms
- Projects current-law Social Security depletion (~2036)
- No additional tax revenue

### 2. Comprehensive Progressive Reform
- **Wealth Tax**: 2% on net worth >$50M, 3% on >$1B
- **Consumption Tax**: 10% VAT with low-income exemptions
- **Carbon Tax**: $50/ton starting, escalating 5% annually
- **Financial Transaction Tax**: 0.1% on trades

### 3. Moderate Reform Package
- **Consumption Tax**: 10% VAT
- **Carbon Tax**: $50/ton escalating
- Conservative revenue estimates

### 4. Revenue-Focused Reform
- Maximizes revenue generation
- All tax reforms enabled
- Aggressive rate structures

### 5. Climate-Focused Reform
- Emphasizes carbon pricing
- $75/ton starting rate
- 7% annual escalation

## Output Format

### Console Output
Each scenario displays:
1. **Social Security Projection**
   - Starting/ending OASI balance
   - Balance change over projection period
   - Fund status (stable/declining/depleted)

2. **Tax Reform Revenue**
   - Revenue by tax type (10-year total)
   - Total combined revenue

3. **Solvency Analysis**
   - Estimated depletion year
   - Trust fund trajectory assessment

4. **Comparison Table** (when running multiple scenarios)
   - Side-by-side trust fund status
   - Revenue comparison
   - Net fiscal impact

### CSV Export
Columns:
- `Scenario`: Scenario name
- `Final_OASI_Balance_Billions`: OASI trust fund balance at end of projection
- `Tax_Reform_Revenue_10yr_Billions`: Total tax reform revenue (10-year)

## Examples

### Basic Demonstration
```powershell
# Run baseline and progressive reform comparison
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive
```

### Long-Term Projection
```powershell
# 30-year projection with higher precision
python scripts/demo_phase2_scenarios.py --years 30 --iterations 500 --scenarios baseline progressive moderate
```

### Export for Analysis
```powershell
# Run all scenarios and export
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive moderate revenue climate --output reports/demo_comparison.csv
```

## Technical Notes

### Monte Carlo Simulation
- Social Security projections use Monte Carlo methods to capture uncertainty
- Default 100 iterations balances accuracy and performance
- Increase `--iterations` for more precise estimates (longer runtime)

### GDP Growth Assumptions
- Fixed 2.5% annual real GDP growth
- Used for revenue projections and economic scaling

### Trust Fund Mechanics
- Separate OASI and DI trust funds
- Interest credited at Treasury rates
- Payroll tax revenue calibrated to SSA baselines

### Tax Reform Models
- **Wealth Tax**: Progressive rates on ultra-high net worth
- **Consumption Tax**: VAT-style with low-income exemptions
- **Carbon Tax**: Price per ton CO2 equivalent
- **FTT**: Per-transaction percentage on financial trades

## Performance

Typical runtimes (Intel i7, 16GB RAM):
- 1 scenario, 10 years, 100 iterations: ~5 seconds
- 5 scenarios, 10 years, 100 iterations: ~20 seconds
- 1 scenario, 30 years, 500 iterations: ~15 seconds

## Troubleshooting

### Unicode Encoding Errors
Script uses ASCII-compatible output for Windows compatibility. If you see encoding errors, ensure your terminal is set to UTF-8 or use default Windows encoding.

### Memory Issues
If running out of memory with high iteration counts:
- Reduce `--iterations` (50-200 is usually sufficient)
- Reduce `--years` for initial testing
- Close other applications

### Import Errors
Ensure all Phase 2 dependencies are installed:
```powershell
pip install -r requirements.txt
```

---

## Phase 3 Demo Scripts

### 1. Unified Budget Projection Demo (`demo_phase3_unified.py`)

**Purpose**: Demonstrate the CombinedFiscalOutlookModel with unified federal budget projections.

#### Quick Start
```powershell
# Quick demo (10 years, 100 iterations)
python scripts/demo_phase3_unified.py --quick

# Full projection (30 years, 1000 iterations)
python scripts/demo_phase3_unified.py --years 30 --iterations 1000

# Compare multiple scenarios
python scripts/demo_phase3_unified.py --scenarios baseline progressive --years 20

# Export to CSV
python scripts/demo_phase3_unified.py --scenarios baseline progressive --output phase3_results.csv
```

#### Features
- ✅ Unified federal budget projections (revenues, spending, debt, interest)
- ✅ Multi-scenario comparisons
- ✅ Monte Carlo uncertainty analysis
- ✅ Healthcare integration (Medicare/Medicaid)
- ✅ Social Security projections
- ✅ Economic feedback loops

#### Output Includes
- Fiscal summary (revenues, spending, deficit, debt)
- GDP metrics and debt-to-GDP ratios
- Warning detection (high debt, large deficits, rapid growth)
- Side-by-side scenario comparison
- CSV export for further analysis

---

### 2. Input Validation Demo (`demo_phase3_validation.py`)

**Purpose**: Demonstrate input validation and safety features (Sprint 4.2).

#### Quick Start
```powershell
# Run validation examples
python scripts/demo_phase3_validation.py

# Run all validation examples (includes convenience functions)
python scripts/demo_phase3_validation.py --all
```

#### Features Demonstrated
- ✅ **Safety #1**: PDF file size limits (50MB default)
- ✅ **Safety #2**: Parameter range validation (20+ types)
- ✅ Scenario name validation
- ✅ Helpful error messages
- ✅ Convenience validation functions

#### Validated Parameters
- `years`: 1-75 years
- `iterations`: 100-50,000 Monte Carlo iterations
- `gdp_growth`: -10% to +15% (recession to boom)
- `inflation`: -5% to +25% (deflation to hyperinflation)
- `tax_rate`: 0-100%
- `spending_pct_gdp`: 0-50% of GDP
- `debt_to_gdp`: 0-500% (Japan-level debt)
- `interest_rate`: 0-25% (crisis-level rates)
- ... and 15+ more parameter types!

---

### 3. Edge Case Handling Demo (`demo_phase3_edge_cases.py`)

**Purpose**: Demonstrate edge case safeguards and robustness features (Sprint 4.3).

#### Quick Start
```powershell
# Run edge case examples
python scripts/demo_phase3_edge_cases.py

# Run all edge case examples (includes integration scenario)
python scripts/demo_phase3_edge_cases.py --all
```

#### Features Demonstrated
- ✅ **Edge Case #1**: Recession GDP growth handling (-15% to +20% bounds)
- ✅ **Edge Case #3**: Extreme inflation detection (deflation and hyperinflation)
- ✅ **Edge Case #8**: Division by zero protection
- ✅ **Edge Case #9**: Extreme debt warnings (>250% GDP)
- ✅ **Edge Case #10**: Missing CBO data fallback (3-tier hierarchy)

#### Edge Cases Handled
1. **Recession Handling**: Caps GDP growth at realistic bounds
   - Normal range: -10% to +15%
   - Extreme cap: -15% (Great Depression) to +20% (post-war boom)

2. **Division Protection**: Prevents crashes from zero denominators
   - `safe_divide()`: Returns configurable default
   - `validate_gdp()`: Enforces MIN_GDP = $1T
   - `validate_population()`: Enforces MIN_POPULATION = 1M

3. **Extreme Value Detection**: Warns for unrealistic scenarios
   - Extreme debt: >250% GDP (Japan crisis levels)
   - Deflation: <-5% (Great Depression)
   - Hyperinflation: >25% (Weimar/Zimbabwe)
   - Extreme interest: >25% (Volcker crisis)

4. **Missing Data Fallback**: Never crashes from missing CBO data
   - Tier 1: User-provided fallback (highest priority)
   - Tier 2: Cached CBO data
   - Tier 3: Hardcoded defaults (lowest priority)

#### Real-World Example
Includes 2020 COVID-19 recession scenario demonstrating:
- -10% GDP contraction handling
- Deflation detection
- High debt warnings
- Safe calculations throughout

---

## Related Documentation
- `documentation/PHASE_4_CBO_SCRAPER_COMPLETE.md` - Phase 4 completion status
- `documentation/QUICK_REFERENCE.md` - Quick reference for polisim features
- `core/README.md` - Core module documentation
- `tests/` - Test suite for validation
- `documentation/debug.md` - Sprint progress and issue tracking

## Version History
- **2025-12-25**: Phase 3 demo scripts added (Sprint 4.5)
  - Unified budget projection demo
  - Input validation demo (Sprint 4.2 features)
  - Edge case handling demo (Sprint 4.3 features)
  - Production-ready reliability demonstrations
- **2025-12-24**: Initial release with Phase 2A completion
  - Social Security Monte Carlo simulation
  - Tax reform revenue analysis
  - Multi-scenario comparison
  - CSV export functionality
  - Windows compatibility (ASCII output)

