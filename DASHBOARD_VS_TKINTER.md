# Streamlit Dashboard vs Tkinter UI - Roadmap

## Current Status

**Tkinter UI** (`Economic_projector.py`): Phase 1 Healthcare only
- Policy parameter input (revenues, spending)
- Simulation controls
- Comparison analysis
- Report export

**Streamlit Dashboard** (`ui/dashboard.py`): Phase 1-3 Healthcare + Social Security + Revenue + Medicare/Medicaid
- 4 active pages
- 2 framework-ready pages
- Interactive real-time calculations
- Plotly visualizations

---

## Next Phase: Phase 3.2 - Discretionary Spending & Macro Integration

**Status**: Planning → Next Implementation  
**Target**: Add remaining federal budget components

### What's Phase 3.2?

| Component | Status | Notes |
|-----------|--------|-------|
| Healthcare | ✅ Phase 1 | USGHA baseline + alternatives |
| Social Security | ✅ Phase 2 | Trust funds + reform scenarios |
| Medicare/Medicaid | ✅ Phase 3.1 | Parts A/B/D + Medicaid spending |
| **Discretionary Spending** | 📋 Phase 3.2 | Defense, non-defense, infrastructure |
| **Interest on Debt** | 📋 Phase 3.2 | Automatic calculations |
| **Macro Integration** | 📋 Phase 3.2 | Unified fiscal outlook |

### Implementation Plan

**Phase 3.2 Modules** (to create):
1. `core/discretionary_spending.py` (~300 LOC)
   - Defense spending scenarios (flat, growth, reduction)
   - Non-defense discretionary (infrastructure, education, R&D)
   - Historical baseline + CBO projections
   - Inflation adjustment logic

2. `core/interest_spending.py` (~150 LOC)
   - Interest rate modeling
   - Debt service calculations
   - Treasury yield scenarios
   - Automatic function

3. `core/combined_outlook.py` (~400 LOC)
   - Unified budget model (all revenue + all spending)
   - Deficit/surplus calculation
   - 75-year sustainability metrics
   - "Fiscal gap" analysis (CBO methodology)

**Phase 3.2 Dashboard Pages** (to add):
1. **Discretionary Spending** page
   - Defense vs non-defense split
   - Scenario selector (flat, growth, reduction)
   - Charts showing inflation impact
   - Year-by-year breakdowns

2. **Combined Fiscal Outlook** page (currently framework-ready)
   - Total revenue (Phase 2)
   - Total mandatory spending (healthcare + SS + Medicare/Medicaid)
   - Total discretionary spending (new Phase 3.2)
   - Interest on debt
   - Bottom line: Deficit or surplus
   - 30-year debt trajectory

3. **Macro Dashboard** page
   - GDP growth scenarios
   - Inflation impacts
   - Employment effects
   - Interest rate sensitivity

---

## Tkinter UI Features to Port to Dashboard

### Current Tkinter Features

| Feature | Status | Tkinter Location | Dashboard Location |
|---------|--------|------------------|-------------------|
| **Parameter Input** | ✅ In progress | `scenarios` tab | Streamlit sliders/inputs |
| **Policy Selection** | ✅ Complete | Scenario setup | Dropdown selectors |
| **Simulation Control** | ✅ Complete | "Run" button | "Run Projection" button |
| **Results Display** | ✅ Complete | Numeric outputs | Metric cards + charts |
| **Comparison Table** | 🔄 Needed | Comparison tab | "Policy Comparison" page |
| **Chart Carousel** | 🔄 Needed | ChartCarousel widget | Plotly tabs on each page |
| **Export Reports** | 🔄 Needed | Export button | Report button (PDF/CSV) |
| **Scenario Library** | ✅ Complete | Saved scenarios list | JSON config files |
| **Multi-country Data** | 🔄 Deferred | Country selector | Future enhancement |

### Tkinter UI Structure (Economic_projector.py, 2,843 LOC)

```
Main Tabs:
├── Scenario Setup (wizard entry point)
│   ├── Country/region selector
│   └── Save scenario button
├── Current Policy (with sub-tabs)
│   ├── General (tax rates, assumptions)
│   ├── Revenues (income, payroll, corporate)
│   └── Spending (healthcare categories)
├── Proposed Policy (with sub-tabs)
│   ├── General
│   ├── Revenues
│   └── Spending
└── Comparison (output results)
    ├── Comparison table
    ├── Chart carousel
    └── Export options
```

### Streamlit Dashboard Structure (ui/dashboard.py, 387 LOC)

