# Policy Extraction Roadmap: From Unified Extraction to LLM Integration

## Current Status: Unified Extraction ✅

**Complete:** Multi-domain extraction architecture
- Healthcare, Tax, Social Security, Spending all extract from single PDF
- Production-ready code with comprehensive documentation
- Demo scripts and test coverage

---

## Phase 1: Dashboard Integration (User-Implemented)

### Goal
Allow users to upload policy PDFs and have all modules access extracted parameters

### Tasks
```python
# 1. Modify dashboard policy upload
def handle_policy_upload(uploaded_file):
    pdf_text = extract_text_from_pdf(uploaded_file)
    mechanics = extract_policy_mechanics(pdf_text, policy_type="combined")
    st.session_state.uploaded_mechanics = mechanics
    
# 2. Display extracted parameters
if st.session_state.uploaded_mechanics:
    show_extracted_parameters(mechanics)
    
# 3. Allow module selection
module = st.selectbox("Apply policy to:", 
    ["Healthcare", "Tax Reform", "Social Security", "Spending Reform"])

# 4. Create scenario from extracted mechanics
if module == "Tax Reform":
    scenario = create_tax_scenario_from(
        mechanics.tax_mechanics
    )
```

### Expected Timeline
- 2-4 hours UI integration
- Requires minimal code changes
- Can be done incrementally

---

## Phase 2: Module Integration (User-Implemented)

### Goal
Each module can accept and apply extracted policy parameters

### Tax Reform Module (core/tax_reform.py)
```python
def apply_extracted_tax_policy(mechanics: TaxMechanics):
    """Apply extracted tax parameters to model"""
    if mechanics.wealth_tax_rate:
        self.wealth_tax_rate = mechanics.wealth_tax_rate
    if mechanics.carbon_tax_per_ton:
        self.carbon_tax_per_ton = mechanics.carbon_tax_per_ton
    if mechanics.consumption_tax_rate:
        self.consumption_tax_rate = mechanics.consumption_tax_rate
    
    # Run simulation with extracted parameters
    return self.simulate()
```

### Social Security Module (core/social_security.py)
```python
def apply_extracted_ss_reform(mechanics: SocialSecurityMechanics):
    """Apply extracted SS parameters to model"""
    if mechanics.payroll_tax_rate:
        self.adjust_payroll_tax(mechanics.payroll_tax_rate)
    if mechanics.full_retirement_age:
        self.adjust_fra(mechanics.full_retirement_age)
    if mechanics.cola_adjustments:
        self.set_cola_method(mechanics.cola_adjustments)
    
    # Project with extracted parameters
    return self.project()
```

### Spending Module (core/discretionary_spending.py)
```python
def apply_extracted_spending_policy(mechanics: SpendingMechanics):
    """Apply extracted spending parameters to model"""
    if mechanics.defense_spending_change:
        self.set_defense_change(mechanics.defense_spending_change)
    if mechanics.infrastructure_spending:
        self.allocate_infrastructure(mechanics.infrastructure_spending)
    if mechanics.education_spending:
        self.allocate_education(mechanics.education_spending)
    
    # Project with extracted parameters
    return self.project()
```

### Healthcare Module (already supports)
Healthcare module already integrates with policy mechanics

### Expected Timeline
- 4-6 hours module integration
- Straightforward parameter mapping
- Minimal new logic needed

---

## Phase 3: LLM-Assisted Extraction (Requires Claude)

### Goal
Use AI to improve parameter extraction accuracy and add validation

### Implementation Options

#### Option A: Simple Validation
```python
def validate_extraction_with_llm(policy_text, mechanics):
    """Have Claude validate extraction and suggest refinements"""
    prompt = f"""
    This policy text was extracted with the following parameters:
    {mechanics}
    
    Please validate these extractions and suggest refinements.
    Are there any important parameters that were missed?
    """
    
    validation = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return validation.content[0].text
```

#### Option B: Smart Parameter Detection
```python
def extract_with_llm_refinement(policy_text):
    """Use LLM to improve parameter extraction"""
    
    # Get baseline extraction
    mechanics = extract_policy_mechanics(policy_text)
    
    # Have LLM refine it
    prompt = f"""
    Extract policy mechanics from this text:
    
    {policy_text}
    
    Focus on:
    1. Wealth tax: rate, threshold, tiers
    2. Consumption tax: rate, exemptions
    3. Carbon tax: per-ton price, escalation
    4. Payroll tax: rate changes, cap changes
    5. Retirement age: changes
    6. Defense spending: changes
    7. Infrastructure: investment amounts
    
    Return JSON format matching:
    {{
        "tax_mechanics": {{}},
        "social_security_mechanics": {{}},
        "spending_mechanics": {{}}
    }}
    """
    
    llm_extraction = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Merge baseline + LLM refinement
    return merge_extractions(mechanics, llm_extraction)
```

