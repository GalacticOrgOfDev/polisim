"""
Edge Case Handlers
Provides robust handling for edge cases and extreme scenarios.

Implements safeguards for:
- Edge Case #1: Zero/negative GDP growth (recession scenarios)
- Edge Case #10: Missing CBO data (fallback mechanisms)
- Division by zero protection
- Extreme value detection and warnings
"""

import logging
import numpy as np
from typing import Optional, Dict, Any, Tuple
import warnings

logger = logging.getLogger(__name__)


class EdgeCaseError(Exception):
    """Raised when an edge case cannot be safely handled."""
    pass


class EdgeCaseHandler:
    """Central handler for edge cases and extreme scenarios."""
    
    # Thresholds for extreme value detection
    EXTREME_GDP_GROWTH_MIN = -0.15  # -15% (worse than Great Depression)
    EXTREME_GDP_GROWTH_MAX = 0.20   # +20% (unrealistic sustained growth)
    EXTREME_INFLATION_MIN = -0.05   # -5% (deflation)
    EXTREME_INFLATION_MAX = 0.25    # 25% (hyperinflation threshold)
    EXTREME_DEBT_GDP_RATIO = 2.5    # 250% debt-to-GDP (worse than Japan)
    EXTREME_INTEREST_RATE_MAX = 0.25  # 25% (crisis level)
    
    # Minimum values to prevent division by zero
    MIN_GDP = 1.0  # $1 trillion minimum GDP
    MIN_POPULATION = 1_000_000  # 1 million minimum population
    MIN_SPENDING = 0.01  # $10 billion minimum
    
    @classmethod
    def handle_recession_gdp_growth(
        cls,
        gdp_growth: float,
        year: Optional[int] = None,
        allow_negative: bool = True
    ) -> Tuple[float, bool]:
        """
        Handle zero or negative GDP growth (Edge Case #1).
        
        Args:
            gdp_growth: GDP growth rate (as decimal, e.g., -0.05 for -5%)
            year: Year of projection (for logging)
            allow_negative: If False, floor at 0% growth
            
        Returns:
            (adjusted_growth, was_adjusted)
        """
        was_adjusted = False
        original_growth = gdp_growth
        
        # Check for extreme negative growth
        if gdp_growth < cls.EXTREME_GDP_GROWTH_MIN:
            warnings.warn(
                f"Extreme GDP contraction detected: {gdp_growth*100:.1f}% "
                f"(year {year if year else 'unknown'}). "
                f"This is worse than the Great Depression (-12.9% in 1932). "
                f"Capping at {cls.EXTREME_GDP_GROWTH_MIN*100:.1f}%.",
                UserWarning
            )
            gdp_growth = cls.EXTREME_GDP_GROWTH_MIN
            was_adjusted = True
        
        # Check for extreme positive growth
        if gdp_growth > cls.EXTREME_GDP_GROWTH_MAX:
            warnings.warn(
                f"Extreme GDP growth detected: {gdp_growth*100:.1f}% "
                f"(year {year if year else 'unknown'}). "
                f"Sustained growth above 10% is historically rare. "
                f"Capping at {cls.EXTREME_GDP_GROWTH_MAX*100:.1f}%.",
                UserWarning
            )
            gdp_growth = cls.EXTREME_GDP_GROWTH_MAX
            was_adjusted = True
        
        # Handle zero/negative growth if not allowed
        if not allow_negative and gdp_growth <= 0:
            logger.warning(
                f"Negative GDP growth {gdp_growth*100:.2f}% (year {year}) "
                f"not allowed in this context. Flooring at 0%."
            )
            gdp_growth = 0.0
            was_adjusted = True
        
        if was_adjusted:
            logger.info(
                f"GDP growth adjusted: {original_growth*100:.2f}% → "
                f"{gdp_growth*100:.2f}% (year {year})"
            )
        
        return gdp_growth, was_adjusted
    
    @classmethod
    def safe_divide(
        cls,
        numerator: float,
        denominator: float,
        default: float = 0.0,
        context: str = ""
    ) -> float:
        """
        Safe division with zero handling.
        
        Args:
            numerator: Value to divide
            denominator: Value to divide by
            default: Return value if division by zero
            context: Description for logging
            
        Returns:
            Result of division or default if denominator is zero
        """
        if abs(denominator) < 1e-10:  # Effectively zero
            if context:
                logger.warning(
                    f"Division by zero in {context}: "
                    f"{numerator}/{denominator} = {default} (default)"
                )
            else:
                logger.warning(
                    f"Division by zero: {numerator}/{denominator} = {default} (default)"
                )
            return default
        
        result = numerator / denominator
        
        # Check for inf or nan
        if not np.isfinite(result):
            logger.warning(
                f"Non-finite result in {context}: "
                f"{numerator}/{denominator} = {result}, returning {default}"
            )
            return default
        
        return result
    
    @classmethod
    def validate_gdp(cls, gdp: float, year: Optional[int] = None) -> float:
        """
        Validate and adjust GDP to prevent division by zero.
        
        Args:
            gdp: GDP value in trillions
            year: Year for logging
            
        Returns:
            Validated GDP (minimum MIN_GDP)
        """
        if gdp < cls.MIN_GDP:
            logger.warning(
                f"GDP ${gdp:.3f}T (year {year}) is below minimum ${cls.MIN_GDP}T. "
                f"Using minimum to prevent division by zero."
            )
            return cls.MIN_GDP
        return gdp
    
    @classmethod
    def validate_population(cls, population: float, year: Optional[int] = None) -> float:
        """
        Validate population to prevent division by zero in per-capita calculations.
        
        Args:
            population: Population count
            year: Year for logging
            
        Returns:
            Validated population (minimum MIN_POPULATION)
        """
        if population < cls.MIN_POPULATION:
            logger.warning(
                f"Population {population:,.0f} (year {year}) is below minimum "
                f"{cls.MIN_POPULATION:,}. Using minimum to prevent division by zero."
            )
            return cls.MIN_POPULATION
        return population
    
    @classmethod
    def check_extreme_debt(
        cls,
        debt: float,
        gdp: float,
        year: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for extreme debt levels (Edge Case #9).
        
        Args:
            debt: National debt in trillions
            gdp: GDP in trillions
            year: Year for logging
            
        Returns:
            (is_extreme, warning_message)
        """
        debt_to_gdp = cls.safe_divide(debt, gdp, context="debt-to-GDP ratio")
        
        if debt_to_gdp > cls.EXTREME_DEBT_GDP_RATIO:
            message = (
                f"Extreme debt-to-GDP ratio detected: {debt_to_gdp*100:.1f}% "
                f"(year {year if year else 'unknown'}). "
                f"This exceeds Japan's peak of ~240%. "
                f"Model predictions may be unreliable at these extreme levels."
            )
            logger.warning(message)
            return True, message
        
        return False, None
    
    @classmethod
    def check_extreme_inflation(
        cls,
        inflation: float,
        year: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for extreme inflation (Edge Case #3).
        
        Args:
            inflation: Inflation rate (as decimal)
            year: Year for logging
            
        Returns:
            (is_extreme, warning_message)
        """
        if inflation < cls.EXTREME_INFLATION_MIN:
            message = (
                f"Severe deflation detected: {inflation*100:.1f}% "
                f"(year {year if year else 'unknown'}). "
                f"This may indicate economic crisis."
            )
            logger.warning(message)
            return True, message
        
        if inflation > cls.EXTREME_INFLATION_MAX:
            message = (
                f"Hyperinflation detected: {inflation*100:.1f}% "
                f"(year {year if year else 'unknown'}). "
                f"Model assumptions may not hold in hyperinflation scenarios."
            )
            logger.warning(message)
            return True, message
        
        return False, None
    
    @classmethod
    def check_extreme_interest_rate(
        cls,
        interest_rate: float,
        year: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for extreme interest rates.
        
        Args:
            interest_rate: Interest rate (as decimal)
            year: Year for logging
            
        Returns:
            (is_extreme, warning_message)
        """
        if interest_rate > cls.EXTREME_INTEREST_RATE_MAX:
            message = (
                f"Extreme interest rate detected: {interest_rate*100:.1f}% "
                f"(year {year if year else 'unknown'}). "
                f"This exceeds typical crisis levels (Paul Volcker's peak was 20%)."
            )
            logger.warning(message)
            return True, message
        
        return False, None
    
    @classmethod
    def handle_missing_cbo_data(
        cls,
        requested_data: str,
        fallback_data: Optional[Dict[str, Any]] = None,
        cached_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle missing CBO data with fallback (Edge Case #10).
        
        Args:
            requested_data: Type of data requested
            fallback_data: Optional fallback data to use
            cached_data: Optional cached data to use
            
        Returns:
            Best available data (fallback > cached > hardcoded defaults)
        """
        logger.warning(
            f"CBO data unavailable for '{requested_data}'. "
            f"Using fallback data."
        )
        
        # Use fallback if provided
        if fallback_data:
            logger.info(f"Using provided fallback data for '{requested_data}'")
            return fallback_data
        
        # Use cached data if available
        if cached_data and requested_data in cached_data:
            logger.info(f"Using cached data for '{requested_data}'")
            return cached_data[requested_data]
        
        # Hardcoded defaults as last resort
        defaults = cls._get_default_cbo_data(requested_data)
        logger.warning(
            f"No fallback or cached data available. "
            f"Using hardcoded defaults for '{requested_data}'"
        )
        return defaults
    
    @classmethod
    def _get_default_cbo_data(cls, data_type: str) -> Dict[str, Any]:
        """
        Get hardcoded default data as last resort.
        
        Args:
            data_type: Type of data requested
            
        Returns:
            Default data dictionary
        """
        defaults = {
            'gdp': {'value': 28.0, 'growth': 0.02, 'source': 'hardcoded_default'},
            'revenues': {
                'income_tax': 2.4,
                'payroll_tax': 1.6,
                'corporate_tax': 0.5,
                'other': 0.7,
                'total': 5.2,
                'source': 'hardcoded_default'
            },
            'spending': {
                'social_security': 1.4,
                'medicare': 0.9,
                'medicaid': 0.6,
                'defense': 0.8,
                'interest_debt': 0.7,
                'other_mandatory': 0.8,
                'other_discretionary': 1.0,
                'total': 6.2,
                'source': 'hardcoded_default'
            },
            'debt': {'value': 36.0, 'source': 'hardcoded_default'},
            'interest_rate': {'value': 0.04, 'source': 'hardcoded_default'},
        }
        
        return defaults.get(data_type, {'error': 'Unknown data type', 'source': 'error'})
    
    @classmethod
    def validate_percentages(
        cls,
        *percentages: float,
        context: str = "",
        allow_negative: bool = False,
        allow_over_100: bool = False
    ) -> bool:
        """
        Validate that percentages are in valid range.
        
        Args:
            *percentages: Percentage values to validate (as decimals 0.0-1.0)
            context: Description for logging
            allow_negative: Allow negative percentages
            allow_over_100: Allow percentages > 100%
            
        Returns:
            True if all valid, False otherwise
        """
        min_val = -1.0 if allow_negative else 0.0
        max_val = float('inf') if allow_over_100 else 1.0
        
        for i, pct in enumerate(percentages):
            if pct < min_val or pct > max_val:
                logger.error(
                    f"Invalid percentage in {context}: {pct*100:.1f}% "
                    f"(index {i}). Must be between {min_val*100:.0f}% and {max_val*100:.0f}%."
                )
                return False
        
        return True
    
    @classmethod
    def clamp_value(
        cls,
        value: float,
        min_val: float,
        max_val: float,
        name: str = "value"
    ) -> Tuple[float, bool]:
        """
        Clamp value to range [min_val, max_val].
        
        Args:
            value: Value to clamp
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            name: Name of value for logging
            
        Returns:
            (clamped_value, was_clamped)
        """
        original = value
        was_clamped = False
        
        if value < min_val:
            value = min_val
            was_clamped = True
        elif value > max_val:
            value = max_val
            was_clamped = True
        
        if was_clamped:
            logger.warning(
                f"{name} clamped: {original} → {value} "
                f"(range: [{min_val}, {max_val}])"
            )
        
        return value, was_clamped


def safe_percentage_of_gdp(
    amount: float,
    gdp: float,
    context: str = ""
) -> float:
    """
    Calculate percentage of GDP safely.
    
    Args:
        amount: Dollar amount (in same units as GDP)
        gdp: GDP value
        context: Description for logging
        
    Returns:
        Percentage (as decimal)
    """
    gdp = EdgeCaseHandler.validate_gdp(gdp)
    return EdgeCaseHandler.safe_divide(amount, gdp, default=0.0, context=context)


def safe_per_capita(
    total: float,
    population: float,
    context: str = ""
) -> float:
    """
    Calculate per-capita value safely.
    
    Args:
        total: Total amount
        population: Population count
        context: Description for logging
        
    Returns:
        Per-capita value
    """
    population = EdgeCaseHandler.validate_population(population)
    return EdgeCaseHandler.safe_divide(total, population, default=0.0, context=context)
