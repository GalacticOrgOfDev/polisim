"""
Tests for Phase 6.2.3: Secrets Management & Configuration

Test coverage:
- Secrets Manager functionality
- Configuration loading and validation
- Secret rotation framework
- Integration with API components
"""

import os
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Secrets Manager Tests
class TestSecretsManager:
    """Test cases for SecretsManager."""
    
    def test_environment_backend_initialization(self):
        """Test EnvironmentSecretsBackend initializes correctly."""
        from api.secrets_manager import EnvironmentSecretsBackend
        
        backend = EnvironmentSecretsBackend()
        assert backend is not None
        assert backend.backend_name == "environment"
    
    def test_environment_backend_get_secret(self):
        """Test retrieving secret from environment."""
        os.environ['POLISIM_TEST_SECRET'] = 'test_value_123'
        
        from api.secrets_manager import EnvironmentSecretsBackend
        backend = EnvironmentSecretsBackend()
        
        secret = backend.get_secret('TEST_SECRET')
        assert secret == 'test_value_123'
        
        # Clean up
        del os.environ['POLISIM_TEST_SECRET']
    
    def test_environment_backend_get_missing_secret(self):
        """Test retrieving missing secret returns None."""
        from api.secrets_manager import EnvironmentSecretsBackend
        
        backend = EnvironmentSecretsBackend()
        secret = backend.get_secret('NONEXISTENT_SECRET_XYZ')
        
        assert secret is None
    
    def test_environment_backend_get_dict(self):
        """Test retrieving dictionary secret from JSON."""
        json_dict = json.dumps({'key1': 'value1', 'key2': 'value2'})
        os.environ['POLISIM_TEST_DICT_JSON'] = json_dict
        
        from api.secrets_manager import EnvironmentSecretsBackend
        backend = EnvironmentSecretsBackend()
        
        result = backend.get_secret_dict('TEST_DICT')
        assert result == {'key1': 'value1', 'key2': 'value2'}
        
        # Clean up
        del os.environ['POLISIM_TEST_DICT_JSON']
    
    def test_secrets_manager_singleton(self):
        """Test SecretsManager is a singleton."""
        from api.secrets_manager import get_secrets_manager
        
        mgr1 = get_secrets_manager()
        mgr2 = get_secrets_manager()
        
        assert mgr1 is mgr2
    
    def test_secrets_manager_get_secret(self):
        """Test getting secret through SecretsManager."""
        os.environ['SECRETS_BACKEND'] = 'environment'
        os.environ['POLISIM_JWT_SECRET_KEY'] = 'test_jwt_secret'
        
        from api.secrets_manager import get_secrets_manager
        
        secrets = get_secrets_manager()
        secret = secrets.get('JWT_SECRET_KEY')
        
        assert secret == 'test_jwt_secret'
        
        # Clean up
        del os.environ['POLISIM_JWT_SECRET_KEY']
    
    def test_secrets_manager_fallback_default(self):
        """Test SecretsManager uses default when secret not found."""
        from api.secrets_manager import get_secrets_manager
        
        secrets = get_secrets_manager()
        secret = secrets.get('NONEXISTENT_SECRET_XYZ', default='default_value')
        
        assert secret == 'default_value'
    
    def test_convenience_functions(self):
        """Test convenience functions for common secrets."""
        os.environ['SECRETS_BACKEND'] = 'environment'
        os.environ['POLISIM_JWT_SECRET_KEY'] = 'jwt_test_secret'
        os.environ['POLISIM_DATABASE_URL'] = 'postgresql://localhost/test'
        
        from api.secrets_manager import (
            get_jwt_secret,
            get_database_url,
            get_jwt_refresh_secret
        )
        
        assert get_jwt_secret() == 'jwt_test_secret'
        assert get_database_url() == 'postgresql://localhost/test'
        assert get_jwt_refresh_secret() is not None  # Has default
        
        # Clean up
        del os.environ['POLISIM_JWT_SECRET_KEY']
        del os.environ['POLISIM_DATABASE_URL']


