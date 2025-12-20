# CBO 2.0 Dashboard - Quick Start Guide

## Launch the Dashboard

### Option 1: Run from Command Line (Recommended)
```bash
python run_dashboard.py
```

Then open your browser to: **http://localhost:8501**

### Option 2: Run with Custom Port
```bash
python run_dashboard.py --port 8502
```

### Option 3: Run from main.py
```bash
python main.py --dashboard
```

### Option 4: Launch Legacy GUI (Phase 1 Healthcare Only)
```bash
python run_dashboard.py --legacy
```
or
```bash
python main.py --legacy-gui
```

---

## What's Available in the Dashboard

### 📊 Pages

1. **Overview** 
   - Status of all modules (Phase 1-3.1)
   - Quick stats and navigation

2. **Social Security** 
   - 5 reform scenarios (raise tax, remove cap, raise FRA, reduce benefits, combined)
   - Trust fund projections with Monte Carlo uncertainty
   - Depletion date analysis with confidence intervals

3. **Federal Revenues**
   - 4 economic scenarios (baseline, recession, strong growth, demographic)
   - 7-source revenue projections
   - Revenue breakdown and growth rates

4. **Medicare/Medicaid**
   - Medicare Parts A/B/D projections
   - Medicaid spending by eligibility category
   - State/federal cost sharing

5. **Combined Outlook** (Coming Soon)
   - Integrated healthcare + SS + revenue analysis

6. **Policy Comparison** (Coming Soon)
   - Side-by-side scenario analysis

---

## Dashboard Features

- ✅ **Interactive Scenarios** - Select from pre-configured policy scenarios
- ✅ **Real-Time Calculations** - Run projections on demand with Streamlit
- ✅ **Monte Carlo Analysis** - Full stochastic uncertainty modeling (10K-100K iterations)
- ✅ **Plotly Charts** - Interactive visualizations with hover details
- ✅ **Parameter Tuning** - Adjust years and iterations with sliders
- ✅ **Baseline Validation** - Compare against SSA/CBO official projections

---

## System Requirements

- Python 3.9+
- Virtual environment activated (`.venv/`)
- Required packages:
  - streamlit >=1.28.0
  - plotly >=5.0.0
  - pandas, numpy, scipy (already installed)

## Install Missing Dependencies

```bash
pip install -r requirements.txt
```

---

## Troubleshooting

### "Streamlit not found" error
```bash
pip install streamlit plotly
```

### Dashboard won't open
- Check that port 8501 is not already in use
- Try custom port: `python run_dashboard.py --port 8502`

### Slow calculations
- Reduce Monte Carlo iterations with the slider
- Start with 5,000-10,000 iterations instead of 50,000

### Import errors
- Ensure you're in the venv: `. .venv/Scripts/Activate.ps1` (PowerShell)
- Or: `.venv\Scripts\Activate` (Command Prompt)

---

## Development

**Edit Dashboard:**
- `ui/dashboard.py` - Main Streamlit app

**Edit Scenarios:**
- `policies/social_security_scenarios.json`
- `policies/tax_reform_scenarios.json`
- `policies/revenue_scenarios.json`

**Edit Models:**
- `core/social_security.py` - Social Security
- `core/revenue_modeling.py` - Revenue projections
- `core/medicare_medicaid.py` - Medicare/Medicaid

**Run Tests:**
```bash
pytest tests/test_phase2_integration.py -v
```

---

## Next Steps

- [ ] Deploy to cloud (Streamlit Cloud, AWS, GCP)
- [ ] Add Phase 3.2 (macro integration, discretionary spending)
- [ ] Add Combined Outlook page
- [ ] Add Policy Comparison page
- [ ] Performance optimization for large iterations
- [ ] Report export to PDF/Excel
