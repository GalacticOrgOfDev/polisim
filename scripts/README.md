# POLISIM Scripts Directory

This directory contains demo scripts and utilities for POLISIM (CBO 2.0).

## 📋 Quick Reference

### Phase 3 Demo Scripts (NEW! - Production-Ready)

#### 1. **demo_phase3_unified.py** - Unified Budget Projections
Demonstrates comprehensive federal budget projections with Phase 3 features.

```powershell
# Quick demo (10 years, 100 iterations)
python scripts/demo_phase3_unified.py --quick

# Full projection (30 years, 1000 iterations)
python scripts/demo_phase3_unified.py --years 30 --iterations 1000

# Compare scenarios
python scripts/demo_phase3_unified.py --scenarios baseline progressive

# Export to CSV
python scripts/demo_phase3_unified.py --scenarios baseline progressive --output results.csv
```

**Features:**
- Unified federal budget (revenues, spending, debt, interest)
- Multi-scenario comparisons
- Monte Carlo uncertainty analysis
- Healthcare integration (Medicare/Medicaid)
- Social Security projections
- Economic feedback loops

---

#### 2. **demo_phase3_validation.py** - Input Validation (Sprint 4.2)
Demonstrates input validation and safety features.

```powershell
# Run key validation examples
python scripts/demo_phase3_validation.py

# Run all validation examples
python scripts/demo_phase3_validation.py --all
```

**Features:**
- Safety #1: PDF file size limits (50MB default)
- Safety #2: Parameter range validation (20+ types)
- Scenario name validation
- Helpful error messages
- Convenience validation functions

---

#### 3. **demo_phase3_edge_cases.py** - Edge Case Handling (Sprint 4.3)
Demonstrates edge case safeguards and robustness.

```powershell
# Run key edge case examples
python scripts/demo_phase3_edge_cases.py

# Run all edge cases + integration scenario
python scripts/demo_phase3_edge_cases.py --all
```

**Features:**
- Edge Case #1: Recession GDP growth (-15% to +20% bounds)
- Edge Case #3: Extreme inflation detection
- Edge Case #8: Division by zero protection
- Edge Case #9: Extreme debt warnings (>250% GDP)
- Edge Case #10: Missing CBO data fallback (3-tier hierarchy)

---

### Phase 2 Demo Scripts

#### 4. **demo_phase2_scenarios.py** - Social Security & Tax Reform
Comprehensive Phase 2A demo with Social Security and tax reform scenarios.

```powershell
# Run baseline scenario
python scripts/demo_phase2_scenarios.py --scenarios baseline

# Compare multiple scenarios
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive moderate

# Export to CSV
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive --output results.csv
```

**Features:**
- 5 policy scenarios (baseline, progressive, moderate, revenue, climate)
- Social Security trust fund projections
- Tax reform revenue analysis
- Multi-scenario comparison
- CSV export

---

## 🛠️ Utility Scripts

### **regenerate_scenario_from_pdf.py** - Policy Parameter Extraction
Regenerates scenario JSON files from PDF policy documents with full mechanism extraction.

```powershell
# Basic usage
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf"

# Specify output
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf" -o policies/scenario.json

# With policy details
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf" --policy-name "My Policy" --policy-type USGHA
```

**See:** `README_regenerate_scenario.md` for detailed documentation

---

### **extract_policy_parameters.py** - Parameter Extraction Tool
Extracts policy parameters from PDF documents for analysis.

### **import_policies.py** - Policy Import Utility
Imports policy scenarios into the system.

### **map_parameters_to_scenario.py** - Parameter Mapping
Maps extracted parameters to scenario format.

### **visualize_*.py** - Visualization Scripts
Various visualization utilities:
- `visualize_scenarios.py` - Scenario comparison charts
- `visualize_revenue_fix.py` - Revenue mechanism visualization
- `visualize_tax_revenue.py` - Tax reform revenue charts
- `visualize_trust_fund.py` - Trust fund projections

### **run_phase2_validation.py** - Validation Runner
Runs Phase 2 validation tests against CBO/SSA baselines.

### **show_fix_summary.py** - Fix Summary Display
Displays summary of bug fixes and improvements.

---

## 📚 Documentation

For complete usage documentation, see:
- **[DEMO_SCRIPT_USAGE.md](../documentation/DEMO_SCRIPT_USAGE.md)** - Comprehensive demo guide
- **[QUICK_REFERENCE.md](../documentation/QUICK_REFERENCE.md)** - Quick reference guide
- **[README.md](../README.md)** - Main project README

---

## 🚀 Getting Started

### For New Users
Start with Phase 3 demos to see production-ready features:

```powershell
# 1. Quick unified budget demo
python scripts/demo_phase3_unified.py --quick

# 2. See input validation in action
python scripts/demo_phase3_validation.py

# 3. Explore edge case handling
python scripts/demo_phase3_edge_cases.py
```

### For Policy Analysis
Use Phase 2 scenarios for detailed policy comparisons:

```powershell
# Compare Social Security reform scenarios
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive moderate
```

### For Policy Development
Extract parameters from new policy PDFs:

```powershell
# Extract policy parameters
python scripts/regenerate_scenario_from_pdf.py "path/to/new_policy.pdf"
```

---

## 📊 What Each Demo Shows

| Demo Script | Purpose | Key Features | Runtime |
|-------------|---------|--------------|---------|
| **demo_phase3_unified.py** | Federal budget projections | Revenues, spending, debt, interest | 1-5 min |
| **demo_phase3_validation.py** | Input validation | PDF limits, parameter checking | < 1 min |
| **demo_phase3_edge_cases.py** | Edge case handling | Recession, division safety, fallbacks | < 1 min |
| **demo_phase2_scenarios.py** | Social Security + tax reform | Trust fund, tax revenue | 2-10 min |
| **regenerate_scenario_from_pdf.py** | Policy extraction | PDF → JSON scenario | 1-2 min |

---

## 🎯 Sprint 4 Features (Production-Ready)

All Phase 3 demo scripts showcase Sprint 4 improvements:

### ✅ Sprint 4.1 - Documentation
- Updated README, PHASES, CHANGELOG
- Comprehensive documentation for all features

### ✅ Sprint 4.2 - Input Validation
- PDF file size limits (Safety #1)
- Parameter range validation (Safety #2)
- 51 validation tests (100% passing)

### ✅ Sprint 4.3 - Edge Case Safeguards
- Recession GDP growth handling
- Division by zero protection
- Extreme value detection
- Missing CBO data fallback
- 50 edge case tests (100% passing)

### ✅ Sprint 4.5 - Demo Scripts (This!)
- 3 new Phase 3 demo scripts
- Comprehensive usage examples
- Production-ready demonstrations

### ⏳ Sprint 4.4 - Performance (Optional)
- Marked as optional - performance adequate
- Can revisit if bottlenecks emerge

---

## 🏆 Test Coverage

Total test suite: **413 tests passing (99.5%)**
- Phase 1: 16 tests
- Phase 2A: 87 tests
- Phase 2B: 159 tests
- Sprint 4.2: 51 validation tests
- Sprint 4.3: 50 edge case tests
- Sprint 4.5: 50 integration tests

---

## 📞 Support

Questions? Issues? Suggestions?
- 📖 Check [documentation/](../documentation/) for guides
- 🐛 Report issues in [debug.md](../documentation/debug.md)
- 💬 See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines

---

**Last Updated:** December 25, 2025 (Sprint 4.5 Complete)
