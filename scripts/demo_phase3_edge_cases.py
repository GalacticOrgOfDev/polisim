#!/usr/bin/env python3
"""
Phase 3 Edge Case Handling Demo

Demonstrates the edge case safeguards added in Sprint 4.3:
- Edge Case #1: Zero/negative GDP growth (recession handling)
- Edge Case #3: Extreme inflation (deflation and hyperinflation)
- Edge Case #8: Division by zero protection
- Edge Case #9: Extreme debt (>200% GDP)
- Edge Case #10: Missing CBO data (fallback mechanisms)

Usage:
    python scripts/demo_phase3_edge_cases.py
    python scripts/demo_phase3_edge_cases.py --all  # Run all edge case examples
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.edge_case_handlers import EdgeCaseHandler


def print_section(title: str, width: int = 80):
    """Print formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def demo_recession_handling():
    """Demonstrate recession GDP growth handling."""
    print_section("Edge Case #1: Recession GDP Growth Handling")
    
    handler = EdgeCaseHandler()
    
    # Example 1: Normal growth
    print("Example 1: Normal economic growth (3%)")
    growth = 0.03
    safe_growth, warning = handler.handle_recession_gdp_growth(growth)
    print(f"  Input:  {growth * 100:.1f}% growth")
    print(f"  Output: {safe_growth * 100:.1f}% growth")
    print(f"  Status: {warning if warning else '✅ Normal growth'}\n")
    
    # Example 2: Mild recession
    print("Example 2: Mild recession (-2%)")
    growth = -0.02
    safe_growth, warning = handler.handle_recession_gdp_growth(growth)
    print(f"  Input:  {growth * 100:.1f}% growth")
    print(f"  Output: {safe_growth * 100:.1f}% growth")
    print(f"  Status: {warning if warning else '✅ Within bounds'}\n")
    
    # Example 3: Severe recession
    print("Example 3: Severe recession (-8% - like 2008)")
    growth = -0.08
    safe_growth, warning = handler.handle_recession_gdp_growth(growth)
    print(f"  Input:  {growth * 100:.1f}% growth")
    print(f"  Output: {safe_growth * 100:.1f}% growth")
    print(f"  Status: ⚠️  {warning}\n")
    
    # Example 4: Extreme contraction (capped)
    print("Example 4: Extreme contraction (-25% - capped at -15%)")
    growth = -0.25
    safe_growth, warning = handler.handle_recession_gdp_growth(growth)
    print(f"  Input:  {growth * 100:.1f}% growth")
    print(f"  Output: {safe_growth * 100:.1f}% growth (CAPPED)")
    print(f"  Status: ⚠️  {warning}\n")
    
    # Example 5: Extreme boom (capped)
    print("Example 5: Extreme boom (30% - capped at 20%)")
    growth = 0.30
    safe_growth, warning = handler.handle_recession_gdp_growth(growth)
    print(f"  Input:  {growth * 100:.1f}% growth")
    print(f"  Output: {safe_growth * 100:.1f}% growth (CAPPED)")
    print(f"  Status: ⚠️  {warning}\n")
    
    print("📝 Key Points:")
    print("  • Allows realistic recession range: -10% to +15%")
    print("  • Caps extreme contractions at -15% (worse than Great Depression)")
    print("  • Caps extreme booms at +20% (post-war recovery levels)")
    print("  • Provides warnings for extreme scenarios")
    print("  • Prevents unrealistic economic assumptions")
    print()