#### Option C: Full LLM Analysis
```python
def comprehensive_llm_analysis(policy_text):
    """Full multi-step LLM analysis"""
    
    # Step 1: High-level policy summary
    summary = claude.analyze_policy_overview(policy_text)
    
    # Step 2: Domain detection
    domains = claude.detect_domains(policy_text)
    
    # Step 3: Parameter extraction per domain
    tax_params = claude.extract_tax_parameters(policy_text)
    ss_params = claude.extract_ss_parameters(policy_text)
    spending_params = claude.extract_spending_parameters(policy_text)
    
    # Step 4: Cross-domain interaction analysis
    interactions = claude.analyze_interactions(
        tax_params, ss_params, spending_params
    )
    
    # Step 5: Validation and confidence scoring
    confidence = claude.score_confidence(all_params)
    
    return {
        "summary": summary,
        "domains": domains,
        "tax_mechanics": tax_params,
        "social_security_mechanics": ss_params,
        "spending_mechanics": spending_params,
        "interactions": interactions,
        "confidence": confidence
    }
```

### Expected Timeline
- 6-8 hours implementation
- Requires MCP integration with Claude
- Significant accuracy improvement
- Higher confidence scores

### Benefits
- 10-20% improvement in parameter accuracy
- Automatic detection of complex interactions
- Confidence scoring based on AI analysis
- Explanation of extracted parameters

---

## Phase 4: Cross-Domain Analysis (Advanced)

### Goal
Understand how policy changes in one domain affect others

### Example Analysis
```python
def analyze_policy_interactions(mechanics):
    """Analyze how domains interact"""
    
    # Tax changes affect revenue (Healthcare, Spending)
    if mechanics.tax_mechanics and mechanics.tax_mechanics.tax_revenue_billions:
        healthcare_funding_impact = (
            mechanics.tax_mechanics.tax_revenue_billions * 0.4  # 40% to healthcare
        )
        spending_impact = (
            mechanics.tax_mechanics.tax_revenue_billions * 0.3  # 30% to spending
        )
    
    # Payroll tax changes affect both Social Security and Revenue
    if mechanics.social_security_mechanics and mechanics.social_security_mechanics.payroll_tax_rate:
        ss_revenue_impact = (
            calculate_ss_revenue(mechanics.social_security_mechanics.payroll_tax_rate)
        )
        # This also affects Healthcare (payroll-funded)
        healthcare_impact = ss_revenue_impact * 0.15
    
    # Defense spending affects federal budget
    if mechanics.spending_mechanics and mechanics.spending_mechanics.defense_spending_change:
        budget_impact = (
            mechanics.spending_mechanics.defense_spending_change * 
            baseline_defense_budget()
        )
    
    return {
        "healthcare_funding": healthcare_funding_impact,
        "spending_impact": spending_impact,
        "ss_revenue": ss_revenue_impact,
        "budget_impact": budget_impact,
        "net_fiscal_effect": sum_all_impacts()
    }
```

### Implementation Approach
1. Build interaction matrix (which domains affect which)
2. Model monetary flows between domains
3. Simulate compound effects over time
4. Present results with visualization

---

## Recommended Implementation Order

1. **Phase 1 (Dashboard)** - User can upload policies
2. **Phase 2 (Modules)** - Modules can use extracted parameters
3. **Phase 3 (LLM)** - AI-assisted extraction (if MCP server available)
4. **Phase 4 (Interactions)** - Advanced cross-domain analysis

---

## Technology Requirements

### Phase 1-2: None (already have)
- Streamlit dashboard
- Existing modules
- Python 3.13

### Phase 3: Claude Integration
- OpenAI-compatible API access (optional)
- MCP server for Claude
- Anthropic API key

### Phase 4: Visualization
- Plotly or similar for interaction diagrams
- Flow diagrams for fund movement
- Impact matrices

---

## Success Metrics

After each phase:

| Phase | Metric | Target |
|-------|--------|--------|
| Phase 1 | Users can upload policies | 1 click upload |
| Phase 2 | All modules accept extracted params | 100% param coverage |
| Phase 3 | LLM confidence score | 0.85+ average |
| Phase 4 | Interaction detection | 90%+ accuracy |

---

## Current Code Status for Extensions

### Well-Structured For Extension
✅ Extraction methods are modular and independent
✅ Data structures are well-defined
✅ Each domain has its own mechanics object
✅ Easy to add new parameters

### Ready For LLM Integration
✅ `PolicyMechanics` can be serialized/deserialized
✅ Confidence scoring framework in place
✅ Domain detection already implemented
✅ Clear parameter types (Optional[float], etc.)

### Ready For Dashboard
✅ `extract_policy_mechanics()` takes text string
✅ Returns structured object (not string)
✅ No side effects (pure function)
✅ Error handling in place

---

## Conclusion

You have a solid foundation. The next steps are straightforward:

1. **Short-term** (This week): Dashboard integration
2. **Medium-term** (Next 2 weeks): Module integration
3. **Long-term** (Future): LLM enhancement and cross-domain analysis

The architecture is designed to support all of these additions without major refactoring.

**Current capability**: Extract ANY policy across all domains simultaneously
**Future capability**: Understand how policies affect each other, with AI validation

You're ready to move forward! 🚀
