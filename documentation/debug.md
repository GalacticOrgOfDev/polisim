# Debug Log - Policy Extraction Issues

## Date: December 24, 2025

### Issue 1: USGHA Extraction Incomplete (6/10+ mechanisms found)

**Status:** CRITICAL BUG

**Description:**
USGHA v1.22 extraction shows only 6 funding mechanisms when the legislation defines 10+ distinct funding sources.

**Mechanisms Found by Extractor:**
1. payroll_tax (0.1% - INCORRECT RATE)
2. efficiency_gains (3% GDP)
3. transaction_tax (1%)
4. excise_reallocation (1%)
5. import_tariffs (12%)
6. reinsurance_pool

**Mechanisms Missing from Extraction:**
- Redirected federal health expenditures (Medicare, Medicaid, CHIP, VA, ACA, HHS) - Section 6(b)(1)
- Converted employer/employee premiums → payroll contributions - Section 6(b)(2)
- Consolidated nutrition/social programs (SNAP, WIC, school lunch) - Section 6(b)(6)
- Pharmaceutical pricing savings (most-favored-nation-minus-20%) - Section 6(c)(3)

**Root Cause:**
`_extract_generic_funding()` in `core/policy_mechanics_extractor.py` (lines 728-828) uses narrow regex patterns that don't capture:
- Federal program consolidation language
- Premium-to-payroll conversion mechanisms
- Pharmaceutical pricing reform savings

**Impact:**
- Simulator accuracy compromised (missing ~40% of funding sources)
- Financial projections will be incomplete
- Dashboard UI shows misleading data

---

### Issue 2: Payroll Tax Percentage Incorrect (0.1% vs 15% cap)

**Status:** CRITICAL BUG

**Description:**
USGHA extraction shows "0.1% payroll tax" when the legislation explicitly caps combined payroll at 15% (Section 6(e)).

**Expected:**
- Rate: 15% (capped)
- Description: "Combined employer/employee payroll capped at 15%, with 45% allocated to Trust Fund"

**Actual:**
- Rate: 0.1%
- Description: "0.1% payroll tax"

**Root Cause:**
Regex at line 734-740 in `_extract_generic_funding()`:
```python
payroll_match = re.search(
    r'payroll\s+(?:tax|contribution)[^.]*?(\d+(?:\.\d+)?)\s*percent',
    text,
    re.IGNORECASE
)
```

This pattern is:
1. Too greedy - matches ANY percentage near "payroll" keyword
2. Doesn't validate ranges (0.1% is implausible for national healthcare)
3. Picks up wrong percentages from context (likely "0.1 percent of GDP" for contingency funds)

**USGHA Text Analysis:**
- "0.1" appears 4 times in USGHA text, all referring to GDP-based contingency funds, NOT payroll rates
- "15 percent" appears as the explicit payroll cap in Section 6(e)

**Fix Required:**
1. Add validation: payroll rates should be 5-20% range for healthcare
2. Prioritize "cap" or "maximum" keywords over generic percentage matches
3. Look for explicit rate statements vs. incidental percentage mentions

---

### Issue 3: M4A Extraction Incomplete (2/4+ mechanisms found)

**Status:** RESOLVED - M4A bill text intentionally lacks funding details

**Description:**
M4A (S.1655) extraction shows only 1 funding mechanism (pharmaceutical_savings at 1.5% GDP).

**Investigation Results:**
Analyzed BILLS-118s1655is.pdf (172,911 characters):
- payroll tax: 0 mentions
- income tax: 0 mentions  
- premium redirect: 22 mentions (but no percentages or rates)
- employer/employee contributions: 0 mentions with rates
- excise/transaction/tariff taxes: 0 mentions

**Root Cause:**
M4A (S.1655) is a **BENEFITS BILL**, not a comprehensive policy with funding.
- Focuses on coverage, eligibility, benefits, provider payments
- Does NOT include explicit tax rates or funding mechanisms
- Sanders' office released separate funding proposals (not in bill text)

**Resolution:**
This is NOT a bug - M4A intentionally defers funding to separate legislation or proposals.

**Recommendation:**
To simulate M4A scenarios, we need to:
1. Document that S.1655 lacks explicit funding (extraction is correct)
2. Create companion scenario based on Sanders' published funding proposals:
   - 7.5% employer payroll tax
   - 4% income-based premium (household)
   - Marginal income tax increases on $250k+
   - Capital gains taxed as ordinary income
   - Wealth tax on net worth $32M+
   - Financial transaction tax (0.5% stocks, 0.1% bonds)