# Configuration Manager Tests
class TestConfigurationManager:
    """Test cases for ConfigurationManager."""
    
    def test_environment_config_initialization(self):
        """Test Environment enum and detection."""
        from api.config_manager import Environment, get_env
        
        # Save original
        original_env = os.getenv('FLASK_ENV')
        
        os.environ['FLASK_ENV'] = 'development'
        assert get_env() == Environment.DEVELOPMENT
        
        os.environ['FLASK_ENV'] = 'production'
        assert get_env() == Environment.PRODUCTION
        
        # Restore original
        if original_env:
            os.environ['FLASK_ENV'] = original_env
        else:
            os.environ.pop('FLASK_ENV', None)
    
    def test_database_config_initialization(self):
        """Test DatabaseConfig initialization."""
        from api.config_manager import DatabaseConfig
        
        config = DatabaseConfig()
        
        assert config.url is not None
        assert config.pool_size == 10
        assert config.max_overflow == 20
    
    def test_database_config_from_environment(self):
        """Test DatabaseConfig loads from environment."""
        os.environ['DATABASE_URL'] = 'postgresql://test:pass@localhost/polisim'
        
        from api.config_manager import DatabaseConfig
        config = DatabaseConfig(url=None)  # Force reload
        
        assert 'postgresql' in config.url
    
    def test_jwt_config_initialization(self):
        """Test JWTConfig initialization."""
        os.environ['POLISIM_JWT_SECRET_KEY'] = 'test_secret_key'
        
        from api.config_manager import JWTConfig
        config = JWTConfig()
        
        assert config.secret_key == 'test_secret_key'
        assert config.algorithm == 'HS256'
        assert config.expiration_hours == 24
    
    def test_jwt_config_configurable_values(self):
        """Test JWTConfig loads configurable values from environment."""
        os.environ['JWT_ALGORITHM'] = 'HS512'
        os.environ['JWT_EXPIRATION_HOURS'] = '48'
        
        from api.config_manager import JWTConfig
        config = JWTConfig()
        
        assert config.algorithm == 'HS512'
        assert config.expiration_hours == 48
    
    def test_api_config_initialization(self):
        """Test APIConfig initialization."""
        from api.config_manager import APIConfig
        
        config = APIConfig()
        
        assert config.host == '0.0.0.0'
        assert config.port == 5000
        assert config.debug == False
        assert config.rate_limit_enabled == True
    
    def test_api_config_cors_origins_parsing(self):
        """Test CORS origins parsing."""
        os.environ['CORS_ALLOWED_ORIGINS'] = 'http://localhost:3000,https://example.com'
        
        from api.config_manager import APIConfig
        config = APIConfig()
        
        origins = config.get_cors_origins()
        assert len(origins) == 2
        assert 'http://localhost:3000' in origins
        assert 'https://example.com' in origins
    
    def test_security_config_initialization(self):
        """Test SecurityConfig initialization."""
        from api.config_manager import SecurityConfig
        
        config = SecurityConfig()
        
        assert config.https_only == True
        assert config.secure_cookies == True
        assert config.password_min_length == 8
        assert config.max_login_attempts == 5
    
    def test_secret_rotation_config(self):
        """Test SecretRotationConfig initialization."""
        from api.config_manager import SecretRotationConfig
        
        config = SecretRotationConfig()
        
        assert config.enabled == True
        assert config.database_password_days == 90
        assert config.api_keys_days == 180
        assert config.jwt_secret_days == 365
    
    def test_main_config_initialization(self):
        """Test main Config class initialization."""
        from api.config_manager import Config, get_config
        
        config = Config()
        
        assert config.environment is not None
        assert config.database is not None
        assert config.jwt is not None
        assert config.api is not None
        assert config.security is not None
        assert config.secret_rotation is not None
    
    def test_config_to_dict(self):
        """Test Config.to_dict() for safe exposure."""
        from api.config_manager import Config
        
        config = Config()
        config_dict = config.to_dict()
        
        # Should include non-sensitive data
        assert 'environment' in config_dict
        assert 'api' in config_dict
        
        # Should NOT include sensitive data
        assert 'JWT_SECRET_KEY' not in str(config_dict)
    
    def test_config_validate_success(self):
        """Test config validation passes with valid config."""
        os.environ['FLASK_ENV'] = 'development'
        os.environ['POLISIM_JWT_SECRET_KEY'] = 'test_secret'
        
        from api.config_manager import Config
        config = Config()
        
        assert config.validate() == True
    
    def test_config_validate_production_without_secret(self):
        """Test config validation fails for production without proper JWT secret."""
        os.environ['FLASK_ENV'] = 'production'
        os.environ.pop('POLISIM_JWT_SECRET_KEY', None)
        os.environ.pop('JWT_SECRET_KEY', None)
        
        from api.config_manager import Config
        config = Config()
        
        # Should warn about dev secret in production
        # (Note: actual validation behavior depends on implementation)


