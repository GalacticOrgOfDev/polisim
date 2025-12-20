# F5 Debugging Guide - CBO 2.0 Dashboard

## Overview

The POLISIM project now has **three ways to launch the CBO 2.0 Streamlit Dashboard**, optimized for different workflows.

## Option 1: F5 Debugging in VSCode (Recommended for Development)

Use this method when you want to debug with breakpoints in VSCode.

**File**: `debug_dashboard.py`

**How to use**:
1. Open `debug_dashboard.py` in VSCode
2. Press `F5` to start debugging
3. Breakpoints work as expected
4. Dashboard will open in browser at `http://localhost:8501`

**Why this works**: 
- Direct Streamlit CLI execution (`streamlit.cli.main()`)
- No subprocess calls that get intercepted by debugpy
- Debugger can step through code cleanly

---

## Option 2: Command-Line Launch (For Testing/Production)

Use this method for normal command-line execution with optional customizations.

**File**: `run_dashboard.py`

**Usage**:
```bash
# Default: port 8501
python run_dashboard.py

# Custom port
python run_dashboard.py --port 8502

# Fallback to legacy Tkinter GUI if dashboard fails
python run_dashboard.py --legacy
```

**Why this works**:
- Subprocess-based approach (works fine outside debugger)
- Allows custom port specification
- Graceful fallback options

---

## Option 3: Main Script (For Integration)

Use this method when you want POLISIM to default to the dashboard.

**File**: `main.py`

**Usage**:
```bash
# Default: launches CBO 2.0 Streamlit Dashboard
python main.py

# Launch legacy Tkinter GUI (Phase 1 healthcare only)
python main.py --legacy-gui

# Run headless simulation
python main.py --simulate --scenario policies/social_security_scenarios.json
```

**Note**: `main.py` is NOT recommended for F5 debugging (subprocess issue). Use `debug_dashboard.py` instead.

---

## Quick Reference

| Workflow | Command | Best For |
|----------|---------|----------|
| **F5 Debugging** | `debug_dashboard.py` (F5 key) | Development with breakpoints |
| **Normal Launch** | `python run_dashboard.py` | Testing from terminal |
| **Integration** | `python main.py` | Automated workflows |
| **Legacy GUI** | `python main.py --legacy-gui` | Phase 1 healthcare only |
| **Headless** | `python main.py --simulate` | Batch processing |

---

## Dashboard Features

### Pages Available
1. **Overview** - Project status and quick navigation
2. **Social Security** - 5 reform scenarios with solvency analysis
3. **Federal Revenues** - 4 economic scenarios with projections
4. **Medicare/Medicaid** - Medicare Parts A/B/D and Medicaid spending
5. **Combined Outlook** - Integrated fiscal analysis (framework ready)
6. **Policy Comparison** - Side-by-side scenario comparison (framework ready)

### Interactive Controls
- Scenario selector (dropdown)
- Projection years (slider: 5-30+ years)
- Iterations (slider: 1K-50K Monte Carlo samples)
- "Run Projection" button for on-demand calculations
- Real-time Plotly charts and metrics

---

## Troubleshooting

### Dashboard Won't Launch
```bash
# Try direct launch
python debug_dashboard.py

# Or with custom port
python run_dashboard.py --port 8502

# Check if Streamlit is installed
python -c "import streamlit; print(streamlit.__version__)"
```

### F5 Debugging Doesn't Work
```bash
# Use this instead:
python debug_dashboard.py

# DO NOT use:
python main.py  # (subprocess issues with debugpy)
```

### Port Already in Use
```bash
python run_dashboard.py --port 8502
```

### Legacy GUI Needed
```bash
python main.py --legacy-gui
```

---

## Architecture

**CBO 2.0 Dashboard** (Streamlit, default)
- Modern web interface
- Interactive visualizations
- Phase 2-3.1 modules (Social Security, Revenue, Medicare/Medicaid)
- Real-time calculations
- Multi-page framework

**Legacy GUI** (Tkinter, optional)
- Phase 1 healthcare module only
- Desktop application
- Use with `--legacy-gui` flag

**Both interfaces share**
- Same core simulation modules
- JSON configuration files
- Database exports (CSV)

---

## Performance Notes

- **Default**: 10,000 Monte Carlo iterations (balanced accuracy/speed)
- **Fast mode**: 1,000 iterations (development, instant feedback)
- **High accuracy**: 50,000 iterations (production, 30-60 second runtime)

Adjust iterations slider in dashboard to control calculation time.

---

## Configuration

- **Port**: 8501 (default, change with `--port` flag)
- **Theme**: Blue (#1f77b4) - see `.streamlit/config.toml`
- **Logging**: Warning level (see `.streamlit/config.toml`)

---

## Next Steps

1. **For development**: Use `python debug_dashboard.py` with F5
2. **For testing**: Use `python run_dashboard.py`
3. **For integration**: Use `python main.py` or environment automation

See `DASHBOARD_QUICKSTART.md` for user guide to dashboard features.
