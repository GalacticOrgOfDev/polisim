# POLISIM CBO 2.0 - Implementation Roadmap

**Transforming POLISIM into an open-source Congressional Budget Office (CBO) successor**

Last Updated: December 19, 2025
Status: Planning → Active Development

---

## Executive Summary

POLISIM will evolve from a healthcare-focused policy simulator into **CBO 2.0**, a comprehensive, open-source federal fiscal projection tool with:

- **Broader scope**: Social Security, Medicare, Medicaid, revenues, discretionary spending, debt
- **Better uncertainty**: Full Monte Carlo stochastic modeling (100K+ iterations)
- **Greater transparency**: Fully open-source, auditable assumptions, public data
- **Institutional credibility**: Validation against CBO/SSA baselines within ±2-5%

---

## Phase-Based Roadmap (2 Years)

### Phase 1: Healthcare Foundation & Validation (Q1-Q2 2025)
**Status**: ✅ COMPLETE - Ready for expansion

**Completed:**
- ✅ Monte Carlo simulation engine (100K+ iterations)
- ✅ Healthcare models (USGHA baseline)
- ✅ Economic projection framework
- ✅ MCP server for AI integration
- ✅ Testing & validation framework
- ✅ Configuration management system

**Deliverables:**
- Healthcare domain validated ±2% vs CBO benchmarks
- Test suite with 50+ test cases
- Documentation complete

**Next**: Expand to Social Security (Phase 2)

---

### Phase 2: Social Security & Revenue Expansion (Q2-Q3 2025)
**Status**: 📋 In Planning

**Objectives:**
- Social Security microsimulation (OASI/DI trust funds)
- Federal revenue modeling (income tax, payroll, corporate, estate)
- Integration with demographic drivers
- Validation against SSA Trustees Report

**Key Components:**

#### 2.1 Social Security Module (`core/social_security.py`)
```python
class SocialSecurityScenario:
    """Model OASI/DI trust funds and benefit streams."""
    
    # Trust fund accounting
    trust_fund_balances: Dict[str, TimeSeries]
    payroll_tax_rate: float
    benefit_claims: Dict[str, TimeSeries]
    
    # Demographic assumptions
    life_expectancy: np.ndarray
    fertility_rate: float
    mortality_rates: Dict[str, np.ndarray]
    
    # Policy parameters
    full_retirement_age: int
    benefit_formula: Callable
    cola_adjustment: float
    
    def project_trust_funds(self, years: int) -> Dict[str, np.ndarray]:
        """Project trust fund balances with uncertainty."""
        
    def estimate_solvency_date(self) -> Dict[str, Any]:
        """Estimate depletion dates with confidence intervals."""
        
    def analyze_policy_reforms(self, reforms: List[PolicyChange]) -> Dict:
        """Model impact of reform packages (raise cap, increase taxes, etc.)."""
```

#### 2.2 Revenue Modeling Module (`core/revenue_modeling.py`)
```python
class FederalRevenueModel:
    """Model all federal revenue sources."""
    
    # Revenue sources
    individual_income_tax: RevenueComponent
    payroll_taxes: RevenueComponent  # Social Security, Medicare
    corporate_income_tax: RevenueComponent
    excise_taxes: RevenueComponent
    customs_duties: RevenueComponent
    estate_tax: RevenueComponent
    
    # Tax base drivers
    wages: np.ndarray
    profits: np.ndarray
    gdp_growth: np.ndarray
    
    def project_revenues(self, years: int, scenarios: List[Dict]) -> Dict:
        """Project revenues under current law and alternatives."""
        
    def apply_tax_reform(self, reform_params: Dict) -> Dict:
        """Model impact of tax policy changes."""
        
    def dynamic_scoring(self, behavioral_responses: Dict) -> Dict:
        """Include behavioral impacts (labor supply, savings, etc.)."""
```

**Deliverables:**
- Social Security module with 20+ test cases
- Revenue modeling system with 5+ tax components
- Combined healthcare+SS+revenue baseline
- Validation report: ±3% vs SSA Trustees baseline

**Timeline**: 8-10 weeks

---

### Phase 3: Mandatory & Discretionary Spending + Macro Integration (Q3-Q4 2025)
**Status**: 📋 Planned