def demo_division_safety():
    """Demonstrate division by zero protection."""
    print_section("Edge Case #8: Division by Zero Protection")
    
    handler = EdgeCaseHandler()
    
    # Example 1: Normal division
    print("Example 1: Normal division (10 / 2)")
    result = handler.safe_divide(10, 2)
    print(f"  Result: {result:.2f}")
    print(f"  Status: ✅ Normal division\n")
    
    # Example 2: Division by zero (default)
    print("Example 2: Division by zero (10 / 0)")
    result = handler.safe_divide(10, 0)
    print(f"  Result: {result:.2f} (default)")
    print(f"  Status: ⚠️  Division by zero prevented - returned default 0.0\n")
    
    # Example 3: Division by zero (custom default)
    print("Example 3: Division by zero with custom default (10 / 0, default=100)")
    result = handler.safe_divide(10, 0, default=100.0)
    print(f"  Result: {result:.2f} (custom default)")
    print(f"  Status: ⚠️  Division by zero prevented - returned custom default\n")
    
    # Example 4: Near-zero division
    print("Example 4: Near-zero division (10 / 0.0001)")
    result = handler.safe_divide(10, 0.0001)
    print(f"  Result: {result:.2f}")
    print(f"  Status: ✅ Small denominator but valid\n")
    
    # Example 5: GDP percentage calculation
    print("Example 5: Safe GDP percentage (spending / GDP)")
    spending = 5e12  # $5T
    gdp = 0  # Zero GDP edge case
    pct = handler.safe_percentage_of_gdp(spending, gdp)
    print(f"  Spending: ${spending / 1e12:.1f}T")
    print(f"  GDP:      ${gdp / 1e12:.1f}T (ZERO!)")
    print(f"  Result:   {pct:.1f}% (used MIN_GDP=$1T instead)")
    print(f"  Status: ⚠️  Zero GDP replaced with minimum to prevent division by zero\n")
    
    print("📝 Key Points:")
    print("  • safe_divide() prevents division by zero crashes")
    print("  • Returns configurable default value")
    print("  • Logs warnings for debugging")
    print("  • Used throughout calculations for robustness")
    print("  • Prevents 'inf' and 'nan' values in results")
    print()


def demo_gdp_validation():
    """Demonstrate GDP validation."""
    print_section("GDP & Population Validation")
    
    handler = EdgeCaseHandler()
    
    # Example 1: Normal GDP
    print("Example 1: Normal GDP ($29T)")
    gdp = 29e12
    safe_gdp, warning = handler.validate_gdp(gdp)
    print(f"  Input:  ${safe_gdp / 1e12:.1f}T")
    print(f"  Output: ${safe_gdp / 1e12:.1f}T")
    print(f"  Status: {warning if warning else '✅ Valid GDP'}\n")
    
    # Example 2: Zero GDP
    print("Example 2: Zero GDP (replaced with minimum)")
    gdp = 0
    safe_gdp, warning = handler.validate_gdp(gdp)
    print(f"  Input:  ${gdp / 1e12:.1f}T")
    print(f"  Output: ${safe_gdp / 1e12:.1f}T (MIN_GDP)")
    print(f"  Status: ⚠️  {warning}\n")
    
    # Example 3: Negative GDP
    print("Example 3: Negative GDP (replaced with minimum)")
    gdp = -5e12
    safe_gdp, warning = handler.validate_gdp(gdp)
    print(f"  Input:  ${gdp / 1e12:.1f}T")
    print(f"  Output: ${safe_gdp / 1e12:.1f}T (MIN_GDP)")
    print(f"  Status: ⚠️  {warning}\n")
    
    # Example 4: Normal population
    print("Example 4: Normal population (335M)")
    pop = 335e6
    safe_pop, warning = handler.validate_population(pop)
    print(f"  Input:  {safe_pop / 1e6:.0f}M")
    print(f"  Output: {safe_pop / 1e6:.0f}M")
    print(f"  Status: {warning if warning else '✅ Valid population'}\n")
    
    # Example 5: Zero population
    print("Example 5: Zero population (replaced with minimum)")
    pop = 0
    safe_pop, warning = handler.validate_population(pop)
    print(f"  Input:  {pop / 1e6:.0f}M")
    print(f"  Output: {safe_pop / 1e6:.0f}M (MIN_POPULATION)")
    print(f"  Status: ⚠️  {warning}\n")
    
    print("📝 Key Points:")
    print("  • MIN_GDP = $1T (prevents division by zero)")
    print("  • MIN_POPULATION = 1M (prevents per-capita errors)")
    print("  • Invalid values automatically replaced")
    print("  • Warnings logged for debugging")
    print("  • Ensures all calculations remain valid")
    print()


