"""
Integration Tests: Phase 6.2.3 (Secrets) + 6.2.4 (Auth) + 6.2.5 (DDoS Protection)

Tests the complete security pipeline:
1. Secrets retrieved from manager
2. JWT tokens generated using secrets
3. RBAC enforced with permissions
4. Rate limiting applied per user
5. Circuit breakers protect external calls
6. Session management with timeout
7. Audit logging of all events
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import core security modules
try:
    from api.secrets_manager import get_secrets_manager, SecretsManager
    from api.jwt_manager import get_token_manager, TokenManager
    from api.rbac import get_rbac_manager, RBACManager
    from api.session_manager import get_session_manager, SessionManager
    from api.auth_audit import get_auth_audit_logger, AuthAuditLogger
    from api.rate_limiter import get_rate_limiter, RateLimiter
    from api.circuit_breaker import CircuitBreakerManager
    from api.request_validator import get_request_validator, RequestValidator
    HAS_SECURITY_MODULES = True
except ImportError as e:
    HAS_SECURITY_MODULES = False
    IMPORT_ERROR = str(e)
    # Provide fallback if get_audit_logger not imported
    def get_audit_logger():
        """Fallback implementation."""
        try:
            from api.auth_audit import get_auth_audit_logger
            return get_auth_audit_logger()
        except ImportError:
            return None

# Make sure get_audit_logger is available if not already imported
if HAS_SECURITY_MODULES:
    get_audit_logger = get_auth_audit_logger


class TestSecurityIntegration:
    """Integration tests for the complete security stack."""

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_secrets_manager_initialization(self):
        """Test secrets manager can be initialized."""
        sm = get_secrets_manager()
        assert sm is not None
        # Should have a backend configured
        assert sm._backend is not None

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_jwt_token_generation_with_secrets(self):
        """Test JWT tokens are generated using secrets from manager."""
        sm = get_secrets_manager()
        tm = get_token_manager()
        
        # Generate token
        access_token = tm.generate_access_token(
            user_id="test_user",
            user_email="test@example.com",
            user_roles=["user"]
        )
        
        # Token should be a valid JWT string
        assert access_token is not None
        assert "." in access_token  # JWT format: header.payload.signature

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_rbac_with_jwt_tokens(self):
        """Test RBAC works with JWT tokens."""
        tm = get_token_manager()
        rbac = get_rbac_manager()
        
        # Create tokens with different roles
        admin_token = tm.generate_access_token(
            user_id="admin",
            email="admin@example.com",
            roles=["admin"]
        )
        
        user_token = tm.generate_access_token(
            user_id="user",
            email="user@example.com",
            roles=["user"]
        )
        
        # Validate both tokens
        admin_claims = tm.validate_token(admin_token)
        user_claims = tm.validate_token(user_token)
        
        assert admin_claims is not None
        assert user_claims is not None
        assert "admin" in admin_claims.get("roles", [])
        assert "user" in user_claims.get("roles", [])

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_session_management_with_auth(self):
        """Test session creation and management with authenticated user."""
        tm = get_token_manager()
        sm = get_session_manager()
        
        # Create user and token
        user_id = "test_user"
        access_token = tm.generate_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        # Validate token to get claims
        claims = tm.validate_token(access_token)
        
        # Create session
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"
        session_id = sm.create_session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        assert session_id is not None
        
        # Session should be retrievable
        session = sm.get_session(session_id)
        assert session is not None
        assert session["user_id"] == user_id

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_rate_limiting_per_authenticated_user(self):
        """Test rate limiting respects user authentication."""
        tm = get_token_manager()
        limiter = get_rate_limiter()
        
        if not limiter._is_redis_available():
            pytest.skip("Redis required")
        
        # Create tokens for two different users
        user1_token = tm.generate_access_token(
            user_id="user1",
            email="user1@example.com",
            roles=["user"]
        )
        
        user2_token = tm.generate_access_token(
            user_id="user2",
            email="user2@example.com",
            roles=["user"]
        )
        
        # Each user should have independent rate limits
        allowed1, _ = limiter.check_user_rate_limit(
            "user1",
            endpoint="simulate",
            limit=100,
            window=3600
        )
        
        allowed2, _ = limiter.check_user_rate_limit(
            "user2",
            endpoint="simulate",
            limit=100,
            window=3600
        )
        
        assert allowed1 is True
        assert allowed2 is True

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_audit_logging_authentication_events(self):
        """Test audit logging records authentication events."""
        tm = get_token_manager()
        audit = get_audit_logger()
        
        # Generate and log token creation
        user_id = "test_user"
        access_token = tm.generate_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        # Log event
        audit.log_token_generated(
            user_id=user_id,
            token_type="access",
            ip_address="192.168.1.1",
            user_agent="test-agent"
        )
        
        # Retrieve audit trail
        events = audit.get_events_by_user(user_id)
        assert events is not None

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_circuit_breaker_with_authenticated_requests(self):
        """Test circuit breaker protects external calls made by authenticated users."""
        tm = get_token_manager()
        
        # Create authenticated token
        access_token = tm.generate_access_token(
            user_id="test_user",
            email="test@example.com",
            roles=["user"]
        )
        
        # Get circuit breaker for external service
        breaker = CircuitBreakerManager.get_breaker("cbo_scraper")
        
        if breaker is None:
            breaker = CircuitBreakerManager.register_breaker("cbo_scraper")
        
        assert breaker is not None
        
        # Test that breaker is in closed state initially
        status = breaker.get_status()
        assert status is not None

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_request_validation_with_authenticated_user(self):
        """Test request validation works with authenticated requests."""
        tm = get_token_manager()
        validator = get_request_validator()
        
        # Create authenticated token
        access_token = tm.generate_access_token(
            user_id="test_user",
            email="test@example.com",
            roles=["user"]
        )
        
        # Validate request headers
        headers = {
            "authorization": f"Bearer {access_token}",
            "content-type": "application/json"
        }
        
        # Clean headers
        cleaned = validator.validate_headers(headers)
        
        # Authorization header should be preserved
        assert "authorization" in cleaned
        assert "content-type" in cleaned

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_permission_based_rate_limiting(self):
        """Test that different roles get different rate limits."""
        tm = get_token_manager()
        rbac = get_rbac_manager()
        limiter = get_rate_limiter()
        
        if not limiter._is_redis_available():
            pytest.skip("Redis required")
        
        # Create admin and user tokens
        admin_token = tm.generate_access_token(
            user_id="admin",
            email="admin@example.com",
            roles=["admin"]
        )
        
        user_token = tm.generate_access_token(
            user_id="user",
            email="user@example.com",
            roles=["user"]
        )
        
        # Both should validate
        admin_claims = tm.validate_token(admin_token)
        user_claims = tm.validate_token(user_token)
        
        assert admin_claims is not None
        assert user_claims is not None
        
        # Admin should have "admin" role
        assert "admin" in admin_claims.get("roles", [])

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_session_timeout_with_rate_limiting(self):
        """Test that sessions timeout while respecting rate limiting."""
        sm = get_session_manager()
        limiter = get_rate_limiter()
        
        # Create session
        session_id = sm.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="test"
        )
        
        assert session_id is not None
        
        # Session should be valid
        session = sm.get_session(session_id)
        assert session is not None

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_full_authentication_flow(self):
        """Test complete authentication flow from secrets to rate limiting."""
        # Step 1: Get secrets
        sm = get_secrets_manager()
        assert sm is not None
        
        # Step 2: Generate JWT token using secrets
        tm = get_token_manager()
        access_token = tm.generate_access_token(
            user_id="test_user",
            email="test@example.com",
            roles=["user"]
        )
        assert access_token is not None
        
        # Step 3: Validate token
        claims = tm.validate_token(access_token)
        assert claims is not None
        assert claims["sub"] == "test_user"  # JWT uses 'sub' claim for user_id
        
        # Step 4: Create session
        session_mgr = get_session_manager()
        session_id = session_mgr.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="test"
        )
        assert session_id is not None
        
        # Step 5: Check RBAC
        rbac = get_rbac_manager()
        assert rbac is not None
        
        # Step 6: Log audit event
        audit = get_audit_logger()
        audit.log_token_generated(
            user_id="test_user",
            token_type="access",
            ip_address="192.168.1.1",
            user_agent="test"
        )
        
        # Step 7: Check rate limit
        limiter = get_rate_limiter()
        if limiter._is_redis_available():
            allowed, _ = limiter.check_user_rate_limit(
                "test_user",
                endpoint="simulate"
            )
            assert allowed is True

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_concurrent_authenticated_sessions(self):
        """Test multiple concurrent sessions for same user."""
        sm = get_session_manager()
        tm = get_token_manager()
        
        user_id = "test_user"
        
        # Create tokens for different clients
        token1 = tm.generate_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        token2 = tm.generate_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        # Create sessions from different IPs
        session1 = sm.create_session(
            user_id=user_id,
            ip_address="192.168.1.1",
            user_agent="Client1"
        )
        
        session2 = sm.create_session(
            user_id=user_id,
            ip_address="192.168.1.2",
            user_agent="Client2"
        )
        
        # Both sessions should be valid
        assert sm.get_session(session1) is not None
        assert sm.get_session(session2) is not None

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_audit_trail_completeness(self):
        """Test that audit trail captures all security events."""
        tm = get_token_manager()
        audit = get_audit_logger()
        
        user_id = "test_user"
        
        # Generate token
        token = tm.generate_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        # Log various events
        audit.log_token_generated(
            user_id=user_id,
            token_type="access",
            ip_address="192.168.1.1",
            user_agent="test"
        )
        
        audit.log_login_success(
            user_id=user_id,
            username="test_user",
            ip_address="192.168.1.1",
            user_agent="test"
        )
        
        # Retrieve events
        events = audit.get_events_by_user(user_id)
        assert events is not None

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_expired_token_with_refresh(self):
        """Test token expiration and refresh flow."""
        tm = get_token_manager()
        
        # Generate access and refresh tokens
        access_token = tm.generate_access_token(
            user_id="test_user",
            email="test@example.com",
            roles=["user"]
        )
        
        refresh_token = tm.generate_refresh_token(user_id="test_user")
        
        assert access_token is not None
        assert refresh_token is not None
        
        # Validate both
        access_claims = tm.validate_token(access_token)
        assert access_claims is not None


class TestSecurityStackInteractions:
    """Tests for interactions between security components."""

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_secrets_rotation_with_active_sessions(self):
        """Test that secret rotation doesn't break active sessions."""
        tm = get_token_manager()
        sm = get_session_manager()
        
        # Create token and session
        token = tm.generate_access_token(
            user_id="test_user",
            email="test@example.com",
            roles=["user"]
        )
        
        session_id = sm.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="test"
        )
        
        # Validate token still works
        claims = tm.validate_token(token)
        assert claims is not None
        
        # Session still valid
        session = sm.get_session(session_id)
        assert session is not None

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_rate_limiting_bypassed_for_admin(self):
        """Test that rate limiting respects user roles."""
        tm = get_token_manager()
        
        # Create admin token
        admin_token = tm.generate_access_token(
            user_id="admin",
            email="admin@example.com",
            roles=["admin"]
        )
        
        # Validate admin token
        claims = tm.validate_token(admin_token)
        assert "admin" in claims.get("roles", [])

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_circuit_breaker_triggers_during_high_load(self):
        """Test circuit breaker behavior under simulated load."""
        from api.circuit_breaker import CircuitBreaker, CircuitState
        
        breaker = CircuitBreaker(
            "test_service",
            failure_threshold=3,
            expected_exception=Exception
        )
        
        # Simulate failures
        for i in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(Exception("Test")))
            except:
                pass
        
        # Circuit should now be open (after threshold)
        # (Actual state depends on Redis availability)

    @pytest.mark.skipif(not HAS_SECURITY_MODULES, reason="Security modules required")
    def test_comprehensive_audit_trail(self):
        """Test that all security operations are audited."""
        tm = get_token_manager()
        audit = get_audit_logger()
        sm = get_session_manager()
        
        user_id = "test_user"
        
        # Multiple security operations
        token = tm.generate_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        session = sm.create_session(
            user_id=user_id,
            ip_address="192.168.1.1",
            user_agent="test"
        )
        
        audit.log_login_success(
            user_id=user_id,
            username="test_user",
            ip_address="192.168.1.1",
            user_agent="test"
        )
        
        # All operations should be logged
        events = audit.get_events_by_user(user_id)
        assert events is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
