"""
Configuration Management for PoliSim

Phase 6.2.3: Centralized configuration management with:
- Environment-based configuration (dev/staging/prod)
- Secure secrets loading through secrets_manager
- Configuration validation
- Default values with overrides
"""

import os
import logging
from typing import Optional, Dict, Any, Type, TypeVar
from dataclasses import dataclass, field
from enum import Enum

from api.secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


T = TypeVar('T')


def get_env() -> Environment:
    """Get current environment."""
    env_str = os.getenv('FLASK_ENV', 'development').lower()
    return Environment[env_str.upper()] if env_str.upper() in Environment.__members__ else Environment.DEVELOPMENT


def get_config_value(
    key: str,
    default: Optional[T] = None,
    env_prefix: str = "POLISIM_",
    secret: bool = False
) -> Optional[T]:
    """
    Get configuration value with fallback chain:
    1. Secrets manager (if secret=True)
    2. Environment variable
    3. Default value
    
    Args:
        key: Configuration key
        default: Default value
        env_prefix: Environment variable prefix
        secret: Whether to load from secrets manager
        
    Returns:
        Configuration value
    """
    # Try secrets manager first if marked as secret
    if secret:
        secrets = get_secrets_manager()
        value = secrets.get(key)
        if value is not None:
            return value
    
    # Try environment variable
    env_key = f"{env_prefix}{key}"
    env_value = os.getenv(env_key)
    if env_value is not None:
        return env_value
    
    return default


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: Optional[str] = field(default=None)
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    
    def __post_init__(self):
        """Load database URL from secrets manager or environment."""
        if not self.url:
            secrets = get_secrets_manager()
            self.url = secrets.get('DATABASE_URL')
        
        if not self.url:
            self.url = os.getenv('DATABASE_URL')
        
        if not self.url:
            # Default to SQLite for development
            from pathlib import Path
            db_path = Path(__file__).resolve().parents[1] / 'databases' / 'polisim.db'
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.url = f"sqlite:///{db_path.as_posix()}"
        
        logger.info(f"Database configured: {self.url[:50]}...")