3. Label clearly: "M4A Benefits (S.1655)" vs "M4A Funding Proposal (Sanders 2019)"

**Impact:**
- Extraction system is working correctly
- Need separate policy file for M4A funding mechanisms
- Current extraction: 1 mechanism (correct for bill text)
- With funding proposal: 6+ mechanisms (needs separate scenario)

---

### Issue 4: Context Framework Taxonomy Gaps

**Status:** HIGH PRIORITY - FRAMEWORK INCOMPLETE

**Description:**
`policy_context_framework.py` single-payer taxonomy is missing critical funding concept patterns.

**Current Patterns (lines 105-200):**
- universal_coverage ✓
- zero_cost_sharing ✓
- payroll_tax_funding ✓
- income_tax_funding ✓
- existing_spending_redirect ✓
- administrative_savings ✓

**Missing Patterns:**
- transaction_tax_funding (for FTT/financial transaction taxes)
- excise_tax_funding (for excise reallocations)
- tariff_funding (for import tariff allocations)
- premium_conversion (for employer/employee premium → payroll)
- program_consolidation (for SNAP/WIC/federal program mergers)
- pharmaceutical_savings (for drug pricing reforms)
- reinsurance_mechanisms (for high-cost risk pools)

**Impact:**
- Context-aware extraction can only detect 6 out of 10+ funding types
- New bill formats with diverse funding won't be recognized
- Framework can't achieve "gold standard" extraction without these patterns

---

### Issue 5: Percentage Extraction Quality Issues

**Status:** RESOLVED - Context classification implemented

**Description:**
`QuantityExtractor.extract_percentage()` extracted ALL percentages without context validation, leading to false positives.

