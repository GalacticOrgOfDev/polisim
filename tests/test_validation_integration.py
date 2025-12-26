"""
Integration Tests for Validation in Combined Outlook Model
Tests that validation catches invalid inputs in the main model
"""

import pytest
from core.combined_outlook import CombinedFiscalOutlookModel
from core.validation import ValidationError


class TestCombinedOutlookValidation:
    """Test that Combined Outlook Model properly validates inputs"""
    
    def setup_method(self):
        """Create model instance for each test"""
        self.model = CombinedFiscalOutlookModel()
    
    def test_valid_parameters(self):
        """Valid parameters should work without error"""
        df = self.model.project_unified_budget(
            years=10,
            iterations=1000,
            revenue_scenario='baseline',
            discretionary_scenario='baseline',
            interest_scenario='baseline'
        )
        assert len(df) == 10
        assert 'year' in df.columns
    
    def test_invalid_years_too_low(self):
        """Years < 1 should raise ValidationError"""
        with pytest.raises(ValidationError, match="below minimum"):
            self.model.project_unified_budget(years=0, iterations=1000)
    
    def test_invalid_years_too_high(self):
        """Years > 75 should raise ValidationError"""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            self.model.project_unified_budget(years=100, iterations=1000)
    
    def test_invalid_iterations_too_low(self):
        """Iterations < 100 should raise ValidationError"""
        with pytest.raises(ValidationError, match="below minimum"):
            self.model.project_unified_budget(years=10, iterations=50)
    
    def test_invalid_iterations_too_high(self):
        """Iterations > 50000 should raise ValidationError"""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            self.model.project_unified_budget(years=10, iterations=100000)
    
    def test_invalid_revenue_scenario(self):
        """Invalid revenue scenario should raise ValidationError"""
        with pytest.raises(ValidationError, match="not a valid option"):
            self.model.project_unified_budget(
                years=10,
                iterations=1000,
                revenue_scenario='invalid_scenario'
            )
    
    def test_invalid_discretionary_scenario(self):
        """Invalid discretionary scenario should raise ValidationError"""
        with pytest.raises(ValidationError, match="not a valid option"):
            self.model.project_unified_budget(
                years=10,
                iterations=1000,
                discretionary_scenario='invalid_scenario'
            )
    
    def test_invalid_interest_scenario(self):
        """Invalid interest scenario should raise ValidationError"""
        with pytest.raises(ValidationError, match="not a valid option"):
            self.model.project_unified_budget(
                years=10,
                iterations=1000,
                interest_scenario='invalid_scenario'
            )
    
    def test_boundary_values(self):
        """Boundary values (min/max) should work correctly"""
        # Minimum values
        df = self.model.project_unified_budget(years=1, iterations=100)
        assert len(df) == 1
        
        # Maximum values (use smaller values for performance)
        df = self.model.project_unified_budget(years=30, iterations=1000)
        assert len(df) == 30
    
    def test_typical_usage_patterns(self):
        """Common usage patterns should work correctly"""
        # Short-term projection
        df = self.model.project_unified_budget(years=5, iterations=1000)
        assert len(df) == 5
        
        # Medium-term projection (CBO 10-year)
        df = self.model.project_unified_budget(years=10, iterations=1000)
        assert len(df) == 10
        
        # Long-term projection (CBO 30-year)
        df = self.model.project_unified_budget(years=30, iterations=1000)
        assert len(df) == 30
    
    def test_all_revenue_scenarios(self):
        """All valid revenue scenarios should work"""
        for scenario in ['baseline', 'recession', 'strong_growth', 'demographic_challenge']:
            df = self.model.project_unified_budget(
                years=5,
                iterations=500,
                revenue_scenario=scenario
            )
            assert len(df) == 5
    
    def test_all_discretionary_scenarios(self):
        """All valid discretionary scenarios should work"""
        for scenario in ['baseline', 'growth', 'reduction']:
            df = self.model.project_unified_budget(
                years=5,
                iterations=500,
                discretionary_scenario=scenario
            )
            assert len(df) == 5
    
    def test_all_interest_scenarios(self):
        """All valid interest scenarios should work"""
        for scenario in ['baseline', 'rising', 'falling', 'spike']:
            df = self.model.project_unified_budget(
                years=5,
                iterations=500,
                interest_scenario=scenario
            )
            assert len(df) == 5


class TestPDFParserValidation:
    """Test that PDF parser validates file sizes"""
    
    def test_pdf_validation_import(self):
        """PDF parser should import validation correctly"""
        from core.pdf_policy_parser import PolicyPDFProcessor
        from pathlib import Path
        # Should not raise ImportError
        processor = PolicyPDFProcessor()
    
    def test_validation_error_in_extract(self):
        """Large file should be caught during extraction"""
        from core.pdf_policy_parser import PolicyPDFProcessor
        import tempfile
        from pathlib import Path
        
        # Create oversized file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'x' * (51 * 1024 * 1024))  # 51MB
            f.flush()
            temp_path = Path(f.name)
        
        processor = PolicyPDFProcessor()
        
        try:
            result = processor.extract_text_from_pdf(temp_path)
            # Should return error message, not raise exception
            assert "file size validation failed" in result.lower() or "exceeds maximum" in result.lower()
        finally:
            temp_path.unlink()