@dataclass
class JWTConfig:
    """JWT configuration."""
    secret_key: str = field(default="")
    refresh_secret_key: str = field(default="")
    algorithm: str = "HS256"
    expiration_hours: int = 24
    refresh_expiration_days: int = 7
    
    def __post_init__(self):
        """Load JWT secrets from secrets manager or environment."""
        if not self.secret_key:
            secrets = get_secrets_manager()
            self.secret_key = secrets.get('JWT_SECRET_KEY')
        
        if not self.secret_key:
            self.secret_key = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
        
        if not self.refresh_secret_key:
            secrets = get_secrets_manager()
            self.refresh_secret_key = secrets.get('JWT_REFRESH_SECRET')
        
        if not self.refresh_secret_key:
            self.refresh_secret_key = os.getenv('JWT_REFRESH_SECRET', 'dev-refresh-secret-change-in-production')
        
        # Load configurable values from environment
        self.algorithm = os.getenv('JWT_ALGORITHM', self.algorithm)
        self.expiration_hours = int(os.getenv('JWT_EXPIRATION_HOURS', self.expiration_hours))
        self.refresh_expiration_days = int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', self.refresh_expiration_days))


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    require_auth: bool = True
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20
    max_payload_mb: int = 10
    timeout_seconds: int = 300
    cors_allowed_origins: str = "http://localhost:3000"
    
    def __post_init__(self):
        """Load API configuration from environment."""
        self.host = os.getenv('FLASK_HOST', self.host)
        self.port = int(os.getenv('FLASK_PORT', self.port))
        self.debug = os.getenv('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
        self.require_auth = os.getenv('API_REQUIRE_AUTH', 'true').lower() in ('1', 'true', 'yes')
        self.rate_limit_enabled = os.getenv('API_RATE_LIMIT_ENABLED', 'true').lower() in ('1', 'true', 'yes')
        self.rate_limit_per_minute = int(os.getenv('API_RATE_LIMIT_PER_MINUTE', self.rate_limit_per_minute))
        self.rate_limit_burst = int(os.getenv('API_RATE_LIMIT_BURST', self.rate_limit_burst))
        self.max_payload_mb = int(os.getenv('API_MAX_PAYLOAD_MB', self.max_payload_mb))
        self.timeout_seconds = int(os.getenv('API_TIMEOUT_SECONDS', self.timeout_seconds))
        self.cors_allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', self.cors_allowed_origins)
    
    def get_cors_origins(self) -> list:
        """Parse CORS allowed origins."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(',') if origin.strip()]


@dataclass
class SecurityConfig:
    """Security configuration."""
    https_only: bool = True
    secure_cookies: bool = True
    session_timeout_minutes: int = 30
    password_min_length: int = 8
    password_require_special: bool = True
    max_login_attempts: int = 5
    login_attempt_timeout_minutes: int = 15
    
    def __post_init__(self):
        """Load security configuration from environment."""
        self.https_only = os.getenv('HTTPS_ONLY', 'true').lower() in ('1', 'true', 'yes')
        self.secure_cookies = os.getenv('SECURE_COOKIES', 'true').lower() in ('1', 'true', 'yes')
        self.session_timeout_minutes = int(os.getenv('SESSION_TIMEOUT_MINUTES', self.session_timeout_minutes))
        self.password_min_length = int(os.getenv('PASSWORD_MIN_LENGTH', self.password_min_length))
        self.password_require_special = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() in ('1', 'true', 'yes')
        self.max_login_attempts = int(os.getenv('MAX_LOGIN_ATTEMPTS', self.max_login_attempts))
        self.login_attempt_timeout_minutes = int(os.getenv('LOGIN_ATTEMPT_TIMEOUT_MINUTES', self.login_attempt_timeout_minutes))


@dataclass
class SecretRotationConfig:
    """Configuration for secret rotation."""
    enabled: bool = True
    database_password_days: int = 90  # Rotate every 90 days
    api_keys_days: int = 180  # Rotate every 180 days
    jwt_secret_days: int = 365  # Rotate annually
    
    def __post_init__(self):
        """Load rotation configuration from environment."""
        self.enabled = os.getenv('SECRET_ROTATION_ENABLED', 'true').lower() in ('1', 'true', 'yes')
        self.database_password_days = int(os.getenv('SECRET_ROTATION_DB_PASSWORD_DAYS', self.database_password_days))
        self.api_keys_days = int(os.getenv('SECRET_ROTATION_API_KEYS_DAYS', self.api_keys_days))
        self.jwt_secret_days = int(os.getenv('SECRET_ROTATION_JWT_SECRET_DAYS', self.jwt_secret_days))


class Config:
    """Main configuration class."""
    
    def __init__(self):
        """Initialize all configuration."""
        self.environment = get_env()
        self.debug = self.environment == Environment.DEVELOPMENT
        
        # Load configuration sections
        self.database = DatabaseConfig()
        self.jwt = JWTConfig()
        self.api = APIConfig()
        self.security = SecurityConfig()
        self.secret_rotation = SecretRotationConfig()
        
        logger.info(f"Configuration loaded for environment: {self.environment.value}")
        logger.debug(f"Debug mode: {self.debug}")
    
    def validate(self) -> bool:
        """Validate configuration."""
        errors = []
        
        # Validate database
        if not self.database.url:
            errors.append("Database URL not configured")
        
        # Validate JWT
        if not self.jwt.secret_key or self.jwt.secret_key == 'dev-secret-key-change-in-production':
            if self.environment == Environment.PRODUCTION:
                errors.append("JWT secret key not properly configured for production")
        
        # Validate API
        if self.api.port < 1 or self.api.port > 65535:
            errors.append(f"Invalid API port: {self.api.port}")
        
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding secrets)."""
        return {
            'environment': self.environment.value,
            'debug': self.debug,
            'database': {
                'url': self.database.url[:50] + '...' if self.database.url else None,
                'pool_size': self.database.pool_size,
            },
            'jwt': {
                'algorithm': self.jwt.algorithm,
                'expiration_hours': self.jwt.expiration_hours,
            },
            'api': {
                'host': self.api.host,
                'port': self.api.port,
                'rate_limit_enabled': self.api.rate_limit_enabled,
                'rate_limit_per_minute': self.api.rate_limit_per_minute,
            },
            'security': {
                'https_only': self.security.https_only,
                'session_timeout_minutes': self.security.session_timeout_minutes,
            },
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global configuration."""
    global _config
    if _config is None:
        _config = Config()
        _config.validate()
    return _config


# Initialize on import
_config = Config()
logger.info(f"Configuration initialized: {_config.environment.value}")
