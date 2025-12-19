"""
Configuration management for polisim.

Loads and manages YAML/JSON configuration files with hierarchical
parameter overrides (defaults -> config file -> environment -> CLI args).

Usage:
    from core.config import load_config, get_parameter
    
    # Load master config
    config = load_config('config.yaml')
    
    # Access nested parameters
    base_gdp = get_parameter(config, 'economic.base_gdp_trillion')
    healthcare_gdp = get_parameter(config, 'healthcare.current_healthcare_gdp_pct')
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


# Default configuration (fallback if files missing)
DEFAULT_CONFIG = {
    "economic": {
        "base_gdp_trillion": 29.0,
        "gdp_growth_rate": 0.025,
        "inflation_rate": 0.03,
        "national_debt_trillion": 35.0,
        "interest_rate": 0.04,
        "simulation_years": 10,
        "simulation_iterations": 100000,
    },
    "healthcare": {
        "current_coverage_pct": 92,
        "current_healthcare_gdp_pct": 18.0,
        "usgha_coverage_pct": 99,
        "usgha_healthcare_gdp_pct": 9.0,
    },
}


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML or JSON file.
    
    Falls back to DEFAULT_CONFIG if file not found.
    
    Args:
        config_file: Path to config.yaml or config.json
                    (if None, looks for config.yaml in current directory)
    
    Returns:
        Dict with configuration parameters
    """
    # Try multiple locations
    candidate_files = [
        config_file,
        "config.yaml",
        "config.json",
        os.path.join(os.path.dirname(__file__), "..", "config.yaml"),
    ]
    
    for file_path in candidate_files:
        if file_path is None:
            continue
        
        if os.path.exists(file_path):
            logger.info(f"Loading configuration from: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                        config = yaml.safe_load(f)
                    else:
                        config = json.load(f)
                
                logger.debug(f"Configuration loaded with {len(config)} top-level sections")
                return _merge_configs(DEFAULT_CONFIG, config)
            
            except (yaml.YAMLError, json.JSONDecodeError) as e:
                logger.error(f"Failed to parse config file {file_path}: {e}")
                raise ValueError(f"Invalid config file format: {e}")
            except IOError as e:
                logger.error(f"Error reading config file {file_path}: {e}")
                raise IOError(f"Cannot read config file: {e}")
    
    logger.warning(f"No config file found; using default configuration")
    return DEFAULT_CONFIG.copy()


def get_parameter(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a parameter from config using dot-notation path.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path (e.g., 'economic.base_gdp_trillion')
        default: Default value if key not found
    
    Returns:
        Parameter value, or default if not found
    
    Examples:
        >>> config = load_config()
        >>> gdp = get_parameter(config, 'economic.base_gdp_trillion', 29.0)
        >>> healthcare = get_parameter(config, 'healthcare.usgha_healthcare_gdp_pct', 9.0)
    """
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                logger.debug(f"Parameter not found: {key_path} (using default: {default})")
                return default
        else:
            logger.debug(f"Cannot navigate {key_path}: {key} not a dict")
            return default
    
    logger.debug(f"Retrieved parameter {key_path}: {value}")
    return value


def set_parameter(config: Dict[str, Any], key_path: str, value: Any) -> None:
    """
    Set a parameter in config using dot-notation path.
    
    Creates intermediate dictionaries if needed.
    
    Args:
        config: Configuration dictionary (modified in-place)
        key_path: Dot-separated path (e.g., 'economic.base_gdp_trillion')
        value: Value to set
    """
    keys = key_path.split('.')
    current = config
    
    # Navigate/create nested structure
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    logger.debug(f"Set parameter {key_path}: {value}")


def merge_with_environment_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge environment variable overrides into config.
    
    Looks for env vars in format: POLISIM_<KEY_PATH>
    (e.g., POLISIM_ECONOMIC_BASE_GDP_TRILLION=30.5)
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Updated configuration with env overrides
    """
    for env_key, env_value in os.environ.items():
        if env_key.startswith("POLISIM_"):
            config_key = env_key[8:].lower()  # Remove "POLISIM_" prefix
            
            # Try to convert to appropriate type
            try:
                # Try float
                if '.' in env_value:
                    typed_value = float(env_value)
                else:
                    # Try int
                    typed_value = int(env_value)
            except ValueError:
                # Keep as string
                typed_value = env_value
            
            set_parameter(config, config_key, typed_value)
            logger.debug(f"Applied environment override: {config_key} = {typed_value}")
    
    return config


def save_config(config: Dict[str, Any], output_file: str, format: str = "yaml") -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary
        output_file: Path to write config file
        format: "yaml" or "json" format
    
    Raises:
        IOError: If file write fails
    """
    logger.info(f"Saving configuration to: {output_file} ({format})")
    
    try:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            if format.lower() in ['yaml', 'yml']:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(config, f, indent=2)
        
        logger.info(f"✓ Configuration saved to {output_file}")
    
    except IOError as e:
        logger.error(f"Failed to save config: {e}")
        raise IOError(f"Cannot write config file: {e}")


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration parameters.
    
    Returns list of warnings (empty if valid).
    
    Args:
        config: Configuration dictionary
    
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Economic validation
    gdp_growth = get_parameter(config, 'economic.gdp_growth_rate', 0.025)
    if gdp_growth < -0.15:
        warnings.append(f"GDP growth rate {gdp_growth*100:.1f}% is very negative")
    if gdp_growth > 0.10:
        warnings.append(f"GDP growth rate {gdp_growth*100:.1f}% is unrealistically high")
    
    inflation = get_parameter(config, 'economic.inflation_rate', 0.03)
    if inflation > 0.30:
        warnings.append(f"Inflation rate {inflation*100:.1f}% is very high (hyperinflation risk)")
    
    # Healthcare validation
    current_healthcare = get_parameter(config, 'healthcare.current_healthcare_gdp_pct', 18.0)
    if current_healthcare < 5 or current_healthcare > 25:
        warnings.append(f"Current healthcare % GDP {current_healthcare:.1f}% seems unrealistic")
    
    if warnings:
        logger.warning(f"Configuration validation found {len(warnings)} issue(s)")
        for w in warnings:
            logger.warning(f"  - {w}")
    else:
        logger.info("Configuration validation passed")
    
    return warnings


def _merge_configs(base: Dict, override: Dict) -> Dict:
    """Recursively merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


class ConfigManager:
    """Context manager for temporary config overrides."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional starting config."""
        self.config = config or load_config()
        self._original_config = None
    
    def __enter__(self):
        """Enter context manager."""
        self._original_config = self.config.copy()
        return self.config
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original config on exit."""
        if self._original_config:
            self.config = self._original_config
        return False
    
    def set(self, key: str, value: Any) -> None:
        """Set parameter value."""
        set_parameter(self.config, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get parameter value."""
        return get_parameter(self.config, key, default)