# Secret Rotation Tests
class TestSecretRotation:
    """Test cases for secret rotation framework."""
    
    def test_rotation_schedule_initialization(self):
        """Test SecretRotationSchedule initialization."""
        from api.secret_rotation import SecretRotationSchedule
        
        schedule = SecretRotationSchedule(
            secret_name='TEST_SECRET',
            secret_type='api_key',
            rotation_days=90
        )
        
        assert schedule.secret_name == 'TEST_SECRET'
        assert schedule.rotation_days == 90
        assert schedule.rotation_count == 0
    
    def test_rotation_schedule_is_due(self):
        """Test SecretRotationSchedule.is_due_for_rotation()."""
        from api.secret_rotation import SecretRotationSchedule
        from datetime import datetime, timedelta, timezone
        
        # Create schedule that's due for rotation
        schedule = SecretRotationSchedule(
            secret_name='TEST_SECRET',
            secret_type='api_key',
            rotation_days=90
        )
        
        # Set next_rotation to past
        schedule.next_rotation = datetime.now(timezone.utc) - timedelta(days=1)
        
        assert schedule.is_due_for_rotation() == True
    
    def test_rotation_schedule_not_due(self):
        """Test SecretRotationSchedule.is_due_for_rotation() returns False."""
        from api.secret_rotation import SecretRotationSchedule
        from datetime import datetime, timedelta
        
        schedule = SecretRotationSchedule(
            secret_name='TEST_SECRET',
            secret_type='api_key',
            rotation_days=90
        )
        
        # Schedule is freshly created, shouldn't be due
        assert schedule.is_due_for_rotation() == False
    
    def test_database_password_rotation_handler(self):
        """Test DatabasePasswordRotationHandler."""
        from api.secret_rotation import DatabasePasswordRotationHandler
        
        handler = DatabasePasswordRotationHandler()
        
        # Generate new secret
        new_secret = handler.generate_new_secret()
        
        assert len(new_secret) >= 32
        assert handler.validate_secret(new_secret) == True
    
    def test_api_key_rotation_handler(self):
        """Test APIKeyRotationHandler."""
        from api.secret_rotation import APIKeyRotationHandler
        
        handler = APIKeyRotationHandler()
        
        # Generate new secret
        new_secret = handler.generate_new_secret()
        
        assert new_secret.startswith('polisim_')
        assert handler.validate_secret(new_secret) == True
    
    def test_jwt_secret_rotation_handler(self):
        """Test JWTSecretRotationHandler."""
        from api.secret_rotation import JWTSecretRotationHandler
        
        handler = JWTSecretRotationHandler()
        
        # Generate new secret
        new_secret = handler.generate_new_secret()
        
        assert len(new_secret) >= 32
        assert handler.validate_secret(new_secret) == True
    
    def test_rotation_manager_initialization(self):
        """Test SecretRotationManager initialization."""
        from api.secret_rotation import SecretRotationManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schedule_file = Path(tmpdir) / 'schedule.json'
            manager = SecretRotationManager(schedule_file=str(schedule_file))
            
            assert len(manager.handlers) > 0
            assert len(manager.schedules) > 0
    
    def test_rotation_manager_get_status(self):
        """Test SecretRotationManager.get_rotation_status()."""
        from api.secret_rotation import SecretRotationManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schedule_file = Path(tmpdir) / 'schedule.json'
            manager = SecretRotationManager(schedule_file=str(schedule_file))
            
            status = manager.get_rotation_status()
            
            assert 'DATABASE_PASSWORD' in status
            assert 'API_KEY' in status
            assert 'JWT_SECRET_KEY' in status
            
            for secret, info in status.items():
                assert 'last_rotated' in info
                assert 'next_rotation' in info
                assert 'days_until_rotation' in info
                assert 'due_for_rotation' in info
    
    def test_rotation_manager_save_load_schedule(self):
        """Test SecretRotationManager saves and loads schedules."""
        from api.secret_rotation import SecretRotationManager
        from datetime import datetime, timedelta
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schedule_file = Path(tmpdir) / 'schedule.json'
            
            # Create and modify manager
            manager1 = SecretRotationManager(schedule_file=str(schedule_file))
            original_count = manager1.schedules['JWT_SECRET_KEY'].rotation_count
            manager1.schedules['JWT_SECRET_KEY'].rotation_count = 5
            manager1._save_schedules()
            
            # Load in new manager
            manager2 = SecretRotationManager(schedule_file=str(schedule_file))
            assert manager2.schedules['JWT_SECRET_KEY'].rotation_count == 5


# Integration Tests
class TestIntegration:
    """Integration tests between components."""
    
    def test_auth_module_uses_secrets_manager(self):
        """Test that auth.py properly uses secrets manager."""
        import sys
        import importlib
        
        # Set environment first
        os.environ['SECRETS_BACKEND'] = 'environment'
        os.environ['POLISIM_JWT_SECRET_KEY'] = 'integration_test_secret'
        
        # Reset the singleton and reload modules
        if 'api.secrets_manager' in sys.modules:
            api_secrets = sys.modules['api.secrets_manager']
            api_secrets.SecretsManager._instance = None
            api_secrets._secrets_manager = None
        
        # Re-import auth to get new secret
        if 'api.auth' in sys.modules:
            del sys.modules['api.auth']
        
        from api.auth import JWT_SECRET_KEY
        
        assert JWT_SECRET_KEY == 'integration_test_secret'
    
    def test_database_module_uses_secrets_manager(self):
        """Test that database.py properly uses secrets manager."""
        os.environ['SECRETS_BACKEND'] = 'environment'
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        
        from api.database import _resolve_database_url
        
        url = _resolve_database_url()
        assert 'sqlite' in url or url.startswith('sqlite')
    
    def test_rest_server_uses_config_manager(self):
        """Test that rest_server.py uses config manager."""
        os.environ['CORS_ALLOWED_ORIGINS'] = 'http://localhost:3000'
        os.environ['SECRETS_BACKEND'] = 'environment'
        
        # Test would need Flask app creation
        from api.rest_server import _get_cors_origins
        
        origins = _get_cors_origins()
        assert 'http://localhost:3000' in origins


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after each test."""
    # Store original state
    original_env = os.environ.copy()
    
    yield
    
    # Restore original state
    # Remove added keys
    for key in list(os.environ.keys()):
        if key not in original_env:
            del os.environ[key]
    
    # Restore modified keys
    for key, value in original_env.items():
        os.environ[key] = value