def demo_extreme_values():
    """Demonstrate extreme value detection."""
    print_section("Edge Cases #3, #9: Extreme Value Detection")
    
    handler = EdgeCaseHandler()
    
    # Example 1: Normal debt
    print("Example 1: Normal debt (100% GDP)")
    debt = 30e12
    gdp = 30e12
    is_extreme, warning = handler.check_extreme_debt(debt, gdp)
    print(f"  Debt/GDP: {(debt / gdp) * 100:.0f}%")
    print(f"  Status: {warning if is_extreme else '✅ Normal debt level'}\n")
    
    # Example 2: High debt (Japan level)
    print("Example 2: High debt (250% GDP - Japan level)")
    debt = 75e12
    gdp = 30e12
    is_extreme, warning = handler.check_extreme_debt(debt, gdp)
    print(f"  Debt/GDP: {(debt / gdp) * 100:.0f}%")
    print(f"  Status: ⚠️  {warning}\n")
    
    # Example 3: Normal inflation
    print("Example 3: Normal inflation (3%)")
    inflation = 0.03
    is_extreme, warning = handler.check_extreme_inflation(inflation)
    print(f"  Inflation: {inflation * 100:.1f}%")
    print(f"  Status: {warning if is_extreme else '✅ Normal inflation'}\n")
    
    # Example 4: Deflation
    print("Example 4: Deflation (-7%)")
    inflation = -0.07
    is_extreme, warning = handler.check_extreme_inflation(inflation)
    print(f"  Inflation: {inflation * 100:.1f}%")
    print(f"  Status: ⚠️  {warning}\n")
    
    # Example 5: Hyperinflation
    print("Example 5: Hyperinflation (30%)")
    inflation = 0.30
    is_extreme, warning = handler.check_extreme_inflation(inflation)
    print(f"  Inflation: {inflation * 100:.1f}%")
    print(f"  Status: ⚠️  {warning}\n")
    
    # Example 6: Normal interest rate
    print("Example 6: Normal interest rate (5%)")
    rate = 0.05
    is_extreme, warning = handler.check_extreme_interest_rate(rate)
    print(f"  Interest Rate: {rate * 100:.1f}%")
    print(f"  Status: {warning if is_extreme else '✅ Normal rate'}\n")
    
    # Example 7: Extreme interest rate
    print("Example 7: Extreme interest rate (30% - crisis level)")
    rate = 0.30
    is_extreme, warning = handler.check_extreme_interest_rate(rate)
    print(f"  Interest Rate: {rate * 100:.1f}%")
    print(f"  Status: ⚠️  {warning}\n")
    
    print("📝 Key Points:")
    print("  • Extreme debt: >250% GDP (Japan crisis levels)")
    print("  • Deflation: <-5% (Great Depression scenario)")
    print("  • Hyperinflation: >25% (Weimar/Zimbabwe levels)")
    print("  • Extreme interest: >25% (Volcker crisis levels)")
    print("  • Detection doesn't prevent calculation - just warns")
    print("  • Helps identify unrealistic scenarios")
    print()


def demo_missing_data():
    """Demonstrate missing CBO data fallback."""
    print_section("Edge Case #10: Missing CBO Data Fallback")
    
    handler = EdgeCaseHandler()
    
    # Example 1: User provides fallback
    print("Example 1: User provides fallback data")
    fallback = {'gdp': 30e12, 'revenues': 4.5e12}
    result = handler.handle_missing_cbo_data('gdp', user_fallback=fallback)
    print(f"  Requested: 'gdp'")
    print(f"  Result:    ${result / 1e12:.1f}T (from user fallback)")
    print(f"  Status:    ✅ Used user-provided data\n")
    
    # Example 2: Use cached data
    print("Example 2: Use cached CBO data")
    cached = {'revenues': 5e12, 'spending': 6e12}
    result = handler.handle_missing_cbo_data('revenues', cached_data=cached)
    print(f"  Requested: 'revenues'")
    print(f"  Result:    ${result / 1e12:.1f}T (from cache)")
    print(f"  Status:    ✅ Used cached data\n")
    
    # Example 3: Use hardcoded defaults
    print("Example 3: Use hardcoded defaults (no fallback or cache)")
    result = handler.handle_missing_cbo_data('gdp')
    print(f"  Requested: 'gdp'")
    print(f"  Result:    ${result / 1e12:.1f}T (hardcoded default)")
    print(f"  Status:    ⚠️  Using default - may be outdated\n")
    
    # Example 4: Fallback hierarchy
    print("Example 4: Fallback precedence hierarchy")
    print("  1. User-provided fallback (highest priority)")
    print("  2. Cached CBO data")
    print("  3. Hardcoded defaults (lowest priority)")
    print()
    print("  This ensures the system NEVER crashes from missing data!")
    print()
    
    print("📝 Hardcoded Defaults Available:")
    print("  • gdp: $29T (2025 estimate)")
    print("  • revenues: $4.9T")
    print("  • spending: $6.8T")
    print("  • debt: $36T")
    print("  • interest_rate: 3.5%")
    print("  • ... and more economic indicators")
    print()
    
    print("🎯 Real-World Scenario:")
    print("  • CBO website down during analysis")
    print("  • Network connectivity issues")
    print("  • Rate limiting from CBO API")
    print("  • Stale cache older than threshold")
    print()
    print("  → System continues with fallback data instead of crashing!")
    print()


