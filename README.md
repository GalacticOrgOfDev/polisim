# POLISIM: Open-Source Federal Fiscal Policy Simulator

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-417/419%20passing-brightgreen.svg)](tests/)
[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)](documentation/VALIDATION_REPORT_DEC26.md)
[![Documentation](https://img.shields.io/badge/docs-comprehensive-blue.svg)](documentation/INDEX.md)

> **An open-source, transparent, stochastic U.S. federal fiscal projection system that democratizes policy analysis.**

Polisim enables researchers, policymakers, and citizens to independently model and verify the fiscal impacts of policy proposals—transforming federal budget analysis from a closed-source black box into an open, auditable, democratic tool.

## 🎯 Core Purpose

**The Problem:** Federal fiscal decisions rely on closed-source models. Citizens, researchers, and policymakers can't independently verify assumptions or explore policy alternatives.

**The Solution:** An open-source fiscal projection system that:

- **🔍 Transparent:** Every assumption documented, configurable, and sourced to official CBO/SSA/CMS data
- **📊 Stochastic:** Monte Carlo simulations (100K+ iterations) with full uncertainty quantification
- **✅ Validated:** Projections validated against government baselines (CBO, SSA, CMS) within ±2-5%
- **🌐 Democratic:** Open source (MIT license), accessible to everyone
- **🔧 Extensible:** Modular architecture enables community contributions
- **🚀 Production Ready:** 417/419 tests passing, comprehensive error handling, optimized performance

## 💡 Why Uncertainty Matters

**Traditional approach (CBO):** Deterministic point estimates
```
Healthcare Spending = 12% of GDP
```

**Polisim approach:** Full probability distributions
```
Healthcare Spending = 12% of GDP [10.5%-13.8% 90% CI]
→ Understand the risks, not just the baseline
→ Quantify policy uncertainty for better decisions
```

Monte Carlo simulations reveal how economic shocks, demographic changes, and parameter uncertainty affect long-term fiscal outcomes—critical for resilient policy design.

---

## 🎨 Key Features

### Federal Budget Modeling
- **Unified Budget Projections** - Revenue, spending, debt, interest over 10-75 years
- **Social Security** - OASI/DI trust fund projections with reform scenarios
- **Medicare/Medicaid** - Enrollment, spending, and trust fund modeling
- **Federal Revenue** - Individual income, payroll, corporate taxes with elasticities
- **Discretionary Spending** - Defense and non-defense baseline and scenarios
- **Healthcare Policy** - 8 policy types with context-aware mechanism extraction
- **Tax Reform Analysis** - Wealth, consumption, carbon, financial transaction taxes

### Advanced Capabilities
- **Monte Carlo Simulations** - 100K+ iterations for robust uncertainty quantification
- **Stochastic Modeling** - Economic shocks, parameter uncertainty, policy interactions
- **Multi-Scenario Comparison** - Side-by-side policy analysis with confidence intervals
- **Sensitivity Analysis** - Identify key drivers of fiscal outcomes
- **Edge Case Handling** - Recession scenarios, extreme debt, missing data fallbacks
- **Input Validation** - Comprehensive parameter checking with helpful error messages
- **Performance Optimized** - Vectorized operations, component caching (42% faster)

### Policy Analysis Tools
- **Context-Aware Extraction** - PDF policy documents → structured mechanisms
- **Baseline Validation** - Automated comparison against CBO/SSA/CMS projections
- **Interactive Dashboard** - Streamlit web interface with educational tooltips
- **AI Integration** - MCP server for Claude/LLM-powered analysis
- **Report Generation** - HTML charts, CSV exports, comprehensive metrics

---

## 🚀 Quick Start

### Installation

```powershell
# Clone and install
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim
pip install -r requirements.txt
```

### Run Example Simulations

```powershell
# Unified budget projection (revenues, spending, debt, interest)
python scripts/demo_phase3_unified.py --years 30 --iterations 1000

# Compare policy scenarios (baseline vs. progressive vs. moderate)
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive moderate

# Social Security trust fund analysis (75-year projection)
python scripts/demo_phase2_scenarios.py --scenarios baseline --years 75

# Healthcare policy simulation
python run_health_sim.py

# Generate comparison reports
python run_report.py

# Regenerate scenario from PDF policy document
python scripts/regenerate_scenario_from_pdf.py "path/to/policy.pdf"
```

**Expected Output:**
- Interactive HTML charts (revenue, spending, debt, trust funds)
- CSV files with Monte Carlo distributions and confidence intervals
- Console metrics (key fiscal indicators, warnings, summary statistics)
- JSON scenarios with structured policy mechanisms

**[Full Demo Guide →](documentation/DEMO_SCRIPT_USAGE.md)**

---

## 🤖 AI Integration (MCP Server)

**Use POLISIM as a tool in AI agents and LLMs.**

POLISIM implements the **Model Context Protocol (MCP)**, enabling AI systems to run simulations, compare policies, and analyze scenarios programmatically.

### Quick Start

```bash
# Start the MCP server
python mcp_server.py

# Configure Claude Desktop (see MCP_INTEGRATION.md)
```

### Available Tools

- **run_simulation** - Execute Monte Carlo analysis with any policy
- **compare_scenarios** - Compare two policies side-by-side
- **sensitivity_analysis** - Analyze parameter impact on outcomes
- **get_policy_catalog** - List available policies
- **get_config_parameters** - Access configuration

### Example Query for Claude

> "Run a 30-year Monte Carlo simulation of the United States Galactic Health Act with 50,000 iterations and show me the 95% confidence interval for debt in 2050"

**[Full MCP Integration Guide →](MCP_INTEGRATION.md)**

---

## 🎨 Interactive Web Dashboard

Launch the Streamlit interface for interactive analysis:

```powershell
streamlit run ui/dashboard.py
```

**Dashboard Features:**
- **Social Security Projections** - Trust fund analysis with Monte Carlo uncertainty bands
- **Federal Revenue Modeling** - Income, payroll, and corporate tax projections
- **Healthcare Policy Analysis** - Compare 8+ healthcare systems
- **Medicare/Medicaid Outlays** - Long-term spending projections
- **Combined Fiscal Outlook** - Unified 10-75 year budget analysis
- **Policy Comparison Tools** - Side-by-side scenario analysis
- **Educational Tooltips** - Context-aware explanations throughout (toggle on/off)
- **Comprehensive Glossary** - 30+ technical term definitions
- **User Settings** - Customize display preferences, chart themes, decimal places

---

## 🏛️ Supported Policy Types

**Healthcare Systems:**
- United States Galactic Health Act (USGHA)
- Medicare-for-All (M4A)
- Current US System
- International Benchmarks (UK NHS, Canada Single-Payer, Australia MBS, Germany Bismarck)

**Tax Reform:**
- Wealth Tax
- Consumption Tax (VAT)
- Carbon Tax
- Financial Transaction Tax

**Social Security:**
- Trust Fund Solvency Analysis
- Payroll Tax Reform
- Full Retirement Age (FRA) Adjustments
- Benefit Structure Changes
- COLA Modifications

**Federal Budget:**
- Unified Revenue/Spending Projections
- Discretionary Spending Analysis
- Interest on Debt Modeling
- Medicare/Medicaid Outlays
- Long-term Fiscal Outlook (10-75 years)

---
---

## 📁 Project Structure

```
polisim/
├── core/                  # Core simulation engine
│   ├── simulation.py      # Main simulation runner
│   ├── economics.py       # Monte Carlo & economic engines
│   ├── healthcare.py      # Healthcare policy models
│   ├── revenue_modeling.py   # Tax revenue projections
│   ├── social_security.py    # Trust fund analysis
│   ├── medicare_medicaid.py  # Medicare/Medicaid modeling
│   ├── policy_mechanics_extractor.py  # PDF → structured data
│   └── comparison.py      # Scenario comparison
├── policies/             # Policy definitions & scenarios
├── scripts/              # Analysis & utility scripts
├── ui/                   # Streamlit dashboard
├── tests/                # Comprehensive test suite (417+ tests)
├── documentation/        # Technical guides & references
└── reports/              # Generated outputs (HTML, CSV, charts)
```

---

## 📖 Documentation

**[Complete Documentation Index →](documentation/INDEX.md)**

**Getting Started:**
- [Quick Reference Guide](documentation/QUICK_REFERENCE.md) - API and usage
- [Demo Scripts Guide](documentation/DEMO_SCRIPT_USAGE.md) - Example simulations
- [MCP Integration Guide](MCP_INTEGRATION.md) - AI agent integration

**Technical:**
- [Context Framework](documentation/CONTEXT_FRAMEWORK.md) - Policy extraction system
- [Type Hints Guide](documentation/TYPE_HINTS_GUIDE.md) - Code standards
- [Naming Conventions](documentation/NAMING_CONVENTIONS.md) - Style guide

**Reference:**
- [Changelog](documentation/CHANGELOG.md) - Version history
- [Project Phases](documentation/PHASES.md) - Roadmap

---

## 🧪 Testing

```powershell
# Run full test suite (417+ tests)
pytest tests/

# Run with coverage report
pytest tests/ --cov=core --cov-report=html

# Run specific test categories
pytest tests/test_economic_engine.py
pytest tests/test_revenue_modeling.py
pytest tests/test_medicare_medicaid.py
```

Comprehensive test coverage validates:
- Economic engine accuracy (24 tests)
- Revenue modeling (25 tests)
- Input validation (51 tests)
- Edge case handling (50 tests)
- Medicare/Medicaid projections (20 tests)
- Context-aware column naming (2 tests)
- Monte Carlo convergence
- Multi-scenario comparisons

---

## 🤝 Contributing

Contributions welcome! This is government-grade open-source policy infrastructure.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-policy`)
3. Add tests for new functionality (maintain >99% passing rate)
4. Follow coding standards ([documentation/NAMING_CONVENTIONS.md](documentation/NAMING_CONVENTIONS.md))
5. Commit changes and push to your fork
6. Open a Pull Request with clear description

**Priority Areas:**
- New policy type implementations
- International health system models
- Performance optimizations
- Documentation improvements

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

Permissive license enabling fork, modify, and redistribute freely—including for government/military/commercial use.

---

## 💬 Questions & Support

- **Issues:** Bug reports, feature requests, policy suggestions
- **Discussions:** Methodology questions, model improvements, collaboration
- **Email:** galacticorgofdev@gmail.com

**Built with rigor. Validated with 417+ tests. Ready for policy analysis at scale.**

---

**Built with:** Python | pandas | NumPy | SciPy | Matplotlib | PyYAML