**Objectives:**
- Medicare (Parts A/B/D), Medicaid, CHIP models
- Other mandatory spending (veterans, federal pensions)
- Discretionary spending frameworks
- Macroeconomic feedback loops

**Key Components:**

#### 3.1 Extended Healthcare Module (`core/healthcare_extended.py`)
```python
class MedicareModel:
    """Full Medicare Parts A, B, D projections."""
    enrollment_by_age: np.ndarray
    per_capita_costs: Dict[str, np.ndarray]
    trust_funds: Dict[str, TimeSeries]
    
class MedicaidModel:
    """Medicaid spending by eligibility category."""
    enrollment: np.ndarray
    per_capita_costs: np.ndarray
    state_federal_split: Dict[str, float]
```

#### 3.2 Macroeconomic Integration (`core/macroeconomic_feedback.py`)
```python
class MacroeconomicFeedback:
    """Model GDP, wage, and interest rate feedbacks."""
    
    def compute_fiscal_impact(self, policy_change: Dict) -> Dict:
        """Include Keynesian/supply-side impacts."""
        
    def project_interest_rates(self, debt_path: np.ndarray) -> np.ndarray:
        """Model interest rate response to debt growth."""
        
    def dynamic_revenue_adjustment(self, gdp_growth: np.ndarray) -> np.ndarray:
        """Adjust tax revenues based on macroeconomic outcomes."""
```

#### 3.3 Unified Fiscal Framework (`core/unified_fiscal_model.py`)
```python
class CBO2UnifiedModel:
    """Integrated healthcare + SS + revenue + mandatory + discretionary + macro."""
    
    def project_full_fiscal_outlook(
        self, years: int, iterations: int = 100000
    ) -> FiscalProjection:
        """Complete 10-75 year fiscal projection."""
        
    def compare_policy_packages(
        self, baseline: Policy, alternatives: List[Policy]
    ) -> ComparisonReport:
        """Dynamic scoring across full fiscal space."""
```

**Deliverables:**
- Full CBO 2.0 unified model
- 100,000+ iteration simulations on full scope
- Validation: ±5% vs CBO long-term outlook
- Performance: 10-75 year projections in <5 min

**Timeline**: 10-12 weeks

---

### Phase 4: Web UI, Data Integration & Reporting (Q4 2025-Q1 2026)
**Status**: 📋 Planned

**Objectives:**
- Interactive web interface (Streamlit/Dash)
- Automated data ingestion (CBO, SSA, Census APIs)
- Report generation (PDF, HTML, Excel)
- Performance optimization for production

**Key Components:**

#### 4.1 Web Application (`ui/dashboard.py` - Streamlit)
```python
# Key Pages:
# 1. "Quick Start" - Run USGHA vs baseline in 60 seconds
# 2. "Policy Builder" - Configure custom policies via UI
# 3. "Scenario Comparison" - Side-by-side policy analysis
# 4. "Uncertainty Analysis" - Monte Carlo distributions, fan charts
# 5. "Data Sources" - Document all assumptions & sources
# 6. "Validation" - Compare vs CBO/SSA historical
```

**Features:**
- Drag-and-drop policy builder
- Real-time Monte Carlo visualization
- Sensitivity sliders
- Export to PDF/Excel
- Share scenarios via URL

#### 4.2 Data Integration Layer (`core/data_sources.py`)
```python
class DataSourceManager:
    """Automated data ingestion and updating."""
    
    def pull_cbo_baseline(self, year: int) -> Dict:
        """Fetch latest CBO Economic & Budget Outlook."""
        
    def pull_ssa_trustees_report(self) -> Dict:
        """Ingest SSA Trustees actuarial assumptions."""
        
    def pull_census_demographics(self) -> pd.DataFrame:
        """Get latest Census population projections."""
        
    def auto_update_schedule(self):
        """Nightly updates of official projections."""
```

#### 4.3 Report Generation (`core/report_generator.py`)
```python
class PolicyBriefGenerator:
    """Generate publication-ready policy briefs."""
    
    def generate_pdf(self, scenario: Scenario) -> bytes:
        """PDF with charts, tables, key findings."""
        
    def generate_html_interactive(self, scenario: Scenario) -> str:
        """Interactive HTML with Plotly charts."""
        
    def generate_excel_workbook(self, comparison: Comparison) -> bytes:
        """Full data + charts in Excel format."""
```

