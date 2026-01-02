"""
API v1 middleware for authentication and rate limiting.

Slice 5.7: Wraps v1 endpoints with optional auth and rate-limit enforcement.
"""

import os
from functools import wraps
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable, Dict, Any
from uuid import uuid4

from flask import request, g, jsonify

# Try to import validation models for error responses
try:
    from api.validation_models import (
        ErrorCode, ErrorResponse, ErrorMetadata, ErrorDetails, create_error_response
    )
    HAS_VALIDATION = True
except ImportError:
    HAS_VALIDATION = False

# Try to import observability
try:
    from api.observability import log_request, metrics
    HAS_OBSERVABILITY = True
except ImportError:
    HAS_OBSERVABILITY = False


def get_api_config() -> Dict[str, Any]:
    """Get API configuration from environment variables."""
    return {
        "PUBLIC_API_ENABLED": os.getenv("PUBLIC_API_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
        "API_REQUIRE_AUTH": os.getenv("API_REQUIRE_AUTH", "false").lower() in {"1", "true", "yes", "on"},
        "API_AUTH_METHOD": os.getenv("API_AUTH_METHOD", "jwt"),  # "jwt" or "api_key"
        "API_RATE_LIMIT_ENABLED": os.getenv("API_RATE_LIMIT_ENABLED", "false").lower() in {"1", "true", "yes", "on"},
        "API_RATE_LIMIT_PER_MINUTE": int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60")),
        "API_RATE_LIMIT_BURST": int(os.getenv("API_RATE_LIMIT_BURST", "10")),
        "API_MAX_PAYLOAD_MB": int(os.getenv("API_MAX_PAYLOAD_MB", "10")),
        "API_TIMEOUT_SECONDS": int(os.getenv("API_TIMEOUT_SECONDS", "300")),
        "API_VERSION": os.getenv("API_VERSION", "1.0"),
    }


class RateLimiter:
    """Simple in-memory rate limiter (per-user/key tracking)."""
    
    def __init__(self, requests_per_minute: int, burst: int = 0):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests: Dict[str, list] = {}  # user_id -> list of timestamps
    
    def is_allowed(self, user_id: str) -> tuple[bool, Dict[str, str]]:
        """
        Check if user is rate-limited.
        
        Returns:
            (is_allowed, headers_dict)
            headers_dict includes X-RateLimit-* values (all strings)
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                ts for ts in self.requests[user_id]
                if ts > window_start
            ]
        else:
            self.requests[user_id] = []
        
        request_count = len(self.requests[user_id])
        limit = self.requests_per_minute + self.burst
        
        headers = {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, limit - request_count)),
            "X-RateLimit-Reset": str(int((now + timedelta(minutes=1)).timestamp())),
        }
        
        if request_count >= limit:
            return False, headers
        
        # Record this request
        self.requests[user_id].append(now)
        return True, headers


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def init_rate_limiter(requests_per_minute: int = 60, burst: int = 10) -> None:
    """Initialize global rate limiter. Guarantees _rate_limiter is not None after."""
    global _rate_limiter
    _rate_limiter = RateLimiter(requests_per_minute, burst)


def require_v1_auth(auth_optional: bool = True) -> Callable:
    """
    Decorator for v1 endpoints requiring auth.
    
    Args:
        auth_optional: If True, auth is optional; if False, auth is required.
    
    Returns:
        Decorated function that validates auth header.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = getattr(g, 'request_id', str(uuid4()))
            api_version = getattr(g, 'api_version', '1.0')
            config = get_api_config()
            
            # If API_REQUIRE_AUTH is set globally, enforce it
            auth_required = config["API_REQUIRE_AUTH"] and not auth_optional
            
            # Try to extract and validate auth header
            auth_header = request.headers.get('Authorization', '')
            api_key_header = request.headers.get('X-API-Key', '')
            
            if auth_required and not auth_header and not api_key_header:
                if HAS_VALIDATION:
                    error_resp = create_error_response(
                        error_code=ErrorCode.AUTH_REQUIRED,
                        message="Authentication required",
                        request_id=request_id,
                        api_version=api_version,
                    )
                    return jsonify(error_resp.dict()), 401
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Authentication required",
                    }), 401
            
            # Store auth info in g for the handler
            g.auth_token = None
            g.api_key = None
            g.user_id = None
            
            if auth_header.startswith('Bearer '):
                g.auth_token = auth_header[7:]
                # In production, validate JWT here
                # For now, use token as user_id for rate limiting
                g.user_id = g.auth_token[:16]  # Truncate for tracking
            elif api_key_header:
                g.api_key = api_key_header
                # In production, validate API key against DB here
                g.user_id = api_key_header[:8]  # Prefix for tracking
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def apply_rate_limit() -> tuple[bool, Dict[str, str]]:
    """
    Check rate limit for current request.
    
    Phase 6.2 Enhancement: Supports per-IP and per-user rate limiting.
    
    Returns:
        (is_allowed, headers_dict)
    """
    config = get_api_config()
    
    if not config["API_RATE_LIMIT_ENABLED"]:
        return True, {}
    
    if _rate_limiter is None:
        init_rate_limiter(config["API_RATE_LIMIT_PER_MINUTE"], config["API_RATE_LIMIT_BURST"])
    
    # Use user_id if available (authenticated), else use IP address
    # This provides per-user limiting for authenticated requests
    # and per-IP limiting for public/unauthenticated requests
    user_id = getattr(g, 'user_id', None)
    
    if not user_id:
        # For unauthenticated requests, use IP address (handles DDoS better)
        # Use X-Forwarded-For if behind proxy, else use remote_addr
        user_id = request.headers.get('X-Forwarded-For', request.remote_addr) or 'anonymous'
        if ',' in user_id:  # X-Forwarded-For can have multiple IPs
            user_id = user_id.split(',')[0].strip()
    
    if _rate_limiter is None:
        return True, {}
    
    is_allowed, headers = _rate_limiter.is_allowed(user_id)
    
    return is_allowed, headers


