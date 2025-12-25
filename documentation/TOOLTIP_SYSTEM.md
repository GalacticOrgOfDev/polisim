# Tooltip System Documentation

## Overview

The PoliSim dashboard includes an educational tooltip system that provides helpful explanations for technical terms and concepts. Users can toggle tooltips on/off via the Settings page.

## Features

### 1. Settings Page (⚙️ Settings)
- **Enable/Disable Tooltips**: Toggle educational tooltips throughout the application
- **Decimal Places**: Control numeric precision in displays
- **Advanced Options**: Show/hide advanced configuration options
- **Chart Theme**: Choose visualization themes (white, dark, seaborn, simple)
- **Glossary of Terms**: Comprehensive reference for Social Security, Economic, and Healthcare terminology

### 2. Tooltip Helper Function

```python
get_tooltip(term, definition)
```

Returns tooltip help text if tooltips are enabled, otherwise returns None.

**Usage in Streamlit widgets:**
```python
st.slider(
    "Projection years:",
    10, 50, 30,
    help=get_tooltip("Projection Years", "Number of years to project into the future")
)
```

### 3. Tooltips on Social Security Page

The Social Security page includes tooltips for:

#### Quick Scenarios Tab
- **Reform Scenario**: Explains policy comparison functionality
- **Projection Years**: Social Security's 75-year projection window
- **Monte Carlo Iterations**: Simulation uncertainty and accuracy trade-offs

#### Custom Parameters Tab
- **Payroll Tax Rate**: Current rate explanation (12.4%, split 6.2% each)
- **Payroll Tax Cap**: 2025 earnings cap ($168,600)
- **Remove Wage Cap**: Revenue increase (~20%) from eliminating cap
- **Interest Rate**: Trust fund investment returns
- **Full Retirement Age (FRA)**: Current FRA and cost impact (~6.7% per year)
- **COLA**: Cost of Living Adjustment based on CPI-W
- **Benefit Reduction**: Across-the-board benefit cuts

## Glossary

### Social Security Terms
- **COLA (Cost of Living Adjustment)**: Annual inflation-based benefit increase
- **FRA (Full Retirement Age)**: Age for unreduced retirement benefits (67 for 1960+)
- **OASI**: Old-Age and Survivors Insurance trust fund
- **DI**: Disability Insurance trust fund
- **Payroll Tax Rate**: Combined 12.4% Social Security tax
- **Wage Cap**: Maximum taxable earnings ($168,600 in 2025)
- **Trust Fund Depletion**: Year reserves exhausted (~77% benefits payable)
- **Monte Carlo Simulation**: Thousands of scenarios to quantify uncertainty

### Economic Terms
- **GDP**: Gross Domestic Product - total economic output
- **CPI**: Consumer Price Index - inflation measure
- **Baseline Scenario**: Current law projections without changes
- **Fiscal Outlook**: Long-term revenue, spending, deficit, debt projections
- **Actuarial Balance**: Long-term financial status as % of taxable payroll

### Healthcare Terms
- **Medicare Part A**: Hospital insurance (inpatient care)
- **Medicare Part B**: Medical insurance (doctors, outpatient)
- **Medicare Part D**: Prescription drug coverage
- **Medicaid**: Federal-state program for low-income health coverage
- **USGHA**: United States Guaranteed Healthcare Act (proposed reform)

## Implementation Notes

### Session State
Settings are stored in `st.session_state.settings`:
```python
{
    'tooltips_enabled': True,
    'show_advanced_options': False,
    'decimal_places': 1,
    'chart_theme': 'plotly_white'
}
```

### Adding New Tooltips

1. Use the `get_tooltip()` helper function
2. Add to the `help` parameter of Streamlit widgets
3. Update the glossary in Settings page if adding new terms

**Example:**
```python
custom_parameter = st.number_input(
    "Parameter Name",
    min_value=0, max_value=100, value=50,
    help=get_tooltip(
        "Parameter Name",
        "Clear explanation of what this parameter does and its typical range"
    )
)
```

## Future Enhancements

- [ ] Tooltips for Federal Revenues page
- [ ] Tooltips for Medicare/Medicaid page
- [ ] Tooltips for Combined Outlook page
- [ ] Interactive tooltip editor for administrators
- [ ] Multi-language tooltip support
- [ ] Contextual help based on user interaction patterns
- [ ] Video tutorials linked from tooltips
- [ ] Tooltip analytics to identify confusing areas

## User Testing

Users should test:
1. Toggle tooltips on/off in Settings
2. Verify tooltips appear when enabled
3. Verify tooltips disappear when disabled
4. Check glossary completeness
5. Suggest new terms that need explanation

## Educational Goals

The tooltip system aims to:
- Make fiscal policy analysis accessible to non-experts
- Educate users about Social Security mechanics
- Explain technical terminology in plain language
- Reduce barriers to understanding complex projections
- Empower informed policy discussions
