"""
Tests for Input Validation Module
Tests Safety #1 (PDF file size limits) and Safety #2 (parameter range validation)
"""

import pytest
import tempfile
from pathlib import Path

from core.validation import (
    InputValidator,
    ValidationError,
    validate_projection_params,
    validate_economic_params,
    validate_tax_params
)


class TestPDFSizeValidation:
    """Test Safety #1: PDF file size limits"""
    
    def test_valid_small_file(self):
        """Valid file under size limit should pass"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'x' * (1024 * 1024))  # 1MB file
            f.flush()
            temp_path = Path(f.name)
        
        try:
            InputValidator.validate_file_size(temp_path)  # Should not raise
        finally:
            temp_path.unlink()
    
    def test_file_exceeds_limit(self):
        """File exceeding 50MB limit should raise ValidationError"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Create 51MB file (exceeds default 50MB limit)
            f.write(b'x' * (51 * 1024 * 1024))
            f.flush()
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValidationError, match="exceeds maximum allowed 50MB"):
                InputValidator.validate_file_size(temp_path)
        finally:
            temp_path.unlink()
    
    def test_custom_size_limit(self):
        """Custom size limit should be respected"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'x' * (6 * 1024 * 1024))  # 6MB file
            f.flush()
            temp_path = Path(f.name)
        
        try:
            # Should pass with 10MB limit
            InputValidator.validate_file_size(temp_path, max_size_mb=10)
            
            # Should fail with 5MB limit
            with pytest.raises(ValidationError, match="exceeds maximum allowed 5MB"):
                InputValidator.validate_file_size(temp_path, max_size_mb=5)
        finally:
            temp_path.unlink()
    
    def test_nonexistent_file(self):
        """Non-existent file should raise FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            InputValidator.validate_file_size(Path("/nonexistent/file.pdf"))


class TestParameterRangeValidation:
    """Test Safety #2: Parameter range validation"""
    
    def test_valid_years(self):
        """Valid years (1-75) should pass"""
        InputValidator.validate_range(1, "years", param_type='years')
        InputValidator.validate_range(30, "years", param_type='years')
        InputValidator.validate_range(75, "years", param_type='years')
    
    def test_invalid_years_too_low(self):
        """Years < 1 should raise ValidationError"""
        with pytest.raises(ValidationError, match="below minimum"):
            InputValidator.validate_range(0, "years", param_type='years')
    
    def test_invalid_years_too_high(self):
        """Years > 75 should raise ValidationError"""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            InputValidator.validate_range(100, "years", param_type='years')
    
    def test_valid_iterations(self):
        """Valid iterations (100-50000) should pass"""
        InputValidator.validate_range(100, "iterations", param_type='iterations')
        InputValidator.validate_range(10000, "iterations", param_type='iterations')
        InputValidator.validate_range(50000, "iterations", param_type='iterations')
    
    def test_invalid_iterations_too_low(self):
        """Iterations < 100 should raise ValidationError"""
        with pytest.raises(ValidationError, match="below minimum"):
            InputValidator.validate_range(50, "iterations", param_type='iterations')
    
    def test_invalid_iterations_too_high(self):
        """Iterations > 50000 should raise ValidationError"""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            InputValidator.validate_range(100000, "iterations", param_type='iterations')
    
    def test_valid_gdp_growth(self):
        """Valid GDP growth (-10% to +15%) should pass"""
        InputValidator.validate_range(-0.10, "gdp_growth", param_type='gdp_growth')
        InputValidator.validate_range(0.02, "gdp_growth", param_type='gdp_growth')
        InputValidator.validate_range(0.15, "gdp_growth", param_type='gdp_growth')
    
    def test_invalid_gdp_growth(self):
        """GDP growth outside -10% to +15% should raise ValidationError"""
        with pytest.raises(ValidationError, match="below minimum"):
            InputValidator.validate_range(-0.20, "gdp_growth", param_type='gdp_growth')
        
        with pytest.raises(ValidationError, match="exceeds maximum"):
            InputValidator.validate_range(0.30, "gdp_growth", param_type='gdp_growth')
    
    def test_valid_tax_rate(self):
        """Valid tax rate (0% to 100%) should pass"""
        InputValidator.validate_range(0.0, "tax_rate", param_type='tax_rate')
        InputValidator.validate_range(0.35, "tax_rate", param_type='tax_rate')
        InputValidator.validate_range(1.0, "tax_rate", param_type='tax_rate')
    
    def test_invalid_tax_rate(self):
        """Tax rate > 100% should raise ValidationError"""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            InputValidator.validate_range(10.0, "tax_rate", param_type='tax_rate')
        
        with pytest.raises(ValidationError, match="below minimum"):
            InputValidator.validate_range(-0.1, "tax_rate", param_type='tax_rate')
    
    def test_valid_spending(self):
        """Valid spending amounts should pass"""
        InputValidator.validate_range(0, "spending", param_type='spending_billions')
        InputValidator.validate_range(5000, "spending", param_type='spending_billions')
        InputValidator.validate_range(50000, "spending", param_type='spending_billions')
    
    def test_invalid_spending(self):
        """Spending > $50T should raise ValidationError"""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            InputValidator.validate_range(100000, "spending", param_type='spending_billions')
    
    def test_valid_probability(self):
        """Valid probability (0.0-1.0) should pass"""
        InputValidator.validate_probability(0.0, "confidence")
        InputValidator.validate_probability(0.5, "confidence")
        InputValidator.validate_probability(1.0, "confidence")
    
    def test_invalid_probability(self):
        """Probability outside 0.0-1.0 should raise ValidationError"""
        with pytest.raises(ValidationError):
            InputValidator.validate_probability(-0.1, "confidence")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_probability(1.5, "confidence")


