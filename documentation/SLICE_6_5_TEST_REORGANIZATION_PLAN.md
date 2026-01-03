# Slice 6.5: Test Reorganization & Validation Plan

**Document Purpose:** Comprehensive plan to reorganize, rename, and enhance the polisim test suite  
**Date Created:** January 2, 2026  
**Status:** In Progress  
**Estimated Effort:** 35-50 hours

---

## Executive Summary

The polisim test suite currently has **~750+ test functions** across **68 test files**. While functional, many tests are named by development phase (e.g., `test_phase2_integration.py`, `test_phase32_integration.py`) rather than by the feature/module they test. This makes it difficult to:

1. Quickly identify what functionality a test covers
2. Determine test coverage for specific features
3. Onboard new contributors
4. Maintain tests when features change

This plan reorganizes tests by **functional domain** with clear, descriptive naming.

---

## Current Test Inventory

### Files Needing Rename (Phase/Slice Named)
| Current Name | Test Count | Actual Purpose | Proposed Name |
|--------------|------------|----------------|---------------|
| `test_phase2_integration.py` | 18 | Social Security + Revenue integration | `test_fiscal_integration_social_security_revenue.py` |
| `test_phase2_validation.py` | 19 | CBO/SSA baseline validation | `test_baseline_validation_cbo_ssa.py` |
| `test_phase2b_edge_cases.py` | 15 | SS/Revenue edge cases | `test_edge_cases_fiscal_models.py` |
| `test_phase2_integration_engine.py` | 19 | Tax reform integration engine | `test_tax_reform_integration.py` |
| `test_phase32_integration.py` | 27 | Discretionary + Interest + Combined outlook | `test_fiscal_integration_discretionary_interest.py` |
| `test_phase_6_2_3_secrets.py` | 33 | Secrets management | `test_secrets_management.py` |
| `test_slice_5_6_integration.py` | 21 | Scenario builder + Report generation | `test_scenario_builder_reports.py` |
| `test_slice_5_7_api.py` | 24 | API v1 endpoints | `test_api_v1_endpoints.py` |

### Tests by Functional Domain

#### 1. **Core Simulation Models** (~170 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_simulation_healthcare.py` | 16 | Healthcare simulation |
| `test_social_security.py` | 22 | Social Security model |
| `test_social_security_enhancements.py` | 31 | SS edge cases/enhancements |
| `test_medicare_medicaid.py` | 20 | Medicare/Medicaid models |
| `test_revenue_modeling.py` | 25 | Revenue projections |
| `test_tax_reform.py` | 37 | Tax reform scenarios |
| `test_economic_engine.py` | 24 | Monte Carlo engine |

#### 2. **Edge Cases & Validation** (~100 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_edge_cases.py` | 50 | Edge case handlers |
| `test_validation.py` | 36 | Data validation |
| `test_validation_integration.py` | 15 | Validation integration |

#### 3. **API & Security** (~125 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_api_authentication.py` | 24 | JWT/login auth |
| `test_security.py` | 22 | OWASP security tests |
| `test_ddos_protection.py` | 22 | Rate limiting/circuit breakers |
| `test_integration_security_stack.py` | 18 | Full security pipeline |
| `test_phase_6_2_3_secrets.py` | 33 | Secrets management |
| `test_ui_auth.py` | 8 | UI authentication |

#### 4. **Reports & Exports** (~50 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_report_generation.py` | 13 | PDF/Excel reports |
| `test_report_charts.py` | 12 | Chart generation |
| `test_scenario_comparison.py` | 14 | Scenario comparison |
| `test_scenario_diff_viewer.py` | 11 | Diff visualization |

#### 5. **Data Integration** (~30 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_cbo_integration.py` | 26 | CBO data scraper |
| `test_combined_outlook_policy.py` | 5 | Combined fiscal outlook |

#### 6. **Policy Extraction** (~10 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_context_framework.py` | 5 | Context-aware extraction |
| `test_full_workflow.py` | 5 | End-to-end PDF extraction |

#### 7. **UI & Dashboard** (~60 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_teaching_mode.py` | 37 | Teaching mode features |
| `test_themes_and_dash.py` | 6 | Theme switching |
| `test_tooltip_registry.py` | 5 | Tooltip system |
| `test_startup_check.py` | 7 | Startup validation |

#### 8. **Stress & Performance** (~30 tests)
| File | Tests | Domain |
|------|-------|--------|
| `test_stress_scenarios.py` | 27 | Stress testing |
| `test_performance_sprint44.py` | 3 | Performance benchmarks |

---

## Reorganization Plan

### Phase 1: Rename Phase-Named Files (8 files)

#### 1.1 `test_phase2_integration.py` → `test_fiscal_integration_social_security_revenue.py`
**Purpose:** Tests Social Security + Federal Revenue integration

**Current class/test names:**
- `TestPhase2ConfigurationLoading` → `TestFiscalPolicyConfigurationLoading`
- `test_social_security_scenarios_load` → Keep (descriptive)
- `test_tax_reform_scenarios_load` → Keep (descriptive)