```
Pages:
├── Overview (status + navigation)
├── Social Security (Phase 2)
│   ├── Scenario selector
│   ├── Run controls
│   └── Results + charts
├── Federal Revenues (Phase 2)
│   ├── Scenario selector
│   └── Results + charts
├── Medicare/Medicaid (Phase 3.1)
│   ├── Tabs for Parts A/B/D
│   └── Medicaid analysis
├── Combined Outlook (framework)
└── Policy Comparison (framework)
```

---

## Strategy: Dual Interface

### Option A: Keep Both (Recommended for Phase 3.2)
**Rationale:**
- Tkinter handles Phase 1 (healthcare) well
- Streamlit better for web-based Phase 2-3+ (complex multi-page)
- Users choose: `python main.py --legacy-gui` vs `python run_dashboard.py`
- Easier gradual migration
- Different use cases (desktop vs browser)

**Implementation:**
1. Keep Tkinter as-is (Phase 1 reference implementation)
2. Expand Streamlit dashboard (Phase 2-5 hub)
3. Add Phase 3.2 to Streamlit first
4. Optionally backport to Tkinter later if needed

### Option B: Migrate Everything to Streamlit
**Rationale:**
- Single codebase
- Better for multi-page, multi-module app
- Web-native (easier deployment)
- Real-time interactivity

**Implementation:**
1. Rebuild Phase 1 healthcare page in Streamlit
2. Unify all Phase 1-3 in single app
3. Deprecate Tkinter
4. Time: ~2-3 days

---

## Recommended Next Steps (Your Choice)

### Path 1: Streamlit-First Expansion (Fastest)
1. **Implement Phase 3.2** (discretionary + macro integration)
   - Time: 2-3 days
   - Creates unified fiscal dashboard
   - All Phase 1-3.2 in one web app

2. **Add Healthcare Module** to Streamlit
   - Port Phase 1 logic to Streamlit page
   - Keep Tkinter available as legacy option
   - Time: 1 day

3. **Result**: Complete CBO 2.0 framework (healthcare + SS + revenue + Medicare/Medicaid + discretionary + macro)

### Path 2: Tkinter-First Approach (Most Thorough)
1. **Add Phase 3.2 to Tkinter** first
   - Extend `core/simulation.py` with discretionary logic
   - Add discretionary spending tabs
   - Maintain consistency with Phase 1

2. **Then expand Streamlit** dashboard
   - Keep as secondary modern interface
   - Provides web access for same models

3. **Result**: Both interfaces support full fiscal model

### Path 3: Parallel Development (Most Flexible)
1. **Add Phase 3.2 core modules** (discretionary + macro)
   - Independent of UI
   - Both Tkinter and Streamlit can use

2. **Simultaneously**:
   - Expand Streamlit dashboard with Phase 3.2 pages
   - Extend Tkinter with Phase 3.2 tabs

3. **Result**: Full feature parity eventually, fastest time to value

---

## What Goes in Each Dashboard Page

### Current Pages (Working ✅)

**Social Security Page**
- Scenario selector (5 reform options)
- Years & iterations controls
- "Run Projection" button
- Solvency metrics (OASI depletion, DI through year, 75-year solvency)
- Chart: Trust fund balance over time

**Federal Revenues Page**
- Scenario selector (4 economic scenarios)
- Results display
- Revenue breakdown chart
- CAGR metrics

**Medicare/Medicaid Page**
- Tabs for Medicare Parts A/B/D
- Medicaid spending tab
- Enrollment projections
- Per-capita cost trends

### Pages Needing Implementation (Framework Ready 🔄)

**Combined Fiscal Outlook** (Phase 3.2)
```
Controls:
├── Scenario selector (pre-built combinations)
├── Years slider (10-75)
└── Iterations slider (1K-50K)

Displays:
├── Summary metrics
│   ├── Total revenue
│   ├── Total spending (all categories)
│   ├── Deficit/surplus
│   └── 30-year debt impact
├── Stacked area chart
│   ├── Revenue (income/payroll/corporate/other)
│   ├── Spending (healthcare/SS/Medicare/Medicaid/discretionary)
│   └── Interest on debt
└── Sustainability metrics
    ├── Primary balance (excluding interest)
    ├── Debt/GDP ratio
    └── Fiscal gap (% of future GDP)
```

**Policy Comparison** (Phase 3.2)
```
Controls:
├── Select up to 3 policies
├── Select metric to compare (deficit, debt/GDP, etc.)
└── Run comparison

Displays:
├── Side-by-side metrics table
├── Line chart comparing outcomes
├── Sensitivity analysis (tornado chart)
└── "Winner" analysis (which policy best achieves goal X)
```