**Deliverables:**
- Production-grade Streamlit app
- Automated daily data updates
- PDF/HTML/Excel report generation
- Performance: Sub-second UI response times

**Timeline**: 8-10 weeks

---

### Phase 5: Validation, Community, & Launch (Q1-Q2 2026)
**Status**: 📋 Planned

**Objectives:**
- Institutional validation (think tanks, academic peer review)
- Community governance & contribution framework
- Public launch with academic papers
- Integration with PSLmodels ecosystem

**Key Activities:**

#### 5.1 Validation
- [ ] Back-test against 20 years of historical projections
- [ ] Peer review by CBO economists, SSA actuaries, academic macroeconomists
- [ ] Published validation report (methodology, accuracy, limitations)
- [ ] Continuous monitoring dashboard: "How accurate are we?"

#### 5.2 Community
- [ ] Contributor guidelines & development roadmap
- [ ] Advisory board (2-3 economists, 1-2 policy experts)
- [ ] Monthly community calls & issue prioritization
- [ ] Integration pathway with PSLmodels
- [ ] Academic partnerships (universities, think tanks)

#### 5.3 Launch Strategy
- [ ] White paper: "POLISIM: Open-Source Fiscal Projection" (arXiv)
- [ ] Press release & media outreach
- [ ] Congressional staff briefings
- [ ] Think tank / university partnerships
- [ ] Open-source community announcements (r/Python, HN, etc.)

#### 5.4 Success Metrics by Month 24
- [ ] **1,000+ GitHub stars**
- [ ] **50+ contributors**
- [ ] **Cited in policy debates** (Congressional testimony, op-eds)
- [ ] **Academic papers** (3+ peer-reviewed publications)
- [ ] **10,000+ users** (estimated from analytics)
- [ ] **±2-5% accuracy** vs CBO/SSA benchmarks

**Timeline**: 12-14 weeks

---

## Detailed Phase 2 Specification (Immediate Next Steps)

### Phase 2a: Social Security Module (Weeks 1-4)

#### Deliverables:
1. **`core/social_security.py`** (400-500 lines)
   - OASI/DI benefit calculations
   - Trust fund projections
   - Demographic drivers (mortality, fertility, immigration)
   - Policy reform modeling (raise cap, increase taxes, benefit changes)

2. **`tests/test_social_security.py`** (250+ lines)
   - Test trust fund projections
   - Validate against SSA Trustees Report assumptions
   - Test policy reforms

3. **Configuration files** (`policies/social_security_*.json`)
   - OASI/DI baseline scenarios
   - Common reform packages (raise cap, increase tax rate, etc.)

4. **Documentation** (`docs/social_security_methodology.md`)
   - Model description, assumptions, validation

#### Validation Targets:
- Social Security trust fund depletion date: ±1 year of 2035 SSA estimate
- 2050 OASI spending as % payroll: ±2% of SSA projection

---

### Phase 2b: Revenue Modeling (Weeks 4-8)

#### Deliverables:
1. **`core/revenue_modeling.py`** (600-700 lines)
   - Individual income tax (effective rates, brackets)
   - Payroll taxes (Social Security, Medicare)
   - Corporate income tax
   - Other revenues (excise, customs, estate)

2. **`tests/test_revenue_modeling.py`** (250+ lines)
   - Test revenue projections
   - Validate current law revenues vs CBO baseline
   - Test tax reform scenarios

3. **Configuration files** (`policies/revenue_scenarios_*.json`)
   - Current law baseline
   - Tax reform packages (rate changes, bracket adjustments, etc.)

4. **Documentation** (`docs/revenue_methodology.md`)

#### Validation Targets:
- Federal revenues 10-year baseline: ±1% of CBO projection
- Income tax breakdown (individual vs corporate): ±2%

---

### Phase 2c: Integration & Cross-Module Testing (Weeks 8-10)

#### Deliverables:
1. **`core/phase2_integrated_model.py`** (300-400 lines)
   - Unified healthcare + SS + revenue model
   - All three modules run together
   - Consistent demographic assumptions

2. **`tests/test_phase2_integration.py`** (150+ lines)
   - End-to-end scenarios (baseline + reforms)
   - Consistency checks between modules

3. **Example scenarios** (Jupyter notebooks + scripts)
   - "Baseline 10-year outlook"
   - "Social Security reform package A"
   - "Tax reform scenario"
   - Combined package (SS + tax + healthcare reforms)

