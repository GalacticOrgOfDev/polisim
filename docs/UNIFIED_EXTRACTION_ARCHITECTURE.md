# Unified Policy Extraction Architecture

## Overview

The **Unified Policy Extraction System** allows a single PDF policy document to be analyzed across ALL policy domains simultaneously:

- **Healthcare** - Coverage, premiums, funding mechanisms
- **Tax Reform** - Wealth tax, consumption tax, carbon tax, income tax changes
- **Social Security** - Payroll tax changes, retirement age, benefit formulas
- **Spending Reform** - Defense, infrastructure, education, research budgets

When a policy PDF is uploaded, it's automatically analyzed for content in all domains, and each extracted parameter is stored in a centralized `PolicyMechanics` object that all modules can access.

## Architecture

### Core Data Structure: `PolicyMechanics`

The `PolicyMechanics` dataclass is the unified container for all extracted policy information:

```python
@dataclass
class PolicyMechanics:
    policy_name: str
    policy_type: str  # "combined", "healthcare", "tax_reform", etc.
    
    # Core mechanisms (healthcare-focused)
    funding_mechanisms: List[FundingMechanism]
    surplus_allocation: Optional[SurplusAllocation]
    circuit_breakers: List[CircuitBreaker]
    innovation_fund: Optional[InnovationFundRules]
    timeline_milestones: List[TimelineMilestone]
    
    # Domain-specific mechanics
    tax_mechanics: Optional[TaxMechanics]           # Tax-related parameters
    social_security_mechanics: Optional[SocialSecurityMechanics]  # SS-related parameters
    spending_mechanics: Optional[SpendingMechanics]  # Spending-related parameters
    
    # Metadata
    confidence_score: float
    source_sections: Dict[str, str]
    unfunded: bool
```

### Domain-Specific Data Structures

#### TaxMechanics
```python
@dataclass
class TaxMechanics:
    wealth_tax_rate: Optional[float]
    wealth_tax_threshold: Optional[float]
    wealth_tax_tiers: Dict[str, float]
    
    consumption_tax_rate: Optional[float]
    consumption_tax_exemptions: List[str]
    consumption_tax_rebate: Optional[float]
    
    carbon_tax_per_ton: Optional[float]
    carbon_tax_annual_increase: Optional[float]
    carbon_revenue_allocation: Dict[str, float]
    
    financial_transaction_tax_rate: Optional[float]
    income_tax_changes: Dict[str, Any]
    corporate_tax_rate: Optional[float]
    payroll_tax_rate: Optional[float]
    
    tax_revenue_billions: Optional[float]
    estimated_tax_revenue_growth: Optional[float]
```

#### SocialSecurityMechanics
```python
@dataclass
class SocialSecurityMechanics:
    payroll_tax_rate: Optional[float]
    payroll_tax_cap_change: Optional[str]  # "remove_cap", "increase_cap"
    payroll_tax_cap_increase: Optional[float]
    
    full_retirement_age: Optional[int]
    full_retirement_age_change: Optional[int]
    
    benefit_formula_changes: Dict[str, Any]
    cola_adjustments: Optional[str]
    
    means_testing_threshold: Optional[float]
    means_testing_enabled: bool
    
    early_claiming_reduction: Optional[float]
    delayed_claiming_credit: Optional[float]
    
    demographic_assumptions: Dict[str, float]
    trust_fund_solvency_year: Optional[int]
    estimated_year_deficit: Optional[float]
```

#### SpendingMechanics
```python
@dataclass
class SpendingMechanics:
    defense_spending_change: Optional[float]
    defense_spending_cap: Optional[float]
    
    nondefense_discretionary_change: Optional[float]
    nondefense_categories: Dict[str, float]
    
    infrastructure_spending: Optional[float]
    education_spending: Optional[float]
    research_spending: Optional[float]
    
    spending_growth_rate: Optional[float]
    inflation_adjustment: Optional[float]
    
    budget_caps_enabled: bool
    budget_cap_levels: Dict[str, float]
```