**Discretionary Spending** (Phase 3.2)
```
Controls:
├── Scenario selector
│   ├── Historical baseline
│   ├── Flat (no growth)
│   ├── GDP growth scenario
│   ├── Reduction scenario
│   └── Custom sliders
├── Defense/non-defense split

Displays:
├── Spending breakdown chart
├── Inflation impact table
├── Year-by-year projections
└── Budget share trends (% of total budget)
```

---

## Feature Comparison Table

| Feature | Tkinter | Streamlit | Decision |
|---------|---------|-----------|----------|
| Scenario builder | ✅ Forms | 🔄 Sliders | Both work well |
| Multi-page layout | 🔄 Tabs | ✅ Navigation | Streamlit better |
| Real-time charts | 🔄 Static (refresh) | ✅ Dynamic | Streamlit superior |
| Parameter input | ✅ Spinboxes | ✅ Sliders/inputs | Both good, Streamlit easier |
| Table display | ✅ Tkinter tables | ✅ Pandas dataframes | Streamlit better |
| Export reports | ✅ CSV/PDF | 🔄 TBD | Need to add |
| Multi-policy compare | 🔄 Tabs | ✅ Page + chart | Streamlit cleaner |
| Responsive layout | 🔄 Fixed size | ✅ Responsive | Streamlit winner |
| Deployment | 🔄 Desktop app | ✅ Web browser | Streamlit better |
| Developer experience | 🔄 Complex (2,843 LOC) | ✅ Simple (387 LOC) | Streamlit cleaner |

---

## My Recommendation

**Go with Path 1: Streamlit-First Expansion**

**Why:**
1. **Cleaner codebase** - 387 LOC vs 2,843 LOC for same functionality
2. **Easier to add Phase 3.2** - Streamlit sliders and charts are perfect for fiscal analysis
3. **Web-native** - Better for future deployment, sharing, collaboration
4. **Less duplication** - Don't maintain two full UIs
5. **Faster iteration** - Can update dashboard without rebuilding desktop app

**Implementation Order:**
1. **Week 1**: Build Phase 3.2 core modules (discretionary + macro + combined)
2. **Week 1-2**: Add 3 new dashboard pages (Combined Outlook, Policy Comparison, Discretionary)
3. **Week 2**: Port healthcare (Phase 1) to Streamlit if time permits
4. **Keep Tkinter** as legacy option (`--legacy-gui` flag)

**Result by end of Phase 3.2**: 
- Complete CBO 2.0 fiscal model
- All 6 dashboard pages functional
- Ready for Phase 4 (web deployment)

---

## Quick Reference: How to Add Features to Dashboard

### Adding a New Page

```python
# 1. Create page function in ui/dashboard.py
def page_discretionary_spending():
    st.title("💰 Discretionary Spending Analysis")
    
    # 2. Add controls
    scenario = st.selectbox("Scenario:", ["Baseline", "Growth", "Reduction"])
    years = st.slider("Years:", 10, 75, 30)
    
    # 3. Load data or run simulation
    if st.button("Run Analysis"):
        model = DiscretionarySpendingModel()
        results = model.project(years, scenario)
    
    # 4. Display results
    st.metric("Total Spending (10yr)", f"${results['total_10yr']:,.0f}B")
    st.plotly_chart(results['chart'])

# 2. Register in main app navigation
pages = {
    "Overview": page_overview,
    "Social Security": page_social_security,
    "Federal Revenues": page_federal_revenues,
    "Medicare/Medicaid": page_medicare_medicaid,
    "Discretionary Spending": page_discretionary_spending,  # NEW
    "Combined Outlook": page_combined_outlook,
    "Policy Comparison": page_policy_comparison,
}
```

### Adding a New Metric

```python
# In your page function:
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Label",
        value,
        delta=f"Change description",
        help="Tooltip text"
    )
```

### Adding a New Chart

```python
# Use Plotly
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(x=years, y=values, name="Series 1"))
fig.update_layout(title="Chart Title", xaxis_title="X", yaxis_title="Y")

st.plotly_chart(fig, use_container_width=True)
```

---

## Next Action

**What would you like to do?**

1. **Start Phase 3.2** - I'll build discretionary spending + macro modules
2. **Port Healthcare to Streamlit** - I'll create Phase 1 page in web dashboard
3. **Add Policy Comparison** - I'll implement comparison page framework
4. **Hybrid approach** - I'll do all three in parallel
5. **Something else** - Tell me your priority

Just let me know! 🚀
