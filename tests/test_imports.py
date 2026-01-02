#!/usr/bin/env python
"""Quick test of security module imports"""

import sys
sys.path.insert(0, '.')

try:
    from api.secrets_manager import get_secrets_manager, SecretsManager
    print("✓ secrets_manager")
    from api.jwt_manager import get_token_manager, TokenManager
    print("✓ jwt_manager")
    from api.rbac import get_rbac_manager, RBACManager
    print("✓ rbac")
    from api.session_manager import get_session_manager, SessionManager
    print("✓ session_manager")
    from api.auth_audit import get_auth_audit_logger, AuthAuditLogger
    print("✓ auth_audit")
    from api.rate_limiter import get_rate_limiter, RateLimiter
    print("✓ rate_limiter")
    from api.circuit_breaker import CircuitBreakerManager
    print("✓ circuit_breaker")
    from api.request_validator import get_request_validator, RequestValidator
    print("✓ request_validator")
    print("\nAll imports successful! HAS_SECURITY_MODULES should be True")
except ImportError as e:
    print(f"✗ ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Exception: {type(e).__name__}: {e}")
    sys.exit(1)