#### 1.2 `test_phase2_validation.py` → `test_baseline_validation_cbo_ssa.py`
**Purpose:** Tests CBO/SSA baseline data validation

**Current class/test names:**
- `TestCBOBaselineData` → Keep (descriptive)
- `TestSSABaselineData` → Keep (descriptive)
- `TestPhase2Validator` → `TestBaselineValidator`

#### 1.3 `test_phase2b_edge_cases.py` → `test_edge_cases_fiscal_models.py`
**Purpose:** Edge cases for Social Security and Revenue models

**Current class/test names:**
- `TestEdgeCases` → `TestFiscalModelEdgeCases`

#### 1.4 `test_phase2_integration_engine.py` → `test_tax_reform_integration.py`
**Purpose:** Tax reform policy package integration

**Current class/test names:**
- `TestPhase2PolicyPackage` → `TestTaxReformPolicyPackage`
- `TestPhase2SimulationEngine` → `TestTaxReformSimulationEngine`
- `TestPhase2ReformPackages` → `TestReformPackagePresets`

#### 1.5 `test_phase32_integration.py` → `test_fiscal_integration_discretionary_interest.py`
**Purpose:** Discretionary spending + Interest + Combined outlook

**Current class/test names:**
- `TestDiscretionarySpending` → Keep (descriptive)
- `TestInterestOnDebt` → Keep (descriptive)
- `TestCombinedFiscalOutlook` → Keep (descriptive)

#### 1.6 `test_phase_6_2_3_secrets.py` → `test_secrets_management.py`
**Purpose:** Secrets management and configuration

**Current class/test names:**
- `TestSecretsManager` → Keep (descriptive)
- `TestConfigurationManager` → Keep (descriptive)
- `TestSecretRotation` → Keep (descriptive)

#### 1.7 `test_slice_5_6_integration.py` → `test_scenario_builder_reports.py`
**Purpose:** Scenario builder + Report generation workflows

**Current class/test names:**
- `TestPolicyLibraryWorkflow` → Keep (descriptive)
- `TestScenarioBundleWorkflow` → Keep (descriptive)
- `TestReportGenerationWorkflow` → Keep (descriptive)

#### 1.8 `test_slice_5_7_api.py` → `test_api_v1_endpoints.py`
**Purpose:** API v1 endpoint contract tests

**Current class/test names:**
- `TestSimulateEndpoint` → Keep (descriptive)
- `TestScenariosEndpoint` → Keep (descriptive)
- `TestHealthEndpoint` → Keep (descriptive)

---

### Phase 2: Update Internal Class/Test Names

For each renamed file, update internal references:
1. Update class names to remove phase/slice references
2. Update docstrings to describe actual functionality
3. Ensure test discovery still works

---

### Phase 3: Add New Validation Tests (~85 tests per Slice 6.5 spec)

#### 3.1 Baseline Reconciliation Tests (25 tests)
Create `test_baseline_reconciliation.py`:
- GDP projection vs CBO ±1%
- Revenue by category vs CBO ±2%
- Spending categories vs CBO ±3%
- Deficit trajectory vs CBO ±2%
- Debt held by public vs CBO ±3%
- OASI trust fund vs SSA
- Payroll tax revenue vs SSA
- Benefit payments vs SSA
- DI fund status vs SSA
- Medicare enrollment vs CMS
- Per-capita spending growth vs CMS

#### 3.2 Expert Scenario Tests (30 tests)
Create `test_expert_scenario_validation.py`:
- Healthcare assumption scenarios
- Revenue/tax assumption scenarios
- Mandatory spending scenarios
- Economic assumption scenarios
- Cross-validation with expert parameters

#### 3.3 Regression Tests (20 tests)
Create `test_regression_suite.py`:
- Core simulation outputs unchanged
- API response format unchanged
- Report generation unchanged
- Policy extraction unchanged
- Monte Carlo convergence unchanged

#### 3.4 Load Tests (10 tests)
Create `test_load_performance.py`:
- 100 concurrent API requests
- 1000 scenario simulations
- Large PDF processing (50+ pages)
- Monte Carlo with 100k iterations
- Report generation with large datasets

---

### Phase 4: Update Documentation

#### 4.1 Update `tests/README.md`
- Document new naming conventions
- Add test category descriptions
- Update coverage goals
- Add examples for each category

#### 4.2 Create Test Naming Convention Guide
- File naming: `test_{domain}_{feature}.py`
- Class naming: `Test{Feature}{Aspect}`
- Function naming: `test_{action}_{expected_result}`

---

## File Rename Mapping

| Current Path | New Path |
|--------------|----------|
| `tests/test_phase2_integration.py` | `tests/test_fiscal_integration_social_security_revenue.py` |
| `tests/test_phase2_validation.py` | `tests/test_baseline_validation_cbo_ssa.py` |
| `tests/test_phase2b_edge_cases.py` | `tests/test_edge_cases_fiscal_models.py` |
| `tests/test_phase2_integration_engine.py` | `tests/test_tax_reform_integration.py` |
| `tests/test_phase32_integration.py` | `tests/test_fiscal_integration_discretionary_interest.py` |
| `tests/test_phase_6_2_3_secrets.py` | `tests/test_secrets_management.py` |
| `tests/test_slice_5_6_integration.py` | `tests/test_scenario_builder_reports.py` |
| `tests/test_slice_5_7_api.py` | `tests/test_api_v1_endpoints.py` |

