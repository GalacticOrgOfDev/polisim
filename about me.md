# About PoliSim

> PoliSim — a lightweight, reproducible policy simulation and analysis toolkit focused on healthcare economics, microsimulation, and scenario comparison.

---

## Quick Snapshot

- **Project name:** PoliSim
- **Purpose:** Simulate healthcare policy scenarios, compare outcomes (spending, revenue, debt/surplus), and produce publication-ready charts and reports.
- **Language / Platform:** Python 3.x
- **Repository layout:** core (models & simulation), ui (visualization & server), reports (outputs & charts), utils (I/O helpers)
- **Primary audience:** Policy researchers, data scientists, public health analysts, educators.

---

## Elevator Pitch

PoliSim provides reusable simulation pipelines and visualization tools to evaluate healthcare policies. It emphasizes reproducibility, transparency, and easy-to-run scenario comparisons so researchers and policy teams can iterate quickly and produce shareable results.

---

## Key Features

- Scenario-based microsimulation for healthcare financing and outcomes
- Modular architecture separating model logic, simulation runner, and reporting
- CSV/JSON input support and opinionated default scenarios for quick starts
- Auto-generated charts and comparison reports (see `reports/charts/`)
- Command-line runners for common workflows (`run_simulation`, `run_compare_and_export`, `run_visualize`)
- Test suite for core components (`tests/`)

---

## What PoliSim Solves

- Allows analysts to create and compare policy scenarios (e.g., baseline vs. reform) with reproducible inputs.
- Bridges domain modeling and presentation by producing tables, interactive charts, and static HTML summaries.
- Helps non-technical stakeholders consume results through pre-built visualization routes and packaged reports.

---

## Architecture Overview

- `core/` — Model definitions, simulation engine, economics and healthcare modules.
- `ui/` — Chart generation, carousel viewer, and a lightweight server for local exploration.
- `reports/` — Rendered HTML charts and packaged summaries for distribution.
- `utils/` — Input/output utilities, parsing, and small helpers.
- Top-level scripts: `main.py`, `run_simulation_healthcare.py`, `run_compare_and_export.py`, `run_visualize.py` to orchestrate common tasks.

---

## Installation

Prerequisites: Python 3.9+ (3.10/3.11 recommended). Install dependencies from `requirements.txt`.

PowerShell example:

```powershell
python -m venv .venv
; .\.venv\Scripts\Activate.ps1
; python -m pip install --upgrade pip
; pip install -r requirements.txt
```

---

## Quick Start — Run a Simulation

1. Activate your virtualenv (see above).
2. Run a built-in scenario from the project root:

```powershell
python run_health_sim.py
```

3. Compare scenarios and export charts:

```powershell
python run_compare_and_export.py
```

4. Open generated reports in `reports/charts/` or `reports/package/charts/`.

---

## Inputs & Outputs

- Inputs: CSV files (example: `usgha_simulation_22y.csv`) and optional policy parameter files.
- Outputs: HTML charts, CSV result tables, and packaged markdown summaries suitable for publication (see `reports/`).

---

## Configuration

- Defaults and configurable parameters are defined in `defaults.py` and CLI scripts accept file-based overrides.
- For reproducibility, keep parameter files under version control and record the commit hash used for any published result.

---

## Development & Testing

- Run unit tests:

```powershell
python -m pytest -q
```

- Linting and basic static checks should be run locally if configured (pre-commit hooks may be optional).

- Project structure for contributors:
  - Work on feature branches
  - Add tests for new behavior in `tests/`
  - Open PRs and request reviews

---

## Notable Modules

- `core.simulation` — orchestrates model execution and time-stepping
- `core.economics` — fiscal calculations and budget projections
- `core.healthcare` — domain-specific health assumptions and population flows
- `ui.healthcare_charts` — chart definitions used across reports

---

## Example Use Cases

- Policy comparison: Baseline vs. Universal coverage reform
- Financial forecasting: Multi-year revenue and spending projections
- Teaching: Use as a hands-on tool for courses on health economics

---

## Roadmap & Known Limitations

- Roadmap:
  - Improve modular plugin system for new policy modules
  - Add parameter sensitivity analysis tooling
  - Containerized examples for reproducible demos

- Limitations:
  - Not intended for real-time or large-scale agent-based models
  - Assumes correctness of input data; garbage-in/garbage-out applies

---

## Contributing

- See `CONTRIBUTING.md` if present (if not, follow standard GitHub fork & PR flow).
- Write tests for new features and document public APIs.

---

## Citation & Credit

If you use PoliSim in academic or policy work, please cite the repository and include authorship information from the `README` or project metadata.

---

## Contacts & Support

- Project maintainer: see `AUTHOR` or repository owner.
- For issues and feature requests: open an issue on the repository.

---

## Licensing

- Check the repository root for a `LICENSE` file. If missing, contact the maintainer before reusing code in commercial products.

---

## Getting Help

- For quick questions, open an issue or start a discussion thread.
- For reproducibility questions, attach the parameter files and the output artifacts when reporting bugs.

---

*Generated: November 26, 2025 — tailored for the PoliSim repository.*
