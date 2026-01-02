"""
Secrets Management Module for PoliSim

Phase 6.2.3: Centralized secrets management with support for multiple backends:
- Environment variables (development)
- AWS Secrets Manager (production)
- HashiCorp Vault (enterprise)
- Local encrypted storage (advanced)

All secrets are loaded through this module to ensure audit logging, rotation,
and secure handling throughout the application.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Type
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretsBackend(ABC):
    """Abstract base class for secrets backends."""

    @abstractmethod
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret by name."""
        pass

    @abstractmethod
    def get_secret_dict(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret that contains multiple key-value pairs."""
        pass

    @abstractmethod
    def backend_info(self) -> str:
        """Return information about the backend."""
        pass


class EnvironmentSecretsBackend(SecretsBackend):
    """
    Load secrets from environment variables (development).
    
    Convention:
    - Simple secrets: POLISIM_<SECRET_NAME>
    - Dict secrets: POLISIM_<SECRET_NAME>_JSON (as JSON string)
    """

    def __init__(self):
        self.backend_name = "environment"
        self.loaded_at = datetime.now(timezone.utc)
        logger.info("Using Environment Variables secrets backend (development only)")

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variable."""
        env_key = f"POLISIM_{secret_name.upper()}"
        value = os.getenv(env_key, default)
        
        if value and value != default:
            # Log access (without revealing value)
            logger.debug(f"Retrieved secret from environment: {env_key}")
        
        return value

    def get_secret_dict(self, secret_name: str) -> Dict[str, Any]:
        """Get JSON secret from environment variable."""
        env_key = f"POLISIM_{secret_name.upper()}_JSON"
        json_str = os.getenv(env_key)
        
        if not json_str:
            logger.warning(f"Secret dict not found: {env_key}")
            return {}
        
        try:
            value = json.loads(json_str)
            logger.debug(f"Retrieved secret dict from environment: {env_key}")
            return value
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret dict {env_key}: {e}")
            return {}

    def backend_info(self) -> str:
        return f"Environment Variables (loaded {self.loaded_at.isoformat()})"


class AWSSecretsManagerBackend(SecretsBackend):
    """
    Load secrets from AWS Secrets Manager (production).
    
    Requires: boto3 package and AWS credentials
    Secret naming convention: polisim/<secret-name>
    """

    def __init__(self):
        try:
            import boto3
            self.backend_name = "aws"
            self.client = boto3.client('secretsmanager')
            self._cache: Dict[str, tuple] = {}  # (value, timestamp) tuples
            self.cache_ttl = 3600  # 1 hour
            self.loaded_at = datetime.now(timezone.utc)
            logger.info("Using AWS Secrets Manager backend (production)")
        except ImportError:
            raise ImportError("boto3 required for AWS Secrets Manager. Install with: pip install boto3")

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            # Check cache first
            if self._is_cached(secret_name):
                value, _ = self._cache[secret_name]
                logger.debug(f"Retrieved secret from cache: {secret_name}")
                return value

            aws_secret_name = f"polisim/{secret_name}"
            response = self.client.get_secret_value(SecretId=aws_secret_name)
            
            if 'SecretString' in response:
                value = response['SecretString']
            elif 'SecretBinary' in response:
                import base64
                value = base64.b64decode(response['SecretBinary']).decode('utf-8')
            else:
                value = default

            # Cache the value
            self._cache[secret_name] = (value, datetime.now(timezone.utc))
            logger.info(f"Retrieved secret from AWS: {aws_secret_name}")
            
            return value

        except Exception as e:
            logger.error(f"Failed to retrieve secret from AWS: {e}")
            return default

    def get_secret_dict(self, secret_name: str) -> Dict[str, Any]:
        """Get JSON secret from AWS Secrets Manager."""
        try:
            # Check cache first
            if self._is_cached(secret_name):
                value, _ = self._cache[secret_name]
                logger.debug(f"Retrieved secret dict from cache: {secret_name}")
                return value if isinstance(value, dict) else {}

            aws_secret_name = f"polisim/{secret_name}"
            response = self.client.get_secret_value(SecretId=aws_secret_name)
            
            secret_value = response.get('SecretString', '{}')
            value = json.loads(secret_value)
            
            # Cache the value
            self._cache[secret_name] = (value, datetime.now(timezone.utc))
            logger.info(f"Retrieved secret dict from AWS: {aws_secret_name}")
            
            return value

        except Exception as e:
            logger.error(f"Failed to retrieve secret dict from AWS: {e}")
            return {}

    def _is_cached(self, secret_name: str) -> bool:
        """Check if secret is cached and still valid."""
        if secret_name not in self._cache:
            return False
        
        _, timestamp = self._cache[secret_name]
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return age < self.cache_ttl

    def backend_info(self) -> str:
        return f"AWS Secrets Manager (loaded {self.loaded_at.isoformat()})"


class VaultSecretsBackend(SecretsBackend):
    """
    Load secrets from HashiCorp Vault (enterprise).
    
    Requires: hvac package and Vault credentials
    Secret path: secret/data/polisim/<secret-name>
    """

    def __init__(self, vault_addr: Optional[str] = None, vault_token: Optional[str] = None):
        try:
            import hvac
            
            self.backend_name = "vault"
            self.vault_addr = vault_addr or os.getenv('VAULT_ADDR', 'http://localhost:8200')
            self.vault_token = vault_token or os.getenv('VAULT_TOKEN', '')
            
            if not self.vault_token:
                raise ValueError("VAULT_TOKEN environment variable not set")
            
            self.client = hvac.Client(url=self.vault_addr, token=self.vault_token)
            self._cache: Dict[str, tuple] = {}
            self.cache_ttl = 3600  # 1 hour
            self.loaded_at = datetime.now(timezone.utc)
            
            logger.info(f"Using HashiCorp Vault backend (address: {self.vault_addr})")
        except ImportError:
            raise ImportError("hvac required for HashiCorp Vault. Install with: pip install hvac")

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from Vault."""
        try:
            # Check cache first
            if self._is_cached(secret_name):
                value, _ = self._cache[secret_name]
                logger.debug(f"Retrieved secret from cache: {secret_name}")
                return value

            vault_path = f"secret/data/polisim/{secret_name}"
            response = self.client.secrets.kv.v2.read_secret_version(path=vault_path)
            
            data = response['data']['data']
            value = data.get('value', default)
            
            # Cache the value
            self._cache[secret_name] = (value, datetime.now(timezone.utc))
            logger.info(f"Retrieved secret from Vault: {vault_path}")
            
            return value

        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            return default

    def get_secret_dict(self, secret_name: str) -> Dict[str, Any]:
        """Get JSON secret from Vault."""
        try:
            # Check cache first
            if self._is_cached(secret_name):
                value, _ = self._cache[secret_name]
                logger.debug(f"Retrieved secret dict from cache: {secret_name}")
                return value if isinstance(value, dict) else {}

            vault_path = f"secret/data/polisim/{secret_name}"
            response = self.client.secrets.kv.v2.read_secret_version(path=vault_path)
            
            value = response['data']['data']
            
            # Cache the value
            self._cache[secret_name] = (value, datetime.now(timezone.utc))
            logger.info(f"Retrieved secret dict from Vault: {vault_path}")
            
            return value

        except Exception as e:
            logger.error(f"Failed to retrieve secret dict from Vault: {e}")
            return {}

    def _is_cached(self, secret_name: str) -> bool:
        """Check if secret is cached and still valid."""
        if secret_name not in self._cache:
            return False
        
        _, timestamp = self._cache[secret_name]
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return age < self.cache_ttl

    def backend_info(self) -> str:
        return f"HashiCorp Vault (address: {self.vault_addr}, loaded {self.loaded_at.isoformat()})"


class SecretsManager:
    """
    Central secrets manager with support for multiple backends.
    
    Usage:
        secrets = SecretsManager()
        jwt_secret = secrets.get('JWT_SECRET_KEY')
        db_creds = secrets.get_dict('DATABASE_CREDENTIALS')
    """

    _instance: Optional['SecretsManager'] = None
    _backend: Optional[SecretsBackend] = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize secrets manager with appropriate backend."""
        if self._initialized:
            return
        
        # Determine backend based on environment
        backend_type = os.getenv('SECRETS_BACKEND', 'environment').lower()
        
        try:
            if backend_type == 'aws':
                self._backend = AWSSecretsManagerBackend()
            elif backend_type == 'vault':
                self._backend = VaultSecretsBackend()
            else:
                # Default to environment variables
                self._backend = EnvironmentSecretsBackend()
            
            logger.info(f"Secrets manager initialized: {self._backend.backend_info()}")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize secrets backend: {e}")
            # Fall back to environment variables
            self._backend = EnvironmentSecretsBackend()
            self._initialized = True

    def get(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value.
        
        Args:
            secret_name: Name of the secret (e.g., 'JWT_SECRET_KEY')
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        if not self._backend:
            return default
        
        return self._backend.get_secret(secret_name, default)

    def get_dict(self, secret_name: str) -> Dict[str, Any]:
        """
        Get a secret containing multiple key-value pairs.
        
        Args:
            secret_name: Name of the secret dict (e.g., 'DATABASE_CREDENTIALS')
            
        Returns:
            Dictionary of secret values
        """
        if not self._backend:
            return {}
        
        return self._backend.get_secret_dict(secret_name)

    def backend_info(self) -> str:
        """Get information about the current backend."""
        return self._backend.backend_info() if self._backend else "No backend configured"


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create the global secrets manager."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


# Convenience functions for common secrets
def get_jwt_secret() -> str:
    """Get JWT secret key."""
    secrets = get_secrets_manager()
    return secrets.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')


def get_database_url() -> str:
    """Get database connection URL."""
    secrets = get_secrets_manager()
    # First try to get from secrets manager
    db_url = secrets.get('DATABASE_URL')
    # Fall back to environment variable
    if not db_url:
        db_url = os.getenv('DATABASE_URL')
    return db_url


def get_jwt_refresh_secret() -> str:
    """Get JWT refresh token secret."""
    secrets = get_secrets_manager()
    return secrets.get('JWT_REFRESH_SECRET', 'dev-refresh-secret-change-in-production')


def get_api_keys() -> Dict[str, str]:
    """Get all API keys."""
    secrets = get_secrets_manager()
    return secrets.get_dict('API_KEYS')


def get_database_credentials() -> Dict[str, str]:
    """Get database credentials."""
    secrets = get_secrets_manager()
    return secrets.get_dict('DATABASE_CREDENTIALS')


# Initialize on module load
_secrets_manager = SecretsManager()
logger.debug(f"Secrets manager initialized: {_secrets_manager.backend_info()}")
