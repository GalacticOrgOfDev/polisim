# POLISIM: Open-Source Federal Fiscal Policy Simulator

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-417/419%20passing-brightgreen.svg)](tests/)
[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)](documentation/VALIDATION_REPORT_DEC26.md)
[![Documentation](https://img.shields.io/badge/docs-comprehensive-blue.svg)](documentation/INDEX.md)

> **An open-source, transparent, stochastic U.S. federal fiscal projection system that democratizes policy analysis.**

Polisim enables researchers, policymakers, and citizens to independently model and verify the fiscal impacts of policy proposals—transforming federal budget analysis from a closed-source black box into an open, auditable, democratic tool.

## 🛰️ Project Status

- **Current:** Phase 7.3 (PoliSim Chatroom) — Action Buttons complete, UI next
- **Complete:** Phases 1-6.3, Slice 7.1.1-7.1.4, Slice 7.2.1-7.2.2, Slice 7.3.1-7.3.2 ✅ (see [docs/PHASES.md](docs/PHASES.md) for full roadmap)
- **Next:** Slice 7.3.3 (Chat UI) — Streamlit sidebar component

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
- **Multi-Agent Swarm Analysis** - 🆕 AI agents collaborate, debate, and reach consensus on policy impacts
- **Multi-Scenario Comparison** - Side-by-side policy analysis with confidence intervals
- **Sensitivity Analysis** - Identify key drivers of fiscal outcomes
- **Edge Case Handling** - Recession scenarios, extreme debt, missing data fallbacks
- **Input Validation** - Comprehensive parameter checking with helpful error messages
- **Performance Optimized** - Vectorized operations, component caching (42% faster)

### Policy Analysis Tools
- **Context-Aware Extraction** - PDF policy documents → structured mechanisms
- **Baseline Validation** - Automated comparison against CBO/SSA/CMS projections
- **Interactive Dashboard** - Streamlit web interface with educational tooltips
- **Scenario Bundles** - Save/load custom policy bundles, diff parameters, export zip bundles and report-ready comparison CSV/JSON
- **AI Integration** - MCP server for Claude/LLM-powered analysis
- **Report Generation** - HTML charts, CSV exports, comprehensive metrics

---

## 🚀 Quick Start

### Installation

```powershell
# Clone repository
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim

# Recommended: Use the launcher (validates dependencies automatically)
python launcher.py
```

### Launcher (Recommended ✅)

The **launcher** is the recommended way to start PoliSim:

```powershell
python launcher.py
```

**Benefits:**
- ✅ Validates all dependencies before starting
- ✅ Checks CBO data ingestion and API prerequisites  
- ✅ Auto-installs missing packages (with your approval)
- ✅ Non-blocking UI - no freezing during operations
- ✅ Real-time activity log with timestamps
- ✅ One-click access to Dashboard, API, or MCP Server

See [docs/LAUNCHER_GUIDE.md](docs/LAUNCHER_GUIDE.md) for full documentation.

### Alternative Setup Methods

```powershell
# Manual installation (advanced users)
pip install -r requirements.txt
python main.py --startup-check-only  # Important: validate dependencies
streamlit run ui/dashboard.py        # Start dashboard
```

### Friendly Startup Check

- Run dependency + data ingestion check: `python main.py --startup-check-only` (adds `--auto-install-deps` to skip prompts). Reports CBO data source, cache use, freshness hours, and checksum.
- The installer/launcher plan is outlined in [docs/startup_check_plan.md](docs/startup_check_plan.md).
- Windows one-liner bootstrap: `powershell -ExecutionPolicy Bypass -File scripts/bootstrap_windows.ps1 -LaunchDashboard` (downloads embeddable Python if needed, builds venv, installs deps, runs startup check, then launches Streamlit).
- Launcher shell (Windows, Tk-based): `python launcher.py` (cyberpunk splash, calls bootstrap for install + launch, opens mobile links).

### Run Example Simulations

```powershell
# Unified budget projection (revenues, spending, debt, interest)
python scripts/demo_phase3_unified.py --years 30 --iterations 1000

# Compare policy scenarios (baseline vs. progressive vs. moderate)
python scripts/demo_phase2_scenarios.py --scenarios baseline progressive moderate

# Social Security trust fund analysis (75-year projection)
python scripts/demo_phase2_scenarios.py --scenarios baseline --years 75

# Healthcare policy simulation
python scripts/run_health_sim.py

# Generate comparison reports
python scripts/run_report.py

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

## � Public API (Slice 5.7)

**Programmatic access to simulations, scenarios, and policy analysis.**

The REST API enables external applications and services to leverage POLISIM's fiscal modeling capabilities.

### Quick Start

```bash
# Start the API server
python api/rest_server.py

# Endpoint base URL
BASE_URL = http://localhost:5000/api/v1
```

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/simulate` | POST | Run Monte Carlo policy simulation |
| `/v1/scenarios` | GET | List available policy scenarios |
| `/v1/data/ingestion-health` | GET | Check CBO data status (source, freshness, schema) |

### Example Usage

```bash
# Run simulation via curl
curl -X POST http://localhost:5000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Tax Reform 2025",
    "revenue_change_pct": 10.5,
    "spending_change_pct": -5.0,
    "years": 10,
    "iterations": 5000
  }'

# List scenarios
curl http://localhost:5000/api/v1/scenarios?filter_type=baseline&page=1&per_page=20

# Check data ingestion status
curl http://localhost:5000/api/v1/data/ingestion-health
```

### Configuration Flags

Control API behavior via environment variables:

```bash
# Authentication & Rate Limiting
PUBLIC_API_ENABLED=true              # Enable/disable public endpoints
API_REQUIRE_AUTH=false               # Require auth (default: optional)
API_RATE_LIMIT_ENABLED=false         # Enable rate limiting
API_RATE_LIMIT_PER_MINUTE=60         # Requests per minute limit
API_MAX_PAYLOAD_MB=10                # Max request size (MB)
API_TIMEOUT_SECONDS=300              # Request timeout

# Versioning
API_VERSION=1.0                      # Current API version
```

### Features

- **Versioned Endpoints** - `/api/v1/` with clear upgrade paths
- **Request Validation** - Pydantic models enforce schema compliance
- **Rate Limiting** - Optional per-user/key throttling
- **Auth Toggle** - API key or JWT (optional, configurable)
- **Structured Errors** - Consistent error format with field-level details
- **Observability** - Structured JSON logging, metrics collection, SLO tracking
- **Request Tracing** - X-Request-ID header for debugging

### Full Documentation

**[API Contract & Reference →](docs/SLICE_5_7_API_CONTRACT.md)**

**[API Test Suite →](tests/test_slice_5_7_api.py)**

---

## �🎨 Interactive Web Dashboard

Launch the Streamlit interface for interactive analysis:

```powershell
streamlit run ui/dashboard.py
# or
python scripts/run_dashboard.py --port 8501
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
├── tests/                # Comprehensive test suite (419 tests; 417 passing)
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
- [API Quick Start](docs/API_QUICK_START.md) - 5-minute API tutorial
- [FAQ](FAQ.md) - Frequently asked questions (20+ Q&A)
- [Glossary](docs/GLOSSARY.md) - 120+ term definitions
- [Sprint 5.4 Slice Work Plan](docs/slice%2054%20work%20plan.md) - Current UI enhancement tasks

**Slice 5.7 (Public API & Hardening):**
- [API Contract & Reference](docs/SLICE_5_7_API_CONTRACT.md) - Versioned endpoints, schemas, auth, rate limits, SLOs
- [API Test Suite](tests/test_slice_5_7_api.py) - Integration and contract tests
- [v1 Middleware](api/v1_middleware.py) - Auth, rate limiting, validation, observability
- [Observability Guide](api/observability.py) - Logging, metrics, SLO reporting

**Phase 6.2 (Security Hardening):**
- [Security Policy](docs/SECURITY.md) - Comprehensive security policy (v2.0)
- [Security Hardening Guide](docs/PHASE_6_2_SECURITY_HARDENING_GUIDE.md) - CORS, security headers, input validation, rate limiting
- [Security Audit Report](docs/PHASE_6_2_SECURITY_AUDIT_REPORT.md) - CVE findings, remediation plan, compliance checklist
- [DDoS Protection Quick Start](docs/PHASE_6_2_5_QUICK_START.md) - Rate limiting, circuit breakers, backpressure
- [Implementation Summary](docs/PHASE_6_2_IMPLEMENTATION_SUMMARY.md) - Phase 6.2 delivery summary
- [Incident Response](docs/INCIDENT_RESPONSE.md) - 5-phase incident response procedures
- [Monitoring & Compliance](docs/MONITORING_COMPLIANCE.md) - Metrics, alerting, compliance
- [Tabletop Exercise](docs/TABLETOP_EXERCISE_SCENARIO.md) - Incident response dry-run scenario

**Phase 6.3 (Public Documentation):**
- [Contributing Guide](CONTRIBUTING.md) - Code style, workflow, community guidelines
- [FAQ](FAQ.md) - 20+ frequently asked questions with detailed answers
- [API Quick Start](docs/API_QUICK_START.md) - Get started with the API in 5 minutes
- [Glossary](docs/GLOSSARY.md) - 120+ economic and policy terms defined

**Technical:**
- [Context Framework](documentation/CONTEXT_FRAMEWORK.md) - Policy extraction system
- [Unified Extraction Architecture](docs/UNIFIED_EXTRACTION_ARCHITECTURE.md) - Multi-domain policy analysis (healthcare, tax, social security, spending)
- [Extraction Implementation Complete](docs/EXTRACTION_IMPLEMENTATION_COMPLETE.md) - Status report, test results, integration guide
- [Type Hints Guide](documentation/TYPE_HINTS_GUIDE.md) - Code standards
- [Naming Conventions](documentation/NAMING_CONVENTIONS.md) - Style guide
- [Theme System](documentation/THEME_SYSTEM.md) - Consolidated themes, fixes, and testing
- [Phase 5 Slice Plan](docs/phase%205%20slices.md) - Remaining Phase 5 slices and exit checklist
- [Ingestion Health Endpoint](docs/ingestion_health_endpoint.md) - API checksum/freshness/schema status (optional auth + rate-limit flags)

**Reference:**
- [Changelog](documentation/CHANGELOG.md) - Version history
- [Project Phases](docs/PHASES.md) - Roadmap
- [Validation Report](documentation/VALIDATION_REPORT_DEC26.md) - System health (A+ grade, 417/419 tests passing)

---

## 🧪 Testing

```powershell
# Run full test suite (419 tests; 417 passing)
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

**📚 Essential Reading:**
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute: bug reports, features, code style, workflow
- **[Code of Conduct](CODE_OF_CONDUCT.md)** - Community guidelines and expectations
- **[Security Policy](docs/SECURITY.md)** - Report vulnerabilities responsibly
- **[FAQ](FAQ.md)** - Frequently asked questions (20+ Q&A)

**Quick Start:**
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

**Community Resources:**
- **[FAQ](FAQ.md)** - Quick answers to common questions
- **[Glossary](docs/GLOSSARY.md)** - Comprehensive term definitions (120+ terms)
- **[API Quick Start](docs/API_QUICK_START.md)** - Get started with the API in 5 minutes
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project

**Get Help:**
- **Issues:** Bug reports, feature requests, policy suggestions
- **Discussions:** Methodology questions, model improvements, collaboration
- **Email:** galacticorgofdev@gmail.com
- **Security:** See [SECURITY.md](docs/SECURITY.md) for responsible disclosure

**Built with rigor. Validated with 417/419 tests. Ready for policy analysis at scale.**

---

**Built with:** Python | pandas | NumPy | SciPy | Matplotlib | PyYAML

