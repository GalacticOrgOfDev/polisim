# 📚 POLISIM PROJECT INDEX & NAVIGATION GUIDE

**Status:** Phase 1 Complete + Phase 2 Code Quality Complete  
**Last Updated:** December 19, 2025  
**Version:** 2.0 (Government-Grade Ready)

---

## 🎯 Quick Navigation

### 👤 **New to polisim?**
1. Start → **[README.md](README.md)** (project overview)
2. Then → **[00_START_HERE.md](00_START_HERE.md)** (quickstart + roadmap)
3. Run → `python run_health_sim.py` (see it work!)

### 👨‍💻 **Developer Setup?**
1. See → **[README.md](README.md#-quick-start)** (installation)
2. Read → **[core/README.md](core/README.md)** (architecture)
3. Run → `pytest tests/ -v` (verify environment)

### 📊 **Running Simulations?**
1. Check → **[README.md](README.md#-quick-start)** (quick commands)
2. Use → **[00_START_HERE.md](00_START_HERE.md#-quick-start-30-seconds)** (literal commands)
3. Customize → **[config.yaml](config.yaml)** (parameters)
4. Compare → **[policies/](policies/)** (scenario files)

### 📈 **Understanding Results?**
1. Review → **[PHASE_1_SUMMARY.md](PHASE_1_SUMMARY.md)** (what was built)
2. Explore → **[PHASE_2_COMPLETION.md](PHASE_2_COMPLETION.md)** (quality improvements)
3. Analyze → Reports in `reports/` directory (generated charts)

---

## 📂 **Project Structure Map**

```
polisim/
├── 📖 Documentation Files
│   ├── README.md                          ★ Start here (project overview)
│   ├── 00_START_HERE.md                   ★ Quick start + 10-phase roadmap
│   ├── PHASE_1_SUMMARY.md                   Phase 1 completion details
│   ├── PHASE_2_COMPLETION.md              ★ NEW: Latest improvements
│   ├── PHASE_2_10_ROADMAP.md              Future phases (2-10)
│   ├── CAROUSEL_README.md                   Visualization features
│   └── LICENSE                            ★ MIT (open source)
│
├── ⚙️ Configuration
│   ├── config.yaml                        ★ Master parameter file
│   ├── requirements.txt                   ★ Pinned dependencies (exact versions)
│   ├── pyproject.toml                     ★ Modern Python packaging
│   ├── defaults.py                          Initial values (legacy)
│   └── current_policy.csv                   Current US system baseline
│
├── 🔧 Core Simulation Engine [core/]
│   ├── healthcare.py                      Healthcare policy models (8 policies)
│   ├── economics.py                       Economic calculations
│   ├── economic_engine.py              ★ NEW: Modularized classes
│   ├── comparison.py                      Policy comparison logic
│   ├── simulation.py                      Main simulator
│   ├── metrics.py                         KPI calculations
│   ├── policies.py                        Policy utilities
│   ├── scenario_loader.py                 Config loading
│   ├── config.py                       ★ NEW: Configuration management
│   ├── __init__.py                        Module exports
│   └── README.md                       ★ NEW: Architecture guide
│
├── 📋 Policy Data [policies/]
│   ├── catalog.json                       Policy registry
│   ├── parameters.json                    Default parameters
│   ├── galactic_health_scenario.json      USGHA scenario
│   ├── scenario_usgha_base.json        ★ NEW: Base scenario template
│   ├── scenario_usgha_conservative.json★ NEW: Conservative scenario
│   ├── comparison_baseline_vs_usgha.json★ NEW: Comparison template
│   └── README.md                       ★ NEW: Policy guide
│
├── 📊 Visualization & UI [ui/]
│   ├── chart_carousel.py                  Multi-scenario carousel
│   ├── healthcare_charts.py                Healthcare visualizations
│   ├── visualization.py                ★ NEW: Advanced charts (600 LOC)
│   ├── server.py                          Web interface (planned)
│   ├── widgets.py                         Reusable components
│   ├── __init__.py                        Module exports
│   └── README.md                       ★ NEW: UI roadmap
│
├── 🛠️ Utilities [utils/]
│   ├── io.py                           ★ ENHANCED: I/O + error handling
│   ├── logging_config.py               ★ NEW: Centralized logging
│   ├── __init__.py                        Module exports
│   └── README.md                       ★ NEW: Utilities guide
│
├── 🧪 Tests [tests/]
│   ├── test_economic_engine.py          ★ NEW: 500 LOC, 20+ cases
│   ├── test_simulation_healthcare.py    ★ ENHANCED: 400 LOC, 15+ cases
│   ├── test_comparison.py                 Comparison tests
│   ├── __pycache__/                       Compiled bytecode
│   └── README.md                       ★ NEW: Testing guide
│
├── 🚀 Runner Scripts (Entry Points)
│   ├── run_health_sim.py               ★ ENHANCED: + logging/errors
│   ├── run_report.py                      Report generation
│   ├── run_visualize.py                   Visualization runner
│   ├── run_compare_and_export.py          Comparison runner
│   ├── Economic_projector.py              Main GUI app
│   └── main.py                            Entry point
│
└── 📤 Generated Output
    └── reports/                         HTML charts, Excel files
```

---

## 📖 **Documentation Guide**

### **For Everyone**

| Document | Purpose | Time |
|----------|---------|------|
| **[README.md](README.md)** | Project overview, features, value prop | 5 min |
| **[00_START_HERE.md](00_START_HERE.md)** | Setup, first simulation, 10-phase plan | 10 min |
| **[LICENSE](LICENSE)** | MIT license (open source, fork-friendly) | 2 min |

### **For Developers**

| Document | Purpose | Time |
|----------|---------|------|
| **[core/README.md](core/README.md)** | Simulation engine architecture | 10 min |
| **[policies/README.md](policies/README.md)** | Policy definitions & scenarios | 8 min |
| **[ui/README.md](ui/README.md)** | Visualization & UI components | 8 min |
| **[tests/README.md](tests/README.md)** | Testing strategy & pytest | 8 min |
| **[PHASE_2_COMPLETION.md](PHASE_2_COMPLETION.md)** | Recent improvements (detailed) | 20 min |

### **For Project Managers**

| Document | Purpose | Time |
|----------|---------|------|
| **[PHASE_1_SUMMARY.md](PHASE_1_SUMMARY.md)** | What Phase 1 delivered | 15 min |
| **[PHASE_2_COMPLETION.md](PHASE_2_COMPLETION.md)** | What Phase 2 improved | 15 min |
| **[PHASE_2_10_ROADMAP.md](PHASE_2_10_ROADMAP.md)** | Phases 2-10 timeline | 20 min |

---

## 🚀 **Quick Commands**

### **Setup**
```bash
# Clone repository
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim

# Install dependencies
pip install -r requirements.txt
```

### **Run Simulations**
```bash
# Healthcare simulation (USGHA)
python run_health_sim.py

# Economic projections (Monte Carlo)
python Economic_projector.py

# Generate reports
python run_report.py

# Visualize results
python run_visualize.py
```

### **Development**
```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html

# Enable verbose logging
python run_health_sim.py --verbose

# Use custom scenario
python run_health_sim.py --scenario policies/scenario_usgha_conservative.json
```

---

## 📊 **Key Features**

### ✅ **Phase 1: Foundation (Complete)**
- 8 healthcare policy models
- Healthcare simulation engine
- Monte Carlo economics
- Policy comparison framework
- Interactive chart carousel
- 530+ lines of core code
- Professional documentation

### ✅ **Phase 2: Code Quality (Complete - NEW!)**
- Modularized economic engine (600 LOC)
- Comprehensive logging throughout
- 35+ unit tests (1500 LOC)
- Configuration management (YAML/JSON)
- Advanced visualization (600 LOC)
- MIT License
- Exact dependency pinning
- Error handling & validation
- This index + comprehensive READMEs

### 🚀 **Phases 3-10: Planned**
- Interactive web UI (Streamlit/Dash)
- Live policy data integration
- Generative AI reports
- FastAPI + React architecture
- GitHub Actions CI/CD
- Production deployment

---

## 💡 **Common Tasks**

### **I want to...**

<details>
<summary><b>Run a simulation</b></summary>

```bash
# Basic USGHA simulation
python run_health_sim.py

# Custom scenario with high inflation
python run_health_sim.py --scenario policies/scenario_usgha_conservative.json

# Extended 50-year projection
python run_health_sim.py --years 50
```

See: [00_START_HERE.md](00_START_HERE.md#-quick-start-30-seconds)
</details>

<details>
<summary><b>Compare policies</b></summary>

Check policy comparison logic in [core/comparison.py](core/comparison.py) and run via:
```bash
python run_visualize.py  # Interactive carousel
python run_report.py      # Excel export with summaries
```

See: [policies/README.md](policies/README.md)
</details>

<details>
<summary><b>Add a new policy</b></summary>

1. Define in [core/healthcare.py](core/healthcare.py) (data class + factory method)
2. Add to [policies/catalog.json](policies/catalog.json)
3. Test via `pytest tests/`

See: [core/README.md](core/README.md#adding-new-policies)
</details>

<details>
<summary><b>Change parameters</b></summary>

Edit [config.yaml](config.yaml) or pass `--scenario custom.json`:

```json
{
  "economic_parameters": {
    "gdp_growth_rate": 0.015,
    "inflation_rate": 0.05
  }
}
```

See: [core/config.py](core/config.py)
</details>

<details>
<summary><b>Create a visualization</b></summary>

Use [ui/visualization.py](ui/visualization.py):

```python
from ui.visualization import SimulationVisualizer

viz = SimulationVisualizer()
fig = viz.plot_scenario_overlay(scenarios, metric='Debt')
fig.savefig('comparison.png')
```

See: [ui/README.md](ui/README.md)
</details>

<details>
<summary><b>Run tests</b></summary>

```bash
pytest tests/                              # All tests
pytest tests/test_economic_engine.py -v   # Specific file
pytest tests/ -k "sensitivity"             # By name pattern
pytest tests/ --cov=core                   # With coverage
```

See: [tests/README.md](tests/README.md)
</details>

<details>
<summary><b>Debug an issue</b></summary>

```bash
# Enable verbose logging
python run_health_sim.py --verbose

# Run with Python debugger
python -m pdb run_health_sim.py

# Check specific module
python -c "from core import get_policy_by_type; print(get_policy_by_type('USGHA'))"
```

See: [PHASE_2_COMPLETION.md](PHASE_2_COMPLETION.md#-error-handling--logging-)
</details>

---

## 🏛️ **Project Statistics**

| Metric | Value |
|--------|-------|
| **Total Lines of Code** | 2,200+ |
| **Test Coverage** | 35+ test cases |
| **Documented Classes** | 15+ |
| **Configuration Options** | 50+ |
| **Supported Policies** | 8 |
| **Visualization Types** | 5+ |
| **Python Version** | 3.9+ |
| **License** | MIT (Open Source) |
| **Current Phase** | 2 of 10 (20%) |

---

## 🔗 **External Links**

- **GitHub:** https://github.com/GalacticOrgOfDev/polisim
- **License:** [MIT License](LICENSE)
- **Python Docs:** https://docs.python.org/3.9/
- **Pytest:** https://docs.pytest.org/
- **Matplotlib:** https://matplotlib.org/

---

## 📞 **Support & Contribution**

### **Questions?**
1. Check the relevant README.md
2. Review [00_START_HERE.md](00_START_HERE.md)
3. Look at example scenarios in [policies/](policies/)
4. Search test files for usage examples

### **Found a bug?**
1. Create a GitHub issue with:
   - Steps to reproduce
   - Error message/traceback
   - Python version and OS
2. Check [PHASE_2_COMPLETION.md](PHASE_2_COMPLETION.md#-error-handling--logging-) for logging tips

### **Want to contribute?**
1. Fork the repository
2. Create a feature branch
3. Add tests (see [tests/README.md](tests/README.md))
4. Submit a pull request
5. Read [00_START_HERE.md](00_START_HERE.md) for governance

---

## 📋 **Checklist for New Developers**

- [ ] Read [README.md](README.md) (5 min)
- [ ] Run `pip install -r requirements.txt`
- [ ] Run `python run_health_sim.py` (verify installation)
- [ ] Run `pytest tests/ -v` (verify tests pass)
- [ ] Read [core/README.md](core/README.md) (understand architecture)
- [ ] Explore [policies/](policies/) (understand data format)
- [ ] Run `python -c "from core import get_policy_by_type; print(get_policy_by_type('USGHA'))"` (verify API)
- [ ] Review [PHASE_2_COMPLETION.md](PHASE_2_COMPLETION.md) (understand recent work)

---

**Last Updated:** December 19, 2025  
**Maintained by:** GitHub Copilot + Development Team  
**Status:** ✅ Government-Grade Ready (Phase 2 Complete)

