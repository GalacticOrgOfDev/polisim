"""
Logging configuration for polisim.

Provides centralized logging setup with structured formatting.

Usage:
    from utils.logging_config import setup_logging
    
    logger = setup_logging("my_module", verbose=True)
    logger.info("Starting operation...")
"""

import logging
import sys
from typing import Optional


def setup_logging(name: str, verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for a module.
    
    Args:
        name: Logger name (usually __name__)
        verbose: If True, set to DEBUG level; otherwise INFO
        log_file: Optional path to write logs to file
    
    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except IOError as e:
            logger.warning(f"Could not configure file logging: {e}")
    
    # Suppress noisy third-party loggers
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logger


class LoggingContext:
    """
    Context manager for temporary logging configuration.
    
    Usage:
        with LoggingContext("module", verbose=True):
            # Logging is verbose here
            logger.debug("Detailed info")
    """
    
    def __init__(self, name: str, verbose: bool = False):
        self.name = name
        self.verbose = verbose
        self.logger = None
        self.original_level = None
    
    def __enter__(self):
        self.logger = logging.getLogger(self.name)
        self.original_level = self.logger.level
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_level is not None:
            self.logger.setLevel(self.original_level)
        return False

