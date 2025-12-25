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

## Related Documentation
- `documentation/PHASE_4_CBO_SCRAPER_COMPLETE.md` - Phase 4 completion status
- `documentation/QUICK_REFERENCE.md` - Quick reference for polisim features
- `core/README.md` - Core module documentation
- `tests/` - Test suite for validation

## Version History
- **2025-12-24**: Initial release with Phase 2A completion
  - Social Security Monte Carlo simulation
  - Tax reform revenue analysis
  - Multi-scenario comparison
  - CSV export functionality
  - Windows compatibility (ASCII output)
