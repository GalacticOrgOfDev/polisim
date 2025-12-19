# polisim

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Government Grade](https://img.shields.io/badge/grade-government%20ready-lightblue.svg)](#)

**A government-grade policy simulator for economic projections with Monte Carlo modeling.**

## 🎯 The Value Proposition

Expose the true cost of policy gatekeeping through **verified economic projections**. 

> Run real economic simulations that reveal hidden inefficiencies, waste, and opportunities in current policy frameworks. Compare your proposal against baseline systems, alternative policies, and international benchmarks—all with transparent Monte Carlo distributions.

**Example:** The United States Galactic Health Act (USGHA) proposal reduces healthcare spending from **18% to 9% of GDP** while achieving 99% coverage and eliminating medical bankruptcies—fully modeled and validated against real-world baselines.

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
```

**Expected Output:**
- `reports/` directory with HTML charts (revenue, spending, debt scenarios)
- Excel files with Monte Carlo distributions and sensitivity analysis
- Console output with key metrics (cost savings, coverage improvements, timeline)

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
│   └── metrics.py        # KPI calculations
├── policies/             # Policy catalogs & parameters
│   ├── catalog.json      # Policy registry
│   └── parameters.json   # Scenario configurations
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

- **[00_START_HERE.md](00_START_HERE.md)** - Project roadmap and Phase 1-10 vision
- **[CAROUSEL_QUICKSTART.md](CAROUSEL_QUICKSTART.md)** - Interactive visualization guide
- **[PHASE_2_10_ROADMAP.md](PHASE_2_10_ROADMAP.md)** - Planned features (live data, AI, Streamlit UI)

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

