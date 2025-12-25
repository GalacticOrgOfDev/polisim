# POLISIM: CBO 2.0

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Phase 1 Complete](https://img.shields.io/badge/Phase%201-100%25%20complete-brightgreen.svg)](documentation/PHASE_1_GAP_ANALYSIS.md)
[![Tests Passing](https://img.shields.io/badge/tests-29/29%20passing-brightgreen.svg)](tests/)
[![Bugs Fixed](https://img.shields.io/badge/bugs-18/18%20fixed-success.svg)](documentation/debug_completed_2025-12-24.md)
[![Government Grade](https://img.shields.io/badge/grade-government%20ready-lightblue.svg)](#)
[![CBO 2.0](https://img.shields.io/badge/vision-CBO%202.0-green.svg)](CBO_2_0_VISION.md)

**Open-source, transparent, stochastic U.S. federal fiscal projection system.**

## 🎯 Mission: CBO 2.0

Transform federal fiscal policy from a closed-source black box into an open, auditable, democratic tool.

**POLISIM is evolving into [CBO 2.0](CBO_2_0_VISION.md):**

- **Transparent:** Every assumption documented, configurable, sourced to official data
- **Stochastic:** Full Monte Carlo (100K+ iterations), not just point estimates
- **Credible:** Validated against CBO/SSA baselines within ±2-5%
- **Democratic:** Open source (MIT), accessible to researchers, policymakers, citizens
- **Extensible:** Modular architecture, community-driven development
- **Production Ready:** Phase 1 complete (16/16 tests passing), 18/18 bugs fixed, comprehensive error handling ✅

### Current Scope (Phase 1 ✅ + Phase 2 🚀)
- ✅ Healthcare policy modeling with context-aware mechanics (Phase 1 COMPLETE)
  - 8 policy types implemented (USGHA, Current US, M4A, UK NHS, Canada, Australia, Germany, UN)
  - Multi-year projections with economic modeling
  - Revenue breakdown and spending trajectories
  - 16 tests, 100% pass rate
- Social Security OASI/DI trust fund projections
- Federal revenue modeling (income, payroll, corporate taxes)
- Medicare/Medicaid baseline projections
- Discretionary spending (defense + non-defense)
- Interest on federal debt
- Combined 10-year budget outlook

### Roadmap (Phases 2-5)
| Phase | Timeline | Coverage |
|-------|----------|----------|
| ✅ Phase 1 | Q1-Q2 2025 | Healthcare |
| 🚀 Phase 2 | Q2-Q3 2025 | + Social Security + Revenue |
| 📋 Phase 3 | Q3-Q4 2025 | + Medicare/Medicaid + Mandatory/Discretionary + Macro |
| 📋 Phase 4 | Q4 2025-Q1 2026 | + Web UI + Data Integration + Reports |
| 📋 Phase 5 | Q1-Q2 2026 | Validation + Community + Public Launch |

[**Full CBO 2.0 Roadmap →**](CBO_2_0_ROADMAP.md)

---

## 💡 Why POLISIM?

**The Problem:** Federal fiscal decisions rely on CBO's closed-source model. Citizens, researchers, and policymakers can't independently verify assumptions or explore alternatives.

**The Solution:** An open-source fiscal projection system that makes policy costs transparent and democratizes fiscal analysis.

**Example:** Compare healthcare policies with full uncertainty quantification
```
Current approach (CBO): Spending = 12% of GDP (deterministic point estimate)
CBO 2.0 approach: Spending = 12% [10.5%-13.8%] with 90% confidence
                  → Understand the risks, not just the baseline
```

### ✅ Recent Achievement: Phase 1 Healthcare Simulation Complete (Dec 24, 2025)
Phase 1 is now **100% complete and production-ready**:
- 16/16 tests passing (100% pass rate)
- All column names standardized across context-aware and legacy paths
- 8 healthcare policy types fully implemented
- Multi-year economic projections with circuit breakers
- Comprehensive documentation and gap analysis

**Previous Achievement:** All 18 identified bugs across Phase 1 and Phase 2 have been fixed and verified:
- 4 Critical bugs (division by zero protection)
- 3 High priority bugs (array validation, trust fund handling)
- 7 Medium priority bugs (error handling, validation, logging)
- 4 Low priority bugs (code quality, documentation)

**See:** 
- [`PHASE_1_GAP_ANALYSIS.md`](documentation/PHASE_1_GAP_ANALYSIS.md) for Phase 1 completion
- [`debug_completed_2025-12-24.md`](documentation/debug_completed_2025-12-24.md) for bug fix details



---

## 🚀 Quick Start

---

## 🚀 Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim
pip install -r requirements.txt
```

### Run Your First Simulation

```bash
# Healthcare policy simulation
python run_health_sim.py

# Economic projections with Monte Carlo
python Economic_projector.py

# Generate comparison reports
python run_report.py

# Visualize scenario overlays
python run_visualize.py

# Regenerate scenario from PDF (updates funding mechanisms)
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf"
```

**Expected Output:**
- `reports/` directory with HTML charts (revenue, spending, debt scenarios)
- Excel files with Monte Carlo distributions and sensitivity analysis
- Console output with key metrics (cost savings, coverage improvements, timeline)
- JSON scenarios with complete mechanism extraction (see `scripts/README_regenerate_scenario.md`)

---

## 🤖 AI Integration (MCP Server)

**Use POLISIM as a tool in AI agents and LLMs!**

POLISIM is available as an **MCP (Model Context Protocol) Server**, enabling AI systems to run simulations, compare policies, and analyze scenarios programmatically.

### Quick Start

```bash
# Start the MCP server
python mcp_server.py

# In Claude Desktop, add to config:
# See MCP_INTEGRATION.md for full setup
```

### Available Tools for AI

- **run_simulation** - Execute Monte Carlo analysis with any policy
- **compare_scenarios** - Compare two policies side-by-side
- **sensitivity_analysis** - Analyze parameter impact on outcomes
- **get_policy_catalog** - List available policies
- **get_config_parameters** - Access configuration

### Example: Ask Claude

> "Run a 30-year Monte Carlo simulation of the United States Galactic Health Act with 50,000 iterations and show me the 95% confidence interval for debt in 2050"

Claude will automatically call POLISIM tools, analyze results, and provide insights.

**[Full MCP Integration Guide →](MCP_INTEGRATION.md)**

---

## 📊 Core Features

### Healthcare Policy Models
- **USGHA** (Your proposal - United States Galactic Health Act v0.6)
- **Current US System** (2025 baseline, 18% GDP)
- **Medicare-for-All** (12% GDP, single-payer)
- **UK NHS, Canada Single-Payer, Australia MBS, Germany Bismarck** (international benchmarks)
- **UN Proposals** (framework ready for expansion)

### Economic Modeling
- **Monte Carlo Simulations** - 100K+ iterations for robust uncertainty quantification
- **Sensitivity Analysis** - Identify key variables driving outcomes
- **Multi-Scenario Comparison** - Baseline vs. alternative vs. proposed policies
- **10-Year Economic Projections** - Revenue, spending, debt, and outcomes

### Visualization & Reporting
- **Interactive HTML Charts** - Revenue, spending, and debt-surplus scenarios
- **Histogram Distributions** - Monte Carlo spread and confidence intervals
- **PDF Reports** - Policy briefs with charts and key findings

---

## 📁 Project Structure

```
polisim/
├── core/                  # Core simulation engine
│   ├── healthcare.py     # Policy models & specifications
│   ├── economics.py      # Monte Carlo & economic engines
│   ├── comparison.py     # Scenario comparison logic
│   ├── simulation.py     # Unified simulation runner
│   ├── policy_mechanics_extractor.py  # PDF → structured data
│   └── metrics.py        # KPI calculations
├── policies/             # Policy catalogs & parameters
│   ├── catalog.json      # Policy registry
│   └── parameters.json   # Scenario configurations
├── scripts/              # Utility scripts
│   ├── regenerate_scenario_from_pdf.py  # PDF → JSON extraction
│   └── README_regenerate_scenario.md    # Script documentation
├── ui/                   # Visualization & reporting
│   ├── chart_carousel.py # Multi-scenario displays
│   └── server.py         # Future web interface
├── tests/                # pytest unit tests
├── reports/              # Generated outputs (HTML, Excel)
├── run_health_sim.py     # Healthcare simulation runner
├── run_report.py         # Report generation
├── run_visualize.py      # Visualization suite
├── Economic_projector.py  # Economic engine (Monte Carlo)
└── requirements.txt      # Python dependencies (pinned versions)
```

---

## 🔧 Configuration

All simulations are configurable via:
- **JSON configs** in `policies/` (policy parameters, scenarios)
- **Python argparse** in runner scripts (iterations, years, output options)
- **Environment variables** for batch processing (planned)

Example: Run 1M Monte Carlo iterations on custom policy:
```bash
python Economic_projector.py --iterations 1000000 --policy custom_scenario.json
```

---

## 📈 Data & Validation

- **US Government Baselines** - CMS, CBO, Census Bureau data
- **International Comparables** - OECD, WHO, national health systems
- **Real-World Projections** - Healthcare cost trends, demographic shifts
- **Tolerance Testing** - Results validated within ±2% of Excel baselines

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

Tests validate:
- Baseline vs. USGHA projections (Excel tolerance)
- Policy comparison logic
- Monte Carlo convergence
- Economic metrics accuracy

---

## 📖 Documentation

**Core Documentation** (in `documentation/` folder):
- **[00_START_HERE.md](documentation/00_START_HERE.md)** - Project overview and quick start
- **[CONTEXT_FRAMEWORK.md](documentation/CONTEXT_FRAMEWORK.md)** - Complete framework guide (extraction system)
- **[CONTEXT_FRAMEWORK_INDEX.md](documentation/CONTEXT_FRAMEWORK_INDEX.md)** - Framework quick reference
- **[QUICK_REFERENCE.md](documentation/QUICK_REFERENCE.md)** - API and usage guide
- **[EXHAUSTIVE_INSTRUCTION_MANUAL.md](documentation/EXHAUSTIVE_INSTRUCTION_MANUAL.md)** - Phase 2-10 detailed roadmap
- **[debug.md](documentation/debug.md)** - Known issues and debugging guide
- **[debug_completion_summary.md](documentation/debug_completion_summary.md)** - ⭐ December 2025 extraction overhaul (60%→100% accuracy)
- **[CHANGELOG.md](documentation/CHANGELOG.md)** - Implementation history and milestones
- **[ASSESSMENT_AUDIT.md](documentation/ASSESSMENT_AUDIT.md)** - Quality audits and validation results

**Phase Documentation:**
- **[PHASE_2_10_ROADMAP_UPDATED.md](documentation/PHASE_2_10_ROADMAP_UPDATED.md)** - Detailed phase breakdown
- **[PHASE_4_CBO_SCRAPER_COMPLETE.md](documentation/PHASE_4_CBO_SCRAPER_COMPLETE.md)** - CBO data integration

---

## 🤝 Contributing

This is a **government-grade, open-source policy simulator**. Contributions welcome:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-policy`)
3. Add tests for new functionality
4. Commit and push
5. Open a Pull Request

See [CONTRIBUTING.md](#) for detailed guidelines.

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

Permissive license enabling fork, modify, and redistribute freely—including for government/military use.

---

## 💬 Questions?

- **Open an issue** for bugs, features, or policy requests
- **Discussions** for methodology questions, model improvements, or collaboration
- **GitHub Wiki** (planned) for deeper technical docs

---

**Built with:** Python | pandas | NumPy | SciPy | Matplotlib | PyYAML

