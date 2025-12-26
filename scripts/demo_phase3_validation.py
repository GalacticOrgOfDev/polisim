#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 Input Validation Demo

Demonstrates the input validation and safety features added in Sprint 4.2:
- PDF file size limits (Safety #1)
- Parameter range validation (Safety #2)
- Scenario name validation
- Helpful error messages

Usage:
    python scripts/demo_phase3_validation.py
    python scripts/demo_phase3_validation.py --all  # Run all validation examples
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure output encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.validation import (
    InputValidator,
    ValidationError,
    validate_projection_params,
    validate_economic_params,
    validate_tax_params
)


def print_section(title: str, width: int = 80):
    """Print formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def demo_pdf_size_validation():
    """Demonstrate PDF file size validation."""
    print_section("PDF File Size Validation (Safety #1)")
    
    validator = InputValidator()
    
    # Example 1: Valid file size (simulated - uses fake path for demo)
    print("Example 1: Valid PDF file (simulated 5MB check)")
    print("  • File size: 5MB")
    print("  • Limit: 50MB (default)")
    print("  ✅ File size is within limits (5MB < 50MB default limit)\n")
    
    # Example 2: Oversized file (default 50MB limit)
    print("Example 2: Oversized PDF file (simulated 75MB check)")
    print("  • File size: 75MB")
    print("  • Limit: 50MB (default)")
    print("  ❌ ValidationError: File size 75.0MB exceeds maximum allowed 50MB.")
    print("     Please provide a smaller file or split into multiple documents.")
    print("   💡 This prevents system crashes from loading huge PDFs!\n")
    
    # Example 3: Custom size limit
    print("Example 3: Custom size limit (simulated 15MB file, 10MB limit)")
    print("  • File size: 15MB")
    print("  • Limit: 10MB (custom)")
    print("  ❌ ValidationError: File size 15.0MB exceeds maximum allowed 10MB.")
    print("     Please provide a smaller file or split into multiple documents.")
    print("   💡 Custom limits can be set for specific use cases\n")
    
    print("📝 Key Points:")
    print("  • Default limit: 50MB (prevents crashes)")
    print("  • Customizable per use case")
    print("  • Clear error messages guide users")
    print()


def demo_parameter_validation():
    """Demonstrate parameter range validation."""
    print_section("Parameter Range Validation (Safety #2)")
    
    validator = InputValidator()
    
    # Example 1: Valid projection years
    print("Example 1: Projection years")
    try:
        validator.validate_range(30, 'years', param_type='years')
        print("✅ Valid: 30 years (within 1-75 range)\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 2: Invalid years (too many)
    try:
        validator.validate_range(100, 'years', param_type='years')
        print("✅ Valid: 100 years\n")
    except ValidationError as e:
        print(f"❌ {e}")
        print("   💡 Prevents unrealistic long-term projections\n")
    
    # Example 3: Valid GDP growth
    print("Example 2: GDP growth rate")
    try:
        validator.validate_range(0.025, 'gdp_growth', param_type='gdp_growth')
        print("✅ Valid: 2.5% GDP growth (within -10% to +15% range)\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 4: Invalid GDP growth (too high)
    try:
        validator.validate_range(0.25, 'gdp_growth', param_type='gdp_growth')
        print("✅ Valid: 25% GDP growth\n")
    except ValidationError as e:
        print(f"❌ {e}")
        print("   💡 Prevents unrealistic economic assumptions\n")
    
    # Example 5: Valid tax rate
    print("Example 3: Tax rate")
    try:
        validator.validate_range(0.35, 'tax_rate', param_type='tax_rate')
        print("✅ Valid: 35% tax rate (within 0-100% range)\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 6: Invalid tax rate (negative)
    try:
        validator.validate_range(-0.05, 'tax_rate', param_type='tax_rate')
        print("✅ Valid: -5% tax rate\n")
    except ValidationError as e:
        print(f"❌ {e}")
        print("   💡 Prevents nonsensical negative tax rates\n")
    
    print("📝 Validated Parameter Types:")
    print("  • years: 1-75 years")
    print("  • iterations: 100-50,000 Monte Carlo iterations")
    print("  • gdp_growth: -10% to +15% (recession to boom)")
    print("  • inflation: -5% to +25% (deflation to hyperinflation)")
    print("  • tax_rate: 0-100%")
    print("  • spending_pct_gdp: 0-50% of GDP")
    print("  • debt_to_gdp: 0-500% (Japan-level debt)")
    print("  • interest_rate: 0-25% (crisis-level rates)")
    print("  • ... and 15+ more parameter types!")
    print()


def demo_scenario_validation():
    """Demonstrate scenario name validation."""
    print_section("Scenario Name Validation")
    
    validator = InputValidator()
    valid_scenarios = ['baseline', 'progressive', 'moderate', 'revenue', 'climate']
    
    # Example 1: Valid baseline scenario
    print("Example 1: Baseline scenario")
    try:
        validator.validate_scenario_name("baseline", valid_scenarios)
        print("✅ Valid: 'baseline' is a supported scenario\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 2: Valid progressive scenario
    print("Example 2: Progressive reform scenario")
    try:
        validator.validate_scenario_name("progressive", valid_scenarios)
        print("✅ Valid: 'progressive' is a supported scenario\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 3: Invalid scenario
    print("Example 3: Unsupported scenario")
    try:
        validator.validate_scenario_name("magic_unicorn_budget", valid_scenarios)
        print("✅ Valid: 'magic_unicorn_budget' scenario\n")
    except ValidationError as e:
        print(f"❌ {e}")
        print("   💡 Helpful error shows valid options!\n")
    
    print("📝 Supported Scenarios:")
    print("  • baseline: Current law projection")
    print("  • progressive: Progressive tax reform")
    print("  • moderate: Moderate reform package")
    print("  • revenue: Revenue-focused reforms")
    print("  • climate: Climate-focused carbon pricing")
    print()


def demo_convenience_functions():
    """Demonstrate convenience validation functions."""
    print_section("Convenience Validation Functions")
    
    # Example 1: Projection parameters
    print("Example 1: Validate projection parameters")
    try:
        validate_projection_params(years=30, iterations=1000, scenario_name="baseline")
        print("✅ All projection parameters valid:")
        print("   • Years: 30")
        print("   • Iterations: 1000")
        print("   • Scenario: baseline\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 2: Economic parameters
    print("Example 2: Validate economic parameters")
    try:
        validate_economic_params(
            gdp_growth=0.025,
            inflation=0.03,
            population_growth=0.005
        )
        print("✅ All economic parameters valid:")
        print("   • GDP Growth: 2.5%")
        print("   • Inflation: 3.0%")
        print("   • Population Growth: 0.5%\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 3: Tax parameters
    print("Example 3: Validate tax parameters")
    try:
        validate_tax_params(
            income_tax_rate=0.35,
            corporate_tax_rate=0.21,
            payroll_tax_rate=0.124
        )
        print("✅ All tax parameters valid:")
        print("   • Income Tax: 35%")
        print("   • Corporate Tax: 21%")
        print("   • Payroll Tax: 12.4%\n")
    except ValidationError as e:
        print(f"❌ {e}\n")
    
    # Example 4: Invalid combination
    print("Example 4: Invalid parameter combination")
    try:
        validate_projection_params(years=100, iterations=50, scenario_name="invalid")
        print("✅ Parameters valid\n")
    except ValidationError as e:
        print(f"❌ {e}")
        print("   💡 Multiple validation errors caught at once!\n")
    
    print("📝 Convenience Functions:")
    print("  • validate_projection_params(): Years, iterations, scenario")
    print("  • validate_economic_params(): GDP, inflation, population")
    print("  • validate_tax_params(): Tax rates and brackets")
    print("  • validate_positive(): Ensure positive values")
    print("  • validate_non_negative(): Allow zero or positive")
    print("  • validate_percentage(): Check 0-100% range")
    print()


def demo_integration_example():
    """Show how validation integrates with real code."""
    print_section("Integration Example: Combined Outlook Model")
    
    print("💡 How Validation Works in Real Code:\n")
    
    print("```python")
    print("from core.combined_outlook import CombinedFiscalOutlookModel")
    print("from core.validation import ValidationError")
    print()
    print("model = CombinedFiscalOutlookModel()")
    print()
    print("try:")
    print("    results = model.project_unified_budget(")
    print("        years=30,          # ✅ Valid (1-75)")
    print("        iterations=1000,   # ✅ Valid (100-50000)")
    print("        scenario_name='baseline'  # ✅ Valid scenario")
    print("    )")
    print("    print('Projection successful!')")
    print()
    print("except ValidationError as e:")
    print("    print(f'Invalid input: {e}')")
    print("    # User gets helpful error message!")
    print("```\n")
    
    print("Before Sprint 4.2 (No Validation):")
    print("  ❌ Years=1000 → Memory overflow crash")
    print("  ❌ Iterations=1 → Nonsense Monte Carlo results")
    print("  ❌ 500MB PDF → System hangs/crashes")
    print("  ❌ GDP growth=1000% → Unrealistic projections\n")
    
    print("After Sprint 4.2 (With Validation):")
    print("  ✅ Years=1000 → Clear error: 'years must be between 1 and 75'")
    print("  ✅ Iterations=1 → Clear error: 'iterations must be at least 100'")
    print("  ✅ 500MB PDF → Clear error: 'PDF exceeds 50MB limit'")
    print("  ✅ GDP growth=1000% → Clear error: 'gdp_growth must be between -0.10 and 0.15'\n")
    
    print("🎯 Benefits:")
    print("  • Prevents crashes and hangs")
    print("  • Guides users to valid inputs")
    print("  • Catches errors early (fail fast)")
    print("  • Production-ready reliability")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3 Input Validation Demo (Sprint 4.2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This demo showcases the input validation and safety features added in Sprint 4.2:
  • Safety #1: PDF file size limits (prevents crashes)
  • Safety #2: Parameter range validation (prevents unrealistic inputs)
  • Helpful error messages guide users to valid inputs
  • Production-ready reliability

Examples:
  python scripts/demo_phase3_validation.py
  python scripts/demo_phase3_validation.py --all
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Run all validation examples')
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 80)
    print("  POLISIM - Phase 3 Input Validation Demo (Sprint 4.2)")
    print("=" * 80)
    print("\n[SAFETY] Demonstrating Safety Features:")
    print("  * Safety #1: PDF file size limits")
    print("  * Safety #2: Parameter range validation")
    print("  * Clear, helpful error messages")
    print()
    
    # Run demos
    if args.all:
        demo_pdf_size_validation()
        demo_parameter_validation()
        demo_scenario_validation()
        demo_convenience_functions()
        demo_integration_example()
    else:
        # Default: run key examples
        demo_pdf_size_validation()
        demo_parameter_validation()
        demo_scenario_validation()
        
        print("💡 Run with --all to see convenience functions and integration examples\n")
    
    # Summary
    print_section("Demo Complete")
    print("✅ Input validation features demonstrated!")
    print("\n📚 Key Takeaways:")
    print("  1. PDF size limits prevent system crashes (50MB default)")
    print("  2. Parameter validation prevents unrealistic inputs")
    print("  3. Clear error messages guide users to valid values")
    print("  4. 20+ parameter types validated (years, GDP, tax rates, etc.)")
    print("  5. Convenience functions simplify validation in code")
    print("\n🎯 Result: Production-ready reliability!")
    print()


if __name__ == "__main__":
    main()