## Extraction Flow

### 1. Content Detection

The system detects which policy domains are present in the text:

```python
def extract_policy_mechanics(text: str, policy_type: str = "combined") -> PolicyMechanics:
    # Auto-detect which domains are present
    if _detect_healthcare_content(text):
        # Extract healthcare mechanisms
    if _detect_tax_content(text):
        # Extract tax mechanics
    if _detect_social_security_content(text):
        # Extract SS mechanics
    if _detect_spending_content(text):
        # Extract spending mechanics
```

Detection uses keyword matching to identify content:
- **Healthcare**: "healthcare", "coverage", "insurance", "premiums", "Medicare", "Medicaid"
- **Tax**: "wealth tax", "consumption tax", "carbon tax", "tax rate", "revenue"
- **Social Security**: "payroll tax", "full retirement age", "benefit formula", "OASDI"
- **Spending**: "defense", "infrastructure", "education", "budget cap"

### 2. Parallel Extraction

Once domains are detected, each is extracted independently:

```python
# Healthcare extraction
if "healthcare" in detected_types:
    mechanics.funding_mechanisms = ...
    mechanics.surplus_allocation = ...
    
# Tax extraction
if "tax" in detected_types:
    mechanics.tax_mechanics = PolicyMechanicsExtractor._extract_tax_mechanics(text)
    
# Social Security extraction
if "social_security" in detected_types:
    mechanics.social_security_mechanics = PolicyMechanicsExtractor._extract_social_security_mechanics(text)
    
# Spending extraction
if "spending" in detected_types:
    mechanics.spending_mechanics = PolicyMechanicsExtractor._extract_spending_mechanics(text)
```

### 3. Return Unified Object

A single `PolicyMechanics` object containing ALL extracted information is returned. Each module can then access only the fields it needs:

```python
# Healthcare module access
healthcare_model.apply_policy(mechanics.funding_mechanisms, mechanics.surplus_allocation)

# Tax module access
tax_model.apply_wealth_tax(mechanics.tax_mechanics.wealth_tax_rate)
tax_model.apply_carbon_tax(mechanics.tax_mechanics.carbon_tax_per_ton)

# Social Security module access
ss_model.adjust_payroll_tax(mechanics.social_security_mechanics.payroll_tax_rate)
ss_model.adjust_fra(mechanics.social_security_mechanics.full_retirement_age)

# Spending module access
spending_model.set_infrastructure_budget(mechanics.spending_mechanics.infrastructure_spending)
```

## Integration with Modules

### Tax Reform Module (core/tax_reform.py)

To use extracted tax mechanics:

```python
from core.policy_mechanics_extractor import extract_policy_mechanics

# Extract from uploaded policy
pdf_text = load_pdf_as_text(uploaded_file)
mechanics = extract_policy_mechanics(pdf_text, policy_type="combined")

# Apply to tax model
if mechanics.tax_mechanics:
    tax_model = TaxReformModel(
        wealth_tax_rate=mechanics.tax_mechanics.wealth_tax_rate,
        wealth_tax_threshold=mechanics.tax_mechanics.wealth_tax_threshold,
        consumption_tax_rate=mechanics.tax_mechanics.consumption_tax_rate,
        carbon_tax_per_ton=mechanics.tax_mechanics.carbon_tax_per_ton,
        # ... other parameters
    )
    results = tax_model.simulate()
```

### Social Security Module (core/social_security.py)

To use extracted SS mechanics:

```python
if mechanics.social_security_mechanics:
    ss_model = SocialSecurityModel(
        benefit_formula=BenefitFormula(
            full_retirement_age=mechanics.social_security_mechanics.full_retirement_age or 67,
            early_claiming_reduction_pct=mechanics.social_security_mechanics.early_claiming_reduction or 0.70,
            # ... other parameters
        )
    )
    results = ss_model.project()
```

### Spending Reform Module (core/discretionary_spending.py)

To use extracted spending mechanics:

```python
if mechanics.spending_mechanics:
    spending_model = DiscretionarySpendingModel(
        assumptions=DiscretionaryAssumptions(
            # Adjust based on extracted mechanics
        )
    )
    results = spending_model.project()
```

## Usage Examples

### Example 1: Healthcare-Only Policy

Input text contains healthcare reform details:
```
United States Galactic Health Act
- Universal coverage
- 15% payroll tax
- Zero out-of-pocket costs
```

Result:
```python
mechanics = extract_policy_mechanics(text, policy_type="combined")
# mechanics.policy_type = "healthcare"
# mechanics.funding_mechanisms populated
# mechanics.tax_mechanics = None
# mechanics.social_security_mechanics = None
# mechanics.spending_mechanics = None
```

### Example 2: Combined Policy

Input text addresses multiple domains:
```
Comprehensive Reform Act
- Healthcare: Universal coverage via 12% payroll tax
- Tax: Wealth tax 2% on $50M+, carbon tax $50/ton
- Social Security: Payroll tax increase to 13%, raise FRA to 68
- Spending: $300B infrastructure investment
```

Result:
```python
mechanics = extract_policy_mechanics(text, policy_type="combined")
# mechanics.policy_type = "combined"
# mechanics.funding_mechanisms populated (healthcare)
# mechanics.tax_mechanics populated (wealth/carbon taxes)
# mechanics.social_security_mechanics populated (payroll/FRA)
# mechanics.spending_mechanics populated (infrastructure)
```

All modules can simultaneously access and apply the relevant parameters to their models.

### Example 3: Tax-Only Policy

Input text is purely tax-focused:
```
Progressive Taxation Act 2026
- Wealth tax: 3% on net worth above $100 million
- Carbon tax: $75 per ton with annual 5% increases
- Financial transaction tax: 0.1%
- Expected revenue: $200 billion annually
```

Result:
```python
mechanics = extract_policy_mechanics(text, policy_type="combined")
# mechanics.policy_type = "tax_reform"
# mechanics.funding_mechanisms = []  # Not applicable
# mechanics.tax_mechanics populated (all tax types)
# mechanics.social_security_mechanics = None
# mechanics.spending_mechanics = None
```

## Serialization

PolicyMechanics can be saved and restored as JSON for later use:

```python
# Save extracted mechanics
import json
mechanics_dict = asdict(mechanics)
with open('policy_mechanics.json', 'w') as f:
    json.dump(mechanics_dict, f)

# Restore mechanics
with open('policy_mechanics.json', 'r') as f:
    loaded_dict = json.load(f)
    restored_mechanics = PolicyMechanicsExtractor.mechanics_from_dict(loaded_dict)
```

## Confidence Scoring

Each extracted PolicyMechanics object includes a `confidence_score` (0.0-1.0) indicating how complete and reliable the extraction is:

- **0.85-1.0**: Comprehensive extraction across multiple domains
- **0.65-0.85**: Solid extraction with most key parameters found
- **0.40-0.65**: Partial extraction, some parameters missing
- **Below 0.40**: Sparse extraction, manual review recommended

Factors that increase confidence:
- Multiple funding mechanisms identified
- Complete policy timeline
- Surplus allocation rules
- Circuit breakers defined
- Cross-domain parameters found

## Future Enhancements

1. **LLM-Assisted Detection**: Use language models to improve content detection and parameter extraction accuracy
2. **Cross-Domain Analysis**: Identify policy interactions (e.g., tax increases funding spending, which affects healthcare)
3. **Scenario Generation**: Automatically create scenarios based on detected policy parameters
4. **Sensitivity Analysis**: Determine which extracted parameters most significantly impact outcomes
5. **Policy Comparison**: Compare multiple extracted policies across all domains

## Implementation Notes

- All extraction methods use regex patterns optimized for legislative language
- When multiple detection keywords appear, higher weight is given to precise matches
- Extraction gracefully handles partial matches and missing parameters
- Each module only needs to check if its mechanics object is non-None before using
- The unified architecture allows policies to be re-analyzed for different domains without re-parsing the source text
