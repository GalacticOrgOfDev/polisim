# 🚀 POLISIM: Getting Started Guide

**Status:** Phase 6.2.5 Complete  
**Last Updated:** January 2, 2026  
**Progress:** Phases 1-6.2.5 complete | Security hardening & policy extraction active  

---

## ⚡ Quick Start (60 seconds)

### Option 1: Launcher (Recommended ✅)

```powershell
# Launch the graphical installer/launcher
python launcher.py
```

**Why use the launcher?**
- ✅ Validates all dependencies before starting
- ✅ Checks CBO data ingestion and API prerequisites
- ✅ Auto-installs missing packages (with approval)
- ✅ Non-blocking UI - no freezing during operations
- ✅ Real-time activity log with timestamps
- ✅ One-click access to Dashboard, API, or MCP Server

The launcher will:
1. Check/create virtual environment
2. Install dependencies
3. Run comprehensive startup checks
4. Launch dashboard, API, or MCP server

### Option 2: Manual Setup (Advanced Users)

> ⚠️ **Note:** Manual setup skips the comprehensive dependency validation that `launcher.py` provides. Use this only if you need specific control over the startup process.

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run startup check (important!)
python main.py --startup-check-only

# Start dashboard
streamlit run ui/dashboard.py

# OR start API server
python api/rest_server.py
```

### Option 3: Docker

```bash
docker-compose up --build
```

---

## 🎯 What is PoliSim?

An open-source, transparent alternative to the Congressional Budget Office's fiscal projections. Built with full Monte Carlo stochastic modeling and comprehensive policy analysis.

### Key Capabilities

| Module | Description |
|--------|-------------|
| **Healthcare** | 8 policy models (USGHA, M4A, UK NHS, etc.) with 22-year projections |
| **Social Security** | Trust fund projections, reform scenarios, solvency analysis |
| **Federal Revenue** | Income, payroll, corporate tax modeling with elasticities |
| **Medicare/Medicaid** | Enrollment, spending, and trust fund projections |
| **Discretionary** | Defense and non-defense spending scenarios |
| **Combined Outlook** | Unified federal budget with Monte Carlo uncertainty |
| **Policy Comparison** | Side-by-side analysis with confidence intervals |

---

## 📊 Dashboard Pages

1. **Overview** - Project status and navigation
2. **Healthcare Analysis** - Policy simulations and comparisons
3. **Social Security** - Trust fund projections and reforms
4. **Federal Revenues** - Tax modeling and scenarios
5. **Medicare/Medicaid** - Healthcare spending projections
6. **Discretionary Spending** - Defense/non-defense scenarios
7. **Combined Outlook** - Unified federal budget model
8. **Policy Comparison** - Multi-policy analysis
9. **Policy Library** - Manage custom and uploaded policies
10. **Settings** - Configure themes, tooltips, and preferences

---

## 🏛️ Completed Phases

### Phase 1: Healthcare Simulation ✅
- 8 policy models (USGHA, Current US, M4A, UK NHS, Canada, Australia, Germany, UN)
- Context-aware mechanism extraction
- 22-year projections with surplus allocation

### Phase 2: Tax Reform + Social Security ✅
- Wealth, consumption, carbon, FTT tax levers
- Social Security trust fund projections
- CBO/SSA baseline validation (±2%)

### Phase 3: Medicare/Medicaid + Revenue ✅
- Combined fiscal outlook
- Monte Carlo stability (100-10K iterations)
- CBO 2026 baseline alignment

### Phase 4: Production Polish ✅
- InputValidator and edge-case handlers
- 42% performance improvement (vectorization)
- 413/415 tests passing

### Phase 5: Web UI + Data Integration ✅
- Streamlit dashboard (10+ pages)
- Tk-based launcher with bootstrap
- Scenario builder, reports, public API

### Phase 6.2: Security Hardening ✅
- Vulnerability audit (pip-audit, bandit, safety)
- CORS whitelist, 7 security headers
- Secrets management, JWT auth, RBAC
- DDoS protection (rate limiting, circuit breakers)

---

## 📚 Documentation Map

| Document | Purpose |
|----------|---------|
| [INDEX.md](INDEX.md) | Central navigation hub |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | API and usage examples |
| [CHANGELOG.md](CHANGELOG.md) | Complete project history |
| [../docs/PHASES.md](../docs/PHASES.md) | Project roadmap (Phases 1-18) |
| [CONTEXT_FRAMEWORK.md](CONTEXT_FRAMEWORK.md) | Policy extraction system |
| [THEME_SYSTEM.md](THEME_SYSTEM.md) | UI theme reference |

---

## 🔧 Common Tasks

### Upload a Policy

1. Navigate to **Policy Library** page
2. Click **📤 Upload Policy**
3. Select PDF file containing policy text
4. Review extracted mechanics
5. Save to library

### Run a Combined Outlook Projection

1. Navigate to **Combined Fiscal Outlook** page
2. Select a policy (Baseline or uploaded)
3. Configure scenarios (Economic, Discretionary, Interest)
4. Click **Calculate Combined Fiscal Outlook**
5. Review charts and metrics

### Compare Policies

1. Navigate to **Policy Comparison** page
2. Select policies to compare
3. Configure projection parameters
4. Review side-by-side analysis

---

## 🛠️ Development

### Run Tests

```powershell
pytest tests/ -v
```

### Run Specific Test Suite

```powershell
pytest tests/test_combined_outlook_policy.py -v
```

### Check for Errors

```powershell
python -m mypy core/ api/ ui/ --ignore-missing-imports
```

---

## 📞 Resources

- **Main README:** [../README.md](../README.md)
- **API Docs:** [API_AUTHENTICATION.md](API_AUTHENTICATION.md)
- **Security:** [../docs/SECURITY.md](../docs/SECURITY.md)
- **Incident Response:** [../docs/INCIDENT_RESPONSE.md](../docs/INCIDENT_RESPONSE.md)

---

**Phase 6.2.5 Status:** ✅ COMPLETE  
**Current Work:** Policy extraction enhancements, Combined Outlook improvements  
**Next Milestone:** Phase 6.3 - Independent Validation