class TestScenarioValidation:
    """Test scenario name validation"""
    
    def test_valid_scenario(self):
        """Valid scenario name should pass"""
        valid = ['baseline', 'recession', 'growth']
        InputValidator.validate_scenario_name('baseline', valid)
        InputValidator.validate_scenario_name('recession', valid)
    
    def test_invalid_scenario(self):
        """Invalid scenario name should raise ValidationError"""
        valid = ['baseline', 'recession', 'growth']
        with pytest.raises(ValidationError, match="not a valid option"):
            InputValidator.validate_scenario_name('invalid', valid)


class TestConvenienceFunctions:
    """Test convenience validation functions"""
    
    def test_validate_positive(self):
        """Positive validation should work correctly"""
        InputValidator.validate_positive(0.1, "value")
        InputValidator.validate_positive(100, "value")
        
        with pytest.raises(ValidationError, match="must be positive"):
            InputValidator.validate_positive(0, "value")
        
        with pytest.raises(ValidationError, match="must be positive"):
            InputValidator.validate_positive(-1, "value")
    
    def test_validate_non_negative(self):
        """Non-negative validation should work correctly"""
        InputValidator.validate_non_negative(0, "value")
        InputValidator.validate_non_negative(100, "value")
        
        with pytest.raises(ValidationError, match="must be non-negative"):
            InputValidator.validate_non_negative(-1, "value")
    
    def test_validate_percentage_decimal(self):
        """Percentage validation (as decimal) should work"""
        InputValidator.validate_percentage(0.0, "rate", as_decimal=True)
        InputValidator.validate_percentage(0.5, "rate", as_decimal=True)
        InputValidator.validate_percentage(1.0, "rate", as_decimal=True)
        
        with pytest.raises(ValidationError):
            InputValidator.validate_percentage(1.5, "rate", as_decimal=True)
    
    def test_validate_percentage_integer(self):
        """Percentage validation (as integer) should work"""
        InputValidator.validate_percentage(0, "rate", as_decimal=False)
        InputValidator.validate_percentage(50, "rate", as_decimal=False)
        InputValidator.validate_percentage(100, "rate", as_decimal=False)
        
        with pytest.raises(ValidationError):
            InputValidator.validate_percentage(150, "rate", as_decimal=False)


class TestProjectionParamsValidation:
    """Test validate_projection_params convenience function"""
    
    def test_valid_projection_params(self):
        """Valid projection parameters should pass"""
        validate_projection_params(10, 1000)
        validate_projection_params(30, 10000)
        validate_projection_params(75, 50000)
    
    def test_invalid_years(self):
        """Invalid years should raise ValidationError"""
        with pytest.raises(ValidationError):
            validate_projection_params(0, 1000)
        
        with pytest.raises(ValidationError):
            validate_projection_params(100, 1000)
    
    def test_invalid_iterations(self):
        """Invalid iterations should raise ValidationError"""
        with pytest.raises(ValidationError):
            validate_projection_params(10, 50)
        
        with pytest.raises(ValidationError):
            validate_projection_params(10, 100000)


class TestEconomicParamsValidation:
    """Test validate_economic_params convenience function"""
    
    def test_valid_economic_params(self):
        """Valid economic parameters should pass"""
        validate_economic_params(
            gdp_growth=0.02,
            wage_growth=0.03,
            inflation=0.02,
            interest_rate=0.04
        )
    
    def test_invalid_gdp_growth(self):
        """Invalid GDP growth should raise ValidationError"""
        with pytest.raises(ValidationError):
            validate_economic_params(gdp_growth=0.30)
    
    def test_invalid_interest_rate(self):
        """Invalid interest rate should raise ValidationError"""
        with pytest.raises(ValidationError):
            validate_economic_params(interest_rate=-0.01)
        
        with pytest.raises(ValidationError):
            validate_economic_params(interest_rate=0.50)


class TestTaxParamsValidation:
    """Test validate_tax_params convenience function"""
    
    def test_valid_tax_params(self):
        """Valid tax parameters should pass"""
        validate_tax_params(
            tax_rate=0.35,
            marginal_rate=0.40,
            corporate_rate=0.21,
            wealth_tax_rate=0.02,
            carbon_tax=50.0
        )
    
    def test_invalid_tax_rate(self):
        """Invalid tax rate should raise ValidationError"""
        with pytest.raises(ValidationError):
            validate_tax_params(tax_rate=2.0)
    
    def test_invalid_carbon_tax(self):
        """Invalid carbon tax should raise ValidationError"""
        with pytest.raises(ValidationError):
            validate_tax_params(carbon_tax=-10)
        
        with pytest.raises(ValidationError):
            validate_tax_params(carbon_tax=1000)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_boundary_values(self):
        """Exact boundary values should pass"""
        # Test exact minimum
        InputValidator.validate_range(1, "years", param_type='years')
        # Test exact maximum
        InputValidator.validate_range(75, "years", param_type='years')
    
    def test_just_outside_boundaries(self):
        """Values just outside boundaries should fail"""
        # Just below minimum
        with pytest.raises(ValidationError):
            InputValidator.validate_range(0.99, "years", param_type='years')
        
        # Just above maximum
        with pytest.raises(ValidationError):
            InputValidator.validate_range(75.01, "years", param_type='years')
    
    def test_extreme_values(self):
        """Extreme values should be caught"""
        with pytest.raises(ValidationError):
            InputValidator.validate_range(-1000000, "spending", param_type='spending_billions')
        
        with pytest.raises(ValidationError):
            InputValidator.validate_range(1000000, "spending", param_type='spending_billions')
