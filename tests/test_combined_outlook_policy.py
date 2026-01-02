"""
Test module for Combined Outlook with Policy Mechanics integration.
Tests the policy-driven projection capabilities.
"""

import pytest
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.combined_outlook import CombinedFiscalOutlookModel


class TestCombinedOutlookPolicyIntegration:
    """Test policy mechanics integration with combined outlook."""
    
    def test_model_initialization(self):
        """Test that model initializes with policy mechanics fields."""
        model = CombinedFiscalOutlookModel()
        
        assert model._policy_mechanics is None
        assert model._healthcare_gdp_target is None
        assert model._healthcare_target_year is None
        assert model._funding_mechanisms == []
        print("✓ Model initialization successful")
    
    def test_apply_policy_mechanics(self):
        """Test applying policy mechanics to the model."""
        model = CombinedFiscalOutlookModel()
        
        mechanics = {
            "target_spending_pct_gdp": 7,
            "target_spending_year": 2045,
            "funding_mechanisms": [
                {"source_type": "payroll_tax", "percentage_gdp": 7.95},
                {"source_type": "redirected_federal", "percentage_gdp": 6.2}
            ]
        }
        
        model.apply_policy_mechanics(mechanics)
        
        assert model._healthcare_gdp_target == 7
        assert model._healthcare_target_year == 2045
        assert len(model._funding_mechanisms) == 2
        print("✓ Policy mechanics applied successfully")
        print(f"  Healthcare target: {model._healthcare_gdp_target}% GDP")
        print(f"  Target year: {model._healthcare_target_year}")
    
    def test_policy_driven_healthcare_spending(self):
        """Test that policy-driven healthcare spending calculation works."""
        model = CombinedFiscalOutlookModel()
        
        # Apply USGHA-like mechanics
        mechanics = {
            "target_spending_pct_gdp": 7,
            "target_spending_year": 2045,
            "funding_mechanisms": [
                {"source_type": "payroll_tax", "percentage_gdp": 7.95}
            ]
        }
        
        model.apply_policy_mechanics(mechanics)
        
        # Calculate spending trajectory
        spending = model._calculate_policy_healthcare_spending(years=30)
        
        assert len(spending) == 30
        # First year should be close to baseline (~$350B)
        assert spending[0] > 300
        assert spending[0] < 500
        
        # Spending should transition toward target
        # After 19 years (to 2045), should be below initial level due to target
        # Since target is 7% GDP and "other health" is ~16% of federal health,
        # target is ~1.14% GDP from current ~1.25%
        print("✓ Policy-driven healthcare spending calculated")
        print(f"  Year 1 spending: ${spending[0]:.1f}B")
        print(f"  Year 30 spending: ${spending[29]:.1f}B")
    
    def test_unified_budget_with_policy(self):
        """Test that unified budget projection works with policy mechanics."""
        model = CombinedFiscalOutlookModel()
        
        # Apply policy mechanics
        mechanics = {
            "target_spending_pct_gdp": 7,
            "target_spending_year": 2045,
            "funding_mechanisms": [
                {"source_type": "payroll_tax", "percentage_gdp": 7.95}
            ],
            "spending_mechanics": {
                "medicaid_expansion": True,
                "national_health_fund": True
            }
        }
        
        model.apply_policy_mechanics(mechanics)
        
        # Run projection
        df = model.project_unified_budget(years=10, iterations=1000)
        
        assert "year" in df.columns
        assert "healthcare_spending" in df.columns  # Should be renamed from other_health_spending
        assert "total_revenue" in df.columns
        assert "total_spending" in df.columns
        assert "deficit_surplus" in df.columns
        
        assert len(df) == 10
        print("✓ Unified budget projection with policy mechanics successful")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Year 1 healthcare spending: ${df['healthcare_spending'].iloc[0]:.1f}B")
    
    def test_clear_policy_mechanics(self):
        """Test that clearing policy mechanics resets the model."""
        model = CombinedFiscalOutlookModel()
        
        # Apply mechanics
        model.apply_policy_mechanics({
            "target_spending_pct_gdp": 7,
            "target_spending_year": 2045,
        })
        
        assert model._healthcare_gdp_target == 7
        
        # Clear mechanics
        model.apply_policy_mechanics(None)
        
        assert model._healthcare_gdp_target is None
        assert model._healthcare_target_year is None
        assert model._policy_mechanics is None
        print("✓ Policy mechanics cleared successfully")


def run_tests():
    """Run all tests manually."""
    test = TestCombinedOutlookPolicyIntegration()
    
    print("\n" + "="*60)
    print("Running Combined Outlook Policy Integration Tests")
    print("="*60 + "\n")
    
    try:
        test.test_model_initialization()
        test.test_apply_policy_mechanics()
        test.test_policy_driven_healthcare_spending()
        test.test_unified_budget_with_policy()
        test.test_clear_policy_mechanics()
        
        print("\n" + "="*60)
        print("All tests passed! ✓")
        print("="*60)
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