---

## Internal Class Rename Mapping

### test_phase2_integration.py → test_fiscal_integration_social_security_revenue.py
| Current | New |
|---------|-----|
| `TestPhase2ConfigurationLoading` | `TestFiscalPolicyConfigLoading` |
| `TestSocialSecurityIntegration` | Keep |
| `TestRevenueIntegration` | Keep |
| `TestCombinedProjections` | Keep |

### test_phase2_validation.py → test_baseline_validation_cbo_ssa.py
| Current | New |
|---------|-----|
| `TestCBOBaselineData` | Keep |
| `TestSSABaselineData` | Keep |
| `TestValidationMetrics` | Keep |
| `TestPhase2Validator` | `TestBaselineValidator` |

### test_phase2b_edge_cases.py → test_edge_cases_fiscal_models.py
| Current | New |
|---------|-----|
| `TestEdgeCases` | `TestFiscalModelEdgeCases` |

### test_phase2_integration_engine.py → test_tax_reform_integration.py
| Current | New |
|---------|-----|
| `TestPhase2PolicyPackage` | `TestTaxReformPolicyPackage` |
| `TestPhase2SimulationEngine` | `TestTaxReformSimulationEngine` |
| `TestPhase2ReformPackages` | `TestReformPackagePresets` |
| `TestPhase2ComparisonScenarios` | `TestTaxReformComparisonScenarios` |

### test_phase32_integration.py → test_fiscal_integration_discretionary_interest.py
| Current | New |
|---------|-----|
| All classes are already descriptive | Keep all |

### test_phase_6_2_3_secrets.py → test_secrets_management.py
| Current | New |
|---------|-----|
| All classes are already descriptive | Keep all |

### test_slice_5_6_integration.py → test_scenario_builder_reports.py
| Current | New |
|---------|-----|
| All classes are already descriptive | Keep all |

### test_slice_5_7_api.py → test_api_v1_endpoints.py
| Current | New |
|---------|-----|
| All classes are already descriptive | Keep all |

---

## Implementation Checklist

### Phase 1: File Renames
- [ ] Rename `test_phase2_integration.py` → `test_fiscal_integration_social_security_revenue.py`
- [ ] Rename `test_phase2_validation.py` → `test_baseline_validation_cbo_ssa.py`
- [ ] Rename `test_phase2b_edge_cases.py` → `test_edge_cases_fiscal_models.py`
- [ ] Rename `test_phase2_integration_engine.py` → `test_tax_reform_integration.py`
- [ ] Rename `test_phase32_integration.py` → `test_fiscal_integration_discretionary_interest.py`
- [ ] Rename `test_phase_6_2_3_secrets.py` → `test_secrets_management.py`
- [ ] Rename `test_slice_5_6_integration.py` → `test_scenario_builder_reports.py`
- [ ] Rename `test_slice_5_7_api.py` → `test_api_v1_endpoints.py`

### Phase 2: Internal Updates
- [ ] Update class names in renamed files
- [ ] Update docstrings to describe functionality
- [ ] Update any import references

### Phase 3: New Tests
- [ ] Create `test_baseline_reconciliation.py` (25 tests)
- [ ] Create `test_expert_scenario_validation.py` (30 tests)
- [ ] Create `test_regression_suite.py` (20 tests)
- [ ] Create `test_load_performance.py` (10 tests)

### Phase 4: Documentation
- [ ] Update `tests/README.md` with new structure
- [ ] Add test naming convention guide
- [ ] Update main `README.md` test section

### Phase 5: Verification
- [ ] Run full test suite
- [ ] Verify test count matches expected
- [ ] Check CI/CD still works (if applicable)

---

## Acceptance Criteria

1. **No more phase/slice named test files** - All files describe functionality
2. **All tests pass** - No regressions from renaming
3. **README updated** - Clear documentation of test structure
4. **~85 new validation tests** - Per Slice 6.5 spec:
   - 25 baseline reconciliation tests
   - 30 expert scenario tests  
   - 20 regression tests
   - 10 load tests
5. **Consistent naming** - All test classes/functions describe what they test

---

## Timeline

| Task | Hours | Priority |
|------|-------|----------|
| Phase 1: File renames | 2-3 | High |
| Phase 2: Internal updates | 4-6 | High |
| Phase 3: New tests | 20-30 | Medium |
| Phase 4: Documentation | 4-6 | Medium |
| Phase 5: Verification | 2-3 | High |
| **Total** | **32-48** | |

---

## Notes

- Some files like `test_performance_sprint44.py` could be renamed to `test_performance_benchmarks.py` in a future cleanup
- Bug-specific tests (`test_bug_*.py`) could be consolidated into domain-specific files once verified fixed
- Import test files (`test_import_*.py`) are debugging utilities and can remain as-is

