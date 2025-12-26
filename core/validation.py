"""
Input Validation Module
Provides validation for all user inputs to prevent invalid parameters and system issues.

Implements:
- Safety #1: PDF file size limits
- Safety #2: Parameter range validation
- Common validation utilities for all models
"""

import os
from pathlib import Path
from typing import Union, Optional, Tuple, Any


class ValidationError(ValueError):
    """Custom exception for validation failures."""
    pass


class InputValidator:
    """Central validation for all model inputs."""
    
    # File size limits (Safety #1)
    MAX_PDF_SIZE_MB = 50
    MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024
    
    # Parameter ranges (Safety #2)
    VALID_RANGES = {
        # Projection parameters
        'years': (1, 75),  # Min 1 year, max 75 years (CBO long-term)
        'iterations': (100, 50000),  # Min 100 for stability, max 50K for performance
        
        # Economic parameters
        'gdp_growth': (-0.10, 0.15),  # -10% to +15% annual growth
        'wage_growth': (-0.05, 0.20),  # -5% to +20% annual wage growth
        'inflation': (0.00, 0.25),  # 0% to 25% annual inflation
        'interest_rate': (0.00, 0.25),  # 0% to 25% interest rates
        'unemployment': (0.01, 0.30),  # 1% to 30% unemployment
        
        # Tax rates
        'tax_rate': (0.00, 1.00),  # 0% to 100% (as decimal)
        'marginal_rate': (0.00, 1.00),  # 0% to 100% (as decimal)
        'corporate_rate': (0.00, 0.70),  # 0% to 70% corporate tax
        'wealth_tax_rate': (0.00, 0.20),  # 0% to 20% wealth tax
        'consumption_tax_rate': (0.00, 0.50),  # 0% to 50% consumption tax
        'carbon_tax': (0, 500),  # $0 to $500 per ton CO2
        'ftt_rate': (0.00, 0.05),  # 0% to 5% financial transaction tax
        
        # Spending parameters
        'spending_billions': (0, 50000),  # $0 to $50T per year
        'deficit_billions': (-10000, 50000),  # -$10T to +$50T (negative = surplus)
        'debt_billions': (0, 200000),  # $0 to $200T national debt
        
        # Healthcare parameters
        'coverage_rate': (0.00, 1.00),  # 0% to 100%
        'per_capita_spending': (0, 50000),  # $0 to $50K per person
        'admin_cost_rate': (0.00, 0.50),  # 0% to 50% administrative costs
        
        # Social Security
        'replacement_rate': (0.10, 1.50),  # 10% to 150% of average wage
        'cola': (-0.05, 0.15),  # -5% to +15% cost-of-living adjustment
        'retirement_age': (55, 75),  # Age 55 to 75
        
        # Probabilities/confidence
        'probability': (0.00, 1.00),  # 0 to 1
        'confidence': (0.00, 1.00),  # 0 to 1
    }
    
    @classmethod
    def validate_file_size(cls, file_path: Union[str, Path], max_size_mb: Optional[int] = None) -> None:
        """
        Validate file size is within acceptable limits (Safety #1).
        
        Args:
            file_path: Path to file to validate
            max_size_mb: Maximum size in MB (default: 50MB)
            
        Raises:
            ValidationError: If file is too large
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        max_bytes = (max_size_mb or cls.MAX_PDF_SIZE_MB) * 1024 * 1024
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size > max_bytes:
            raise ValidationError(
                f"File size {file_size_mb:.1f}MB exceeds maximum allowed "
                f"{max_size_mb or cls.MAX_PDF_SIZE_MB}MB. "
                f"Please provide a smaller file or split into multiple documents."
            )
    
    @classmethod
    def validate_range(
        cls,
        value: Union[int, float],
        param_name: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        param_type: Optional[str] = None
    ) -> None:
        """
        Validate parameter is within acceptable range (Safety #2).
        
        Args:
            value: The value to validate
            param_name: Name of parameter (for error messages)
            min_val: Minimum allowed value (optional, uses VALID_RANGES if param_type provided)
            max_val: Maximum allowed value (optional, uses VALID_RANGES if param_type provided)
            param_type: Type key in VALID_RANGES (optional)
            
        Raises:
            ValidationError: If value is out of range
        """
        # Get range from VALID_RANGES if param_type specified
        if param_type and param_type in cls.VALID_RANGES:
            min_val, max_val = cls.VALID_RANGES[param_type]
        
        if min_val is None and max_val is None:
            raise ValueError(f"Must specify either min_val/max_val or param_type for {param_name}")
        
        # Validate
        if min_val is not None and value < min_val:
            raise ValidationError(
                f"{param_name}={value} is below minimum allowed value of {min_val}. "
                f"Please provide a value >= {min_val}."
            )
        
        if max_val is not None and value > max_val:
            raise ValidationError(
                f"{param_name}={value} exceeds maximum allowed value of {max_val}. "
                f"Please provide a value <= {max_val}."
            )
    
    @classmethod
    def validate_positive(cls, value: Union[int, float], param_name: str) -> None:
        """Validate parameter is positive (> 0)."""
        if value <= 0:
            raise ValidationError(
                f"{param_name}={value} must be positive (> 0). "
                f"Please provide a value greater than zero."
            )
    
    @classmethod
    def validate_non_negative(cls, value: Union[int, float], param_name: str) -> None:
        """Validate parameter is non-negative (>= 0)."""
        if value < 0:
            raise ValidationError(
                f"{param_name}={value} must be non-negative (>= 0). "
                f"Please provide a value greater than or equal to zero."
            )
    
    @classmethod
    def validate_probability(cls, value: float, param_name: str) -> None:
        """Validate parameter is a probability (0.0 to 1.0)."""
        cls.validate_range(value, param_name, 0.0, 1.0, param_type='probability')
    
    @classmethod
    def validate_percentage(cls, value: float, param_name: str, as_decimal: bool = True) -> None:
        """
        Validate parameter is a percentage.
        
        Args:
            value: The percentage value
            param_name: Parameter name
            as_decimal: If True, expects 0.0-1.0; if False, expects 0-100
        """
        if as_decimal:
            cls.validate_range(value, param_name, 0.0, 1.0)
        else:
            cls.validate_range(value, param_name, 0, 100)
    
    @classmethod
    def validate_scenario_name(cls, scenario: str, valid_scenarios: list, param_name: str = "scenario") -> None:
        """
        Validate scenario name is in allowed list.
        
        Args:
            scenario: Scenario name to validate
            valid_scenarios: List of valid scenario names
            param_name: Parameter name for error message
            
        Raises:
            ValidationError: If scenario not in valid list
        """
        if scenario not in valid_scenarios:
            raise ValidationError(
                f"{param_name}='{scenario}' is not a valid option. "
                f"Valid options are: {', '.join(valid_scenarios)}"
            )
    
    @classmethod
    def validate_all(cls, **params) -> None:
        """
        Convenience method to validate multiple parameters at once.
        
        Example:
            validate_all(
                years=(10, 'years'),
                iterations=(1000, 'iterations'),
                gdp_growth=(0.02, 'gdp_growth')
            )
        """
        for param_name, (value, param_type) in params.items():
            if param_type in cls.VALID_RANGES:
                cls.validate_range(value, param_name, param_type=param_type)


def validate_projection_params(years: int, iterations: int) -> None:
    """
    Validate common projection parameters.
    
    Args:
        years: Number of years to project
        iterations: Monte Carlo iterations
        
    Raises:
        ValidationError: If parameters are invalid
    """
    InputValidator.validate_range(years, "years", param_type='years')
    InputValidator.validate_range(iterations, "iterations", param_type='iterations')


def validate_economic_params(
    gdp_growth: Optional[float] = None,
    wage_growth: Optional[float] = None,
    inflation: Optional[float] = None,
    interest_rate: Optional[float] = None
) -> None:
    """
    Validate economic parameters.
    
    Args:
        gdp_growth: GDP growth rate (as decimal)
        wage_growth: Wage growth rate (as decimal)
        inflation: Inflation rate (as decimal)
        interest_rate: Interest rate (as decimal)
        
    Raises:
        ValidationError: If any parameter is invalid
    """
    if gdp_growth is not None:
        InputValidator.validate_range(gdp_growth, "gdp_growth", param_type='gdp_growth')
    if wage_growth is not None:
        InputValidator.validate_range(wage_growth, "wage_growth", param_type='wage_growth')
    if inflation is not None:
        InputValidator.validate_range(inflation, "inflation", param_type='inflation')
    if interest_rate is not None:
        InputValidator.validate_range(interest_rate, "interest_rate", param_type='interest_rate')


def validate_tax_params(
    tax_rate: Optional[float] = None,
    marginal_rate: Optional[float] = None,
    corporate_rate: Optional[float] = None,
    wealth_tax_rate: Optional[float] = None,
    carbon_tax: Optional[float] = None
) -> None:
    """
    Validate tax parameters.
    
    Args:
        tax_rate: General tax rate (as decimal 0.0-1.0)
        marginal_rate: Marginal tax rate (as decimal 0.0-1.0)
        corporate_rate: Corporate tax rate (as decimal 0.0-1.0)
        wealth_tax_rate: Wealth tax rate (as decimal 0.0-1.0)
        carbon_tax: Carbon tax per ton CO2 ($)
        
    Raises:
        ValidationError: If any parameter is invalid
    """
    if tax_rate is not None:
        InputValidator.validate_range(tax_rate, "tax_rate", param_type='tax_rate')
    if marginal_rate is not None:
        InputValidator.validate_range(marginal_rate, "marginal_rate", param_type='marginal_rate')
    if corporate_rate is not None:
        InputValidator.validate_range(corporate_rate, "corporate_rate", param_type='corporate_rate')
    if wealth_tax_rate is not None:
        InputValidator.validate_range(wealth_tax_rate, "wealth_tax_rate", param_type='wealth_tax_rate')
    if carbon_tax is not None:
        InputValidator.validate_range(carbon_tax, "carbon_tax", param_type='carbon_tax')