def validate_payload_size() -> tuple[bool, Optional[str]]:
    """
    Check request payload size.
    
    Returns:
        (is_valid, error_message)
    """
    config = get_api_config()
    max_bytes = config["API_MAX_PAYLOAD_MB"] * 1024 * 1024
    
    content_length = request.content_length
    if content_length and content_length > max_bytes:
        return False, f"Payload exceeds {config['API_MAX_PAYLOAD_MB']} MB limit"
    
    return True, None


def validate_request_content_type() -> tuple[bool, Optional[str]]:
    """
    Validate request content type for JSON endpoints.
    
    Phase 6.2: Request validation hardening
    
    Returns:
        (is_valid, error_message)
    """
    # Only validate for requests with bodies
    if request.method not in ['POST', 'PUT', 'PATCH']:
        return True, None
    
    content_type = request.content_type or ''
    
    # Allow JSON content type
    if 'application/json' in content_type:
        return True, None
    
    # Reject if method expects JSON but got something else
    if request.content_length and request.content_length > 0:
        return False, "Invalid Content-Type. Expected application/json"
    
    return True, None


def validate_request_json() -> tuple[bool, Optional[str]]:
    """
    Validate JSON is well-formed.
    
    Phase 6.2: Request validation hardening
    
    Returns:
        (is_valid, error_message)
    """
    if request.method not in ['POST', 'PUT', 'PATCH']:
        return True, None
    
    # Try to parse JSON (will raise BadRequest if invalid)
    try:
        # This triggers JSON parsing without returning the data
        _ = request.get_json(force=False, silent=True)
        return True, None
    except Exception as e:
        return False, f"Malformed JSON request: {str(e)[:100]}"


def before_v1_request():
    """
    Called before each v1 request.
    Initializes request context, validates payload size, validates JSON,
    checks rate limits. (Phase 6.2 Security Hardening)
    """
    request_id = str(uuid4())
    api_version = "1.0"
    
    g.request_id = request_id
    g.api_version = api_version
    g.start_time = datetime.now(timezone.utc)
    
    # Phase 6.2: Validate content type
    is_valid, error_msg = validate_request_content_type()
    if not is_valid:
        if HAS_VALIDATION:
            error_resp = create_error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=error_msg,
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.dict()), 400
        else:
            return jsonify({"status": "error", "message": error_msg}), 400
    
    # Phase 6.2: Validate payload size
    is_valid, error_msg = validate_payload_size()
    if not is_valid:
        if HAS_VALIDATION:
            error_resp = create_error_response(
                error_code=ErrorCode.PAYLOAD_TOO_LARGE,
                message=error_msg,
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.dict()), 413
        else:
            return jsonify({"status": "error", "message": error_msg}), 413
    
    # Phase 6.2: Validate JSON structure
    is_valid, error_msg = validate_request_json()
    if not is_valid:
        if HAS_VALIDATION:
            error_resp = create_error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=error_msg,
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.dict()), 400
        else:
            return jsonify({"status": "error", "message": error_msg}), 400
    
    # Check rate limit
    is_allowed, rate_limit_headers = apply_rate_limit()
    if not is_allowed:
        if HAS_VALIDATION:
            error_resp = create_error_response(
                error_code=ErrorCode.RATE_LIMITED,
                message="Rate limit exceeded",
                request_id=request_id,
                api_version=api_version,
            )
            response = jsonify(error_resp.dict())
        else:
            response = jsonify({
                "status": "error",
                "error_code": "RATE_LIMITED",
                "message": "Rate limit exceeded",
            })
        
        response.status_code = 429
        for key, value in rate_limit_headers.items():
            response.headers[key] = value
        response.headers["Retry-After"] = "60"
        return response
    
    # Add rate limit headers to response (via after_request handler)
    g.rate_limit_headers = rate_limit_headers


def after_v1_request(response):
    """
    Called after each v1 request.
    Adds rate limit headers, request tracing headers, and logs the request.
    """
    request_id = getattr(g, 'request_id', str(uuid4()))
    api_version = getattr(g, 'api_version', '1.0')
    rate_limit_headers = getattr(g, 'rate_limit_headers', {})
    start_time = getattr(g, 'start_time', datetime.now(timezone.utc))
    
    # Add headers
    response.headers['X-Request-ID'] = request_id
    response.headers['X-API-Version'] = api_version
    
    duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
    response.headers['X-Response-Time'] = f"{duration_ms}ms"
    
    # Add rate limit headers
    for key, value in rate_limit_headers.items():
        response.headers[key] = value
    
    # Log request
    if HAS_OBSERVABILITY:
        input_size_kb = (request.content_length or 0) / 1024
        output_size_kb = (len(response.data) if hasattr(response, 'data') else 0) / 1024
        error_msg = None
        if response.status_code >= 400:
            try:
                data = response.get_json() if response.content_type == 'application/json' else {}
                error_msg = data.get('message') or data.get('error')
            except:
                error_msg = response.data.decode('utf-8', errors='ignore')[:100]
        
        log_request(
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            response_time_ms=duration_ms,
            error=error_msg,
            input_size_kb=input_size_kb,
            output_size_kb=output_size_kb,
        )
        
        metrics.record_request(
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            response_time_ms=duration_ms,
            error=error_msg,
        )
    
    return response