#### Deliverables:
- Unified model runs 10-year projections with all three domains
- 100,000 iterations in <2 minutes
- Results match expected ranges (±3%)

---

## Repository Structure After Phase 2

```
polisim/
├── core/
│   ├── __init__.py
│   ├── economic_engine.py          # Existing - Monte Carlo core
│   ├── config.py                   # Existing - Config mgmt
│   ├── healthcare.py               # Existing - Healthcare models
│   ├── social_security.py           # 🆕 Phase 2 - SS module
│   ├── revenue_modeling.py          # 🆕 Phase 2 - Revenue module
│   ├── phase2_integrated_model.py   # 🆕 Phase 2 - Integration
│   └── ...
├── policies/
│   ├── catalog.json                # Existing
│   ├── healthcare_*.json           # Existing
│   ├── social_security_*.json      # 🆕 Phase 2 - SS scenarios
│   ├── revenue_scenarios_*.json    # 🆕 Phase 2 - Revenue scenarios
│   └── phase2_combined_*.json      # 🆕 Phase 2 - Combined packages
├── tests/
│   ├── test_economic_engine.py     # Existing
│   ├── test_simulation_healthcare.py # Existing
│   ├── test_social_security.py     # 🆕 Phase 2
│   ├── test_revenue_modeling.py    # 🆕 Phase 2
│   └── test_phase2_integration.py  # 🆕 Phase 2
├── docs/
│   ├── methodology/
│   │   ├── healthcare_methodology.md
│   │   ├── social_security_methodology.md  # 🆕 Phase 2
│   │   ├── revenue_methodology.md          # 🆕 Phase 2
│   │   └── validation_framework.md
│   ├── user_guides/
│   └── examples/
├── CBO_2_0_ROADMAP.md              # This document
├── CBO_2_0_IMPLEMENTATION.md       # Detailed specs
└── ...
```

---

## Success Criteria Checklist

### Phase 2 Complete When:
- [ ] Social Security module passes ±1 year validation vs SSA baseline
- [ ] Revenue modeling matches ±1% vs CBO current-law baseline
- [ ] Integrated model runs 100,000 iterations in <2 minutes
- [ ] 50+ new test cases all passing
- [ ] Documentation complete with worked examples
- [ ] Phase 2 combines with Phase 1 (healthcare) for unified 3-domain baseline
- [ ] MCP server updated with new tools (run_ss_analysis, revenue_reform, etc.)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Data access delays | Start with SSA published assumptions; add APIs later |
| Scope creep in Phase 2 | Focus on OASI/DI only; defer complex Medicaid interactions |
| Demographic complexity | Use published SSA/Census assumptions; don't build new models |
| Performance degradation | Profiling + parallel processing (NumPy/Dask) from start |
| Model divergence from CBO | Monthly validation checks; pivot early if >5% error |

---

## Timeline Summary

| Phase | Duration | Key Deliverables | Status |
|-------|----------|-----------------|--------|
| Phase 1 | Q4 2024 - Q1 2025 | Healthcare engine, MCP server, tests | ✅ Complete |
| Phase 2 | Q2-Q3 2025 | Social Security + Revenue modules | 📋 Planning |
| Phase 3 | Q3-Q4 2025 | Full mandatory/discretionary + macro | 📋 Planned |
| Phase 4 | Q4 2025 - Q1 2026 | Web UI, data integration, reports | 📋 Planned |
| Phase 5 | Q1-Q2 2026 | Validation, community, public launch | 📋 Planned |

**Total Timeline**: ~18 months to "CBO 2.0 Ready for Production"

---

## Next Steps (After PRD Approval)

1. **Finalize Phase 2 Spec** (1 week)
   - Confirm data sources (SSA, CBO, Census APIs)
   - Finalize module interfaces
   - Create GitHub milestone & issues

2. **Phase 2 Kickoff** (Next week)
   - Create `core/social_security.py` skeleton
   - Add to requirements.txt if new dependencies needed
   - Create GitHub issues for each component

3. **Weekly Check-ins**
   - Track progress against milestones
   - Flag any blockers or changes

---

**Document Status**: Draft - Ready for CBO 2.0 Roadmap Approval
**Last Updated**: December 19, 2025
**Next Review**: January 9, 2026
