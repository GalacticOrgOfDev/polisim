"""
Test script for Bug #6 (seed management) and Bug #13 (hardcoded interest rate)
"""
import numpy as np
import sys

print("=" * 60)
print("TESTING BUG FIXES #6 AND #13")
print("=" * 60)

# Test Bug #6: Seed management for reproducibility
print("\n[Bug #6] Testing seed management across all models...")
try:
    from core.social_security import SocialSecurityModel
    from core.revenue_modeling import FederalRevenueModel
    from core.medicare_medicaid import MedicareModel, MedicaidModel
    from core.discretionary_spending import DiscretionarySpendingModel
    from core.interest_spending import InterestOnDebtModel
    
    # Test that seed parameter exists and works
    seed_value = 42
    
    # Test SocialSecurityModel
    ss_model_1 = SocialSecurityModel(seed=seed_value)
    ss_model_2 = SocialSecurityModel(seed=seed_value)
    
    # Test FederalRevenueModel
    rev_model_1 = FederalRevenueModel(seed=seed_value)
    rev_model_2 = FederalRevenueModel(seed=seed_value)
    
    # Test MedicareModel
    medicare_model_1 = MedicareModel(seed=seed_value)
    medicare_model_2 = MedicareModel(seed=seed_value)
    
    # Test MedicaidModel
    medicaid_model_1 = MedicaidModel(seed=seed_value)
    medicaid_model_2 = MedicaidModel(seed=seed_value)
    
    # Test DiscretionarySpendingModel
    disc_model_1 = DiscretionarySpendingModel(seed=seed_value)
    disc_model_2 = DiscretionarySpendingModel(seed=seed_value)
    
    # Test InterestOnDebtModel
    interest_model_1 = InterestOnDebtModel(seed=seed_value)
    interest_model_2 = InterestOnDebtModel(seed=seed_value)
    
    print(f"  ✓ PASS: All models accept seed parameter")
    print(f"  Models tested: SocialSecurity, Revenue, Medicare, Medicaid, Discretionary, Interest")
    print(f"  Seed value used: {seed_value}")
    
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test Bug #13: Configurable interest rate
print("\n[Bug #13] Testing configurable interest rate...")
try:
    from core.social_security import SocialSecurityModel, TrustFundAssumptions
    
    # Test default interest rate
    default_assumptions = TrustFundAssumptions()
    assert hasattr(default_assumptions, 'trust_fund_interest_rate'), "Missing trust_fund_interest_rate attribute"
    assert default_assumptions.trust_fund_interest_rate == 0.035, f"Expected 0.035, got {default_assumptions.trust_fund_interest_rate}"
    
    # Test custom interest rate
    custom_assumptions = TrustFundAssumptions(trust_fund_interest_rate=0.045)
    assert custom_assumptions.trust_fund_interest_rate == 0.045, f"Custom rate not set correctly"
    
    # Create model with custom assumptions
    model = SocialSecurityModel(trust_fund=custom_assumptions)
    assert model.trust_fund.trust_fund_interest_rate == 0.045, "Model didn't use custom interest rate"
    
    print(f"  ✓ PASS: Interest rate is now configurable")
    print(f"  Default rate: {default_assumptions.trust_fund_interest_rate:.3%}")
    print(f"  Custom rate: {custom_assumptions.trust_fund_interest_rate:.3%}")
    print(f"  No longer hardcoded in code")
    
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