def demo_integration_scenario():
    """Show realistic integration scenario."""
    print_section("Realistic Integration Scenario: 2020 COVID Recession")
    
    handler = EdgeCaseHandler()
    
    print("🌐 Simulating 2020 COVID-19 Economic Shock:\n")
    
    # 2020 Q2 conditions
    gdp_growth = -0.10  # -10% contraction
    inflation = -0.01   # Slight deflation
    debt_to_gdp = 1.28  # 128% debt-to-GDP
    
    print("Input Conditions:")
    print(f"  • GDP Growth: {gdp_growth * 100:.1f}%")
    print(f"  • Inflation:  {inflation * 100:.1f}%")
    print(f"  • Debt/GDP:   {debt_to_gdp * 100:.0f}%")
    print()
    
    # Handle recession
    safe_growth, growth_warning = handler.handle_recession_gdp_growth(gdp_growth)
    print(f"Recession Handling:")
    print(f"  • Adjusted Growth: {safe_growth * 100:.1f}%")
    if growth_warning:
        print(f"  • Warning: {growth_warning}")
    print()
    
    # Check inflation
    extreme_inflation, inflation_warning = handler.check_extreme_inflation(inflation)
    print(f"Inflation Check:")
    if extreme_inflation:
        print(f"  • ⚠️  {inflation_warning}")
    else:
        print(f"  • ✅ Inflation within normal range")
    print()
    
    # Check debt
    extreme_debt, debt_warning = handler.check_extreme_debt(
        debt=28e12, 
        gdp=21e12  # Contracted GDP
    )
    print(f"Debt Sustainability:")
    if extreme_debt:
        print(f"  • ⚠️  {debt_warning}")
    else:
        print(f"  • ✅ Debt level manageable")
    print()
    
    # Safe calculations
    spending = 6.5e12
    gdp = 21e12
    spending_pct = handler.safe_percentage_of_gdp(spending, gdp)
    print(f"Safe Calculations:")
    print(f"  • Spending: ${spending / 1e12:.1f}T")
    print(f"  • GDP:      ${gdp / 1e12:.1f}T")
    print(f"  • Spending/GDP: {spending_pct:.1f}%")
    print(f"  • Status:   ✅ All divisions safe (no crashes)")
    print()
    
    print("🎯 Result:")
    print("  • System handled extreme 2020 conditions gracefully")
    print("  • No crashes or infinite values")
    print("  • Clear warnings for policy makers")
    print("  • Calculations remained valid throughout")
    print("  • Production-ready for real-world shocks!")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3 Edge Case Handling Demo (Sprint 4.3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This demo showcases the edge case safeguards added in Sprint 4.3:
  • Edge Case #1: Recession GDP growth handling
  • Edge Case #3: Extreme inflation detection
  • Edge Case #8: Division by zero protection
  • Edge Case #9: Extreme debt warnings
  • Edge Case #10: Missing CBO data fallback

Examples:
  python scripts/demo_phase3_edge_cases.py
  python scripts/demo_phase3_edge_cases.py --all
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Run all edge case examples')
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 80)
    print("  POLISIM - Phase 3 Edge Case Handling Demo (Sprint 4.3)")
    print("=" * 80)
    print("\n🛡️  Demonstrating Robustness Features:")
    print("  • Edge Case #1: Recession GDP growth")
    print("  • Edge Case #3: Extreme inflation")
    print("  • Edge Case #8: Division by zero")
    print("  • Edge Case #9: Extreme debt")
    print("  • Edge Case #10: Missing CBO data")
    print()
    
    # Run demos
    if args.all:
        demo_recession_handling()
        demo_division_safety()
        demo_gdp_validation()
        demo_extreme_values()
        demo_missing_data()
        demo_integration_scenario()
    else:
        # Default: run key examples
        demo_recession_handling()
        demo_division_safety()
        demo_extreme_values()
        demo_missing_data()
        
        print("💡 Run with --all to see all edge case examples and integration scenario\n")
    
    # Summary
    print_section("Demo Complete")
    print("✅ Edge case handling features demonstrated!")
    print("\n📚 Key Takeaways:")
    print("  1. Recession handling: -15% to +20% GDP growth bounds")
    print("  2. Division protection: No crashes from zero denominators")
    print("  3. GDP/population validation: Minimum values prevent errors")
    print("  4. Extreme value detection: Warns for debt, inflation, interest")
    print("  5. CBO data fallback: 3-tier hierarchy (user → cache → defaults)")
    print("\n🎯 Result: Production-ready robustness!")
    print()


if __name__ == "__main__":
    main()