**Problems:**
1. ✓ FIXED: No filtering for plausible ranges (0.1% payroll is implausible)
2. ✓ FIXED: No keyword association (can't tell if percentage relates to tax, GDP, or efficacy)
3. ✓ FIXED: No confidence scoring based on proximity to funding keywords

**Solution Implemented:**
Added `context_type` parameter to `extract_percentage()` with three classification modes:

```python
QuantityExtractor.extract_percentage(text, context_type='tax_rate')
# Options: 'tax_rate', 'gdp', 'efficacy', None
```

**Features:**
1. **Context Filtering**: Only extracts percentages near relevant keywords
   - tax_rate: Requires keywords: tax, payroll, income, rate, levy, contribution
   - gdp: Requires keywords: gdp, gross domestic product, economy
   - efficacy: Requires keywords: effective, probability, evidence, success
   
2. **Range Validation**: Type-specific range checks
   - tax_rate: 1-50% (rejects implausible values like 0.1% or 100%)
   - gdp: 0-50%
   - efficacy: 0-100%
   
3. **Proximity-Based Confidence**: 
   - Keywords within 50 chars: 0.9 confidence
   - Keywords within 200 chars: 0.75 confidence
   - Base: 0.7 confidence

**Validation:**
Tested on USGHA text:
- ✓ Correctly extracts 15% payroll with 'tax_rate' context
- ✓ Filters out 0.1% GDP contingency (not a tax rate)
- ✓ Context-less extraction finds all percentages (backward compatible)
- ✓ End-to-end test: USGHA still shows 15% payroll, 11 mechanisms, 22.19% GDP

**Impact:**
- Reduces false positives in funding mechanism extraction
- Improves confidence scoring accuracy
- Backward compatible (context_type=None preserves old behavior)
- Ready for production use

---

## Recommended Fix Priority:

1. **CRITICAL:** Fix payroll percentage regex (Issue 2) - prevents wrong data in UI
2. **CRITICAL:** Add missing funding patterns to `_extract_generic_funding()` (Issue 1)
3. **HIGH:** Expand context framework taxonomy with 7 missing patterns (Issue 4)
4. **HIGH:** Improve M4A detection by adding premium conversion patterns (Issue 3)
5. **MEDIUM:** Add percentage context classification (Issue 5)

---

## Fine-Tooth-Comb Step-Through (Per Instructions)

### Step 1: Trace USGHA Extraction Path
1. User uploads PDF → `dashboard.py:policy_upload_section()`
2. Calls `PolicyPDFProcessor.analyze_policy_text()`
3. Calls `extract_policy_mechanics()` → routes to `extract_with_context_awareness()`
4. Context framework returns: policy_type="single_payer", 21 concepts found
5. Standard extraction via `extract_generic_healthcare_mechanics()`
6. Calls `_extract_generic_funding()` → returns 6 mechanisms
7. Context enhancement adds 0 additional mechanisms (already found by standard)

### Step 2: Analyze Why Mechanisms Missed
- **Redirected federal**: Pattern `r'(?:federal\s+health|Medicare|Medicaid)[^.]*?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:GDP|gross\s+domestic\s+product)'`
  - USGHA text: "Redirection of existing federal health expenditures (Medicare, Medicaid, CHIP, VA, ACA...)"
  - NO percentage attached to this list → regex fails
  
- **Premium conversion**: No pattern exists for `r'(?:employer|employee)[^.]*?premium[^.]*?converted'`
  
- **Program consolidation**: No pattern for SNAP/WIC/nutrition programs as funding

### Step 3: Analyze Payroll 0.1% Bug
USGHA text search for "0.1":
- Line 1: "equivalent to 0.1 percent of the prior fiscal year's federal health expenditures" (contingency reserve)
- Line 2: "0.1 percent of the prior fiscal year's nominal gross domestic product" (multiplanetary funding)
- Line 3: "up to 0.1 percent of the prior fiscal year's federal health expenditures" (provider stabilization)
- Line 4: "0.1 percent of the prior fiscal year's federal health expenditures" (AI-assisted training)

None refer to payroll tax rate. The regex is capturing these GDP/contingency references.

USGHA text search for "15 percent":
- Section 6(e): "The total combined payroll tax rate (including employer and employee shares) **shall be capped at 15 percent**"

The regex should prioritize "cap" or "maximum" keywords over generic percentage proximity.

---

## Action Items for Resolution:

### Immediate (Today):
- [x] Document bugs in this file
- [x] Update `_extract_generic_funding()` regex patterns
- [x] Add payroll rate validation (5-20% range)
- [x] Fix payroll regex to prioritize "cap"/"maximum" keywords

### Short-term (This Week):
- [x] Expand single_payer taxonomy with 7 missing funding patterns
- [x] Add premium conversion detection
- [x] Test on M4A to verify mechanisms detected (1 found - correct for bill text)
- [x] Test on USGHA to verify 10+ mechanisms detected (11 found - SUCCESS)

### Medium-term (Next Sprint):
- [x] Add percentage context classification
- [x] Implement confidence scoring based on keyword proximity
- [x] Create validation rules for implausible rates

---

## RESOLUTION SUMMARY (December 24, 2025)

**All 5 Issues Resolved:**

✅ **Issue 1**: USGHA now extracts 11/11 mechanisms (was 6/10)
- Added 8 new funding patterns to `_extract_generic_funding()`
- Total revenue: 22.19% GDP (up from 16.10% in old scenarios)

✅ **Issue 2**: Payroll tax correctly shows 15% (was 0.1%)
- Bidirectional regex searches both "cap...payroll...15%" and "payroll...capped...15%"
- Range validation: Only accepts 5-25% for payroll taxes
- GDP conversion: 15% payroll × 53% wage share = 7.95% GDP

✅ **Issue 3**: M4A extraction working correctly (1 mechanism)
- M4A (S.1655) is a benefits bill without explicit funding mechanisms
- Only pharmaceutical savings (1.5% GDP) explicitly mentioned
- Sanders' separate funding proposals need separate scenario file

✅ **Issue 4**: Context framework taxonomy expanded (6→16 categories)
- Added patterns for: transaction_tax, excise_tax, tariff, premium_conversion, 
  program_consolidation, pharmaceutical_savings, reinsurance, dsh_gme, 
  inflation_adjustment, eitc_rebate
- Rebalanced scoring weights across all concepts

✅ **Issue 5**: Percentage extraction with context classification
- Added context_type parameter: 'tax_rate', 'gdp', 'efficacy'
- Keyword proximity filtering (50 chars = high confidence, 200 chars = medium)
- Range validation: tax_rate (1-50%), gdp (0-50%), efficacy (0-100%)
- Successfully filters 0.1% GDP contingencies from tax rate extraction

**Validation Results:**
- USGHA Extraction: 11 mechanisms, 22.19% GDP, 15% payroll ✓
- Simulation: $0 final debt, $52.89T debt reduction ✓
- Per-capita: $10,178 in 2045 (62% reduction from baseline) ✓
- User Satisfaction: "those results are flippin beautiful!!" ✓

**Next Steps:**
Follow `debug.md` → resolve issues found → update extraction accuracy to meet "gold standard" requirement from project guidelines.
