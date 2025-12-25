"""
Test script for Bug #5 (bare exceptions) and Bug #11 (input validation)
"""
import sys

print("=" * 60)
print("TESTING BUG FIXES #5 AND #11")
print("=" * 60)

# Test Bug #5: Bare exception handlers replaced with logging
print("\n[Bug #5] Testing that exception handlers now log properly...")
try:
    # Test imports to ensure logging is set up
    from core.simulation import simulate_healthcare_years
    from core.scenario_loader import load_scenario
    from core.metrics import compute_policy_metrics
    
    # Verify logger exists
    import core.simulation as sim_module
    import core.scenario_loader as loader_module
    import core.metrics as metrics_module
    
    has_logger_sim = hasattr(sim_module, 'logger')
    has_logger_loader = hasattr(loader_module, 'logger')
    has_logger_metrics = hasattr(metrics_module, 'logger')
    
    if has_logger_sim and has_logger_loader and has_logger_metrics:
        print(f"  ✓ PASS: All modules have logging configured")
        print(f"    - simulation.py: logger present")
        print(f"    - scenario_loader.py: logger present")
        print(f"    - metrics.py: logger present")
    else:
        print(f"  ✗ FAIL: Missing loggers")
        print(f"    - simulation.py: {has_logger_sim}")
        print(f"    - scenario_loader.py: {has_logger_loader}")
        print(f"    - metrics.py: {has_logger_metrics}")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test Bug #11: Input validation
print("\n[Bug #11] Testing input validation in model constructors...")
try:
    from core.social_security import SocialSecurityModel, TrustFundAssumptions
    from core.revenue_modeling import FederalRevenueModel, IndividualIncomeTaxAssumptions
    
    validation_tests_passed = 0
    validation_tests_total = 4
    
    # Test 1: Negative OASI balance should raise ValueError
    try:
        bad_trust_fund = TrustFundAssumptions(oasi_beginning_balance=-1000)
        model = SocialSecurityModel(trust_fund=bad_trust_fund)
        print(f"  ✗ Test 1 FAIL: Negative OASI balance accepted (should raise ValueError)")
    except ValueError as e:
        validation_tests_passed += 1
        print(f"  ✓ Test 1 PASS: Negative OASI balance rejected")
    
    # Test 2: Interest rate > 100% should raise ValueError
    try:
        bad_trust_fund = TrustFundAssumptions(trust_fund_interest_rate=1.5)
        model = SocialSecurityModel(trust_fund=bad_trust_fund)
        print(f"  ✗ Test 2 FAIL: Interest rate >100% accepted (should raise ValueError)")
    except ValueError as e:
        validation_tests_passed += 1
        print(f"  ✓ Test 2 PASS: Interest rate >100% rejected")
    
    # Test 3: Fertility rate > 10 should raise ValueError  
    try:
        from core.social_security import DemographicAssumptions
        bad_demographics = DemographicAssumptions(total_fertility_rate=15.0)
        model = SocialSecurityModel(demographics=bad_demographics)
        print(f"  ✗ Test 3 FAIL: Fertility rate >10 accepted (should raise ValueError)")
    except ValueError as e:
        validation_tests_passed += 1
        print(f"  ✓ Test 3 PASS: Fertility rate >10 rejected")
    
    # Test 4: Wage growth > 50% should raise ValueError
    try:
        from core.revenue_modeling import PayrollTaxAssumptions
        bad_payroll = PayrollTaxAssumptions(wage_growth_rate=0.75)
        model = FederalRevenueModel(payroll_taxes=bad_payroll)
        print(f"  ✗ Test 4 FAIL: Wage growth >50% accepted (should raise ValueError)")
    except ValueError as e:
        validation_tests_passed += 1
        print(f"  ✓ Test 4 PASS: Wage growth >50% rejected")
    
    if validation_tests_passed == validation_tests_total:
        print(f"\n  ✓ PASS: All {validation_tests_total} validation tests passed")
    else:
        print(f"\n  ✗ FAIL: Only {validation_tests_passed}/{validation_tests_total} validation tests passed")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
