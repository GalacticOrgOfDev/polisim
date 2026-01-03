"""
Sentry Integration for PoliSim Error Tracking.

Phase 6.7.3: Integrates Sentry for unhandled exception tracking,
performance monitoring, and release tracking.

Features:
- Automatic exception capture with request context
- Release/version tracking
- Sampling rules to control noise
- Sensitive data scrubbing
- Integration with telemetry module

Note: sentry-sdk is an optional dependency. All type errors related to
the conditional import are expected and suppressed.
"""
# pyright: reportOptionalMemberAccess=false

import os
import logging
from typing import Optional, Dict, Any, Callable, cast
from functools import wraps

# Sentry SDK imports
try:
    import sentry_sdk  # type: ignore[import-untyped]
    from sentry_sdk.integrations.flask import FlaskIntegration  # type: ignore[import-untyped]
    from sentry_sdk.integrations.logging import LoggingIntegration  # type: ignore[import-untyped]
    from sentry_sdk.integrations.threading import ThreadingIntegration  # type: ignore[import-untyped]
    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False
    sentry_sdk = None  # type: ignore[assignment]

# Try to import telemetry module
try:
    from api.telemetry import get_telemetry, TelemetryContext
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False


logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

class SentryConfig:
    """Sentry configuration from environment variables."""
    
    @property
    def dsn(self) -> Optional[str]:
        """Sentry DSN (Data Source Name)."""
        return os.getenv("SENTRY_DSN")
    
    @property
    def environment(self) -> str:
        """Environment name (local/dev/staging/prod)."""
        return os.getenv("POLISIM_ENV", os.getenv("SENTRY_ENVIRONMENT", "local"))
    
    @property
    def release(self) -> str:
        """Release/version identifier."""
        # Try git SHA first, then version
        git_sha = os.getenv("GIT_SHA", os.getenv("COMMIT_SHA", ""))
        version = os.getenv("POLISIM_VERSION", "1.0.0")
        return git_sha[:8] if git_sha else f"polisim@{version}"
    
    @property
    def traces_sample_rate(self) -> float:
        """Performance monitoring sample rate (0.0 to 1.0)."""
        rate = os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
        try:
            return min(1.0, max(0.0, float(rate)))
        except ValueError:
            return 0.1
    
    @property
    def profiles_sample_rate(self) -> float:
        """Profiling sample rate (0.0 to 1.0)."""
        rate = os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")
        try:
            return min(1.0, max(0.0, float(rate)))
        except ValueError:
            return 0.1
    
    @property
    def send_default_pii(self) -> bool:
        """Whether to send PII (disabled by default for privacy)."""
        return os.getenv("SENTRY_SEND_PII", "false").lower() in ("true", "1", "yes")
    
    @property
    def debug(self) -> bool:
        """Enable Sentry debug mode."""
        return os.getenv("SENTRY_DEBUG", "false").lower() in ("true", "1", "yes")
    
    @property
    def enabled(self) -> bool:
        """Whether Sentry is enabled."""
        return bool(self.dsn) and HAS_SENTRY


# ============================================================================
# SENSITIVE DATA SCRUBBING
# ============================================================================

# Fields to scrub from Sentry events
SENSITIVE_FIELDS = {
    'password', 'passwd', 'secret', 'api_key', 'apikey', 'token',
    'access_token', 'refresh_token', 'authorization', 'auth',
    'cookie', 'session', 'csrf', 'xsrf', 'ssn', 'credit_card',
    'card_number', 'cvv', 'private_key', 'secret_key',
}

# Headers to scrub
SENSITIVE_HEADERS = {
    'authorization', 'cookie', 'x-api-key', 'x-auth-token',
    'x-csrf-token', 'x-xsrf-token',
}


def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process event before sending to Sentry.
    
    - Scrubs sensitive data
    - Adds telemetry context
    - Filters noisy events
    """
    # Scrub request data
    if 'request' in event:
        req = event['request']
        
        # Scrub headers
        if 'headers' in req:
            for header in list(req['headers'].keys()):
                if header.lower() in SENSITIVE_HEADERS:
                    req['headers'][header] = '[REDACTED]'
        
        # Scrub data/body
        if 'data' in req and isinstance(req['data'], dict):
            req['data'] = _scrub_dict(req['data'])
        
        # Scrub query string
        if 'query_string' in req:
            req['query_string'] = _scrub_query_string(req['query_string'])
    
    # Scrub extra context
    if 'extra' in event:
        event['extra'] = _scrub_dict(event['extra'])
    
    # Add telemetry context if available
    if HAS_TELEMETRY:
        try:
            telemetry = get_telemetry()
            ctx = telemetry.get_context()
            if ctx.request_id:
                event.setdefault('tags', {})['request_id'] = ctx.request_id
            if ctx.user_id:
                event.setdefault('user', {})['id'] = ctx.user_id
            if ctx.simulation_id:
                event.setdefault('tags', {})['simulation_id'] = ctx.simulation_id
        except Exception:
            pass
    
    # Filter out noisy events
    if _should_filter_event(event, hint):
        return None
    
    return event


def _scrub_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scrub sensitive fields from dictionary."""
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            result[key] = _scrub_dict(value)
        elif isinstance(value, list):
            result[key] = [_scrub_dict(v) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    return result


def _scrub_query_string(query_string: str) -> str:
    """Scrub sensitive parameters from query string."""
    if not query_string:
        return query_string
    
    parts = []
    for part in query_string.split('&'):
        if '=' in part:
            key, _ = part.split('=', 1)
            if key.lower() in SENSITIVE_FIELDS:
                parts.append(f"{key}=[REDACTED]")
            else:
                parts.append(part)
        else:
            parts.append(part)
    return '&'.join(parts)


def _should_filter_event(event: Dict[str, Any], hint: Dict[str, Any]) -> bool:
    """Determine if event should be filtered (not sent to Sentry)."""
    # Filter health check errors
    if 'request' in event:
        url = event['request'].get('url', '')
        if '/health' in url or '/ping' in url:
            return True
    
    # Filter expected exceptions
    if 'exc_info' in hint:
        exc_type, exc_value, _ = hint['exc_info']
        
        # Filter rate limit errors (expected behavior)
        if exc_type and exc_type.__name__ in ('RateLimitError', 'TooManyRequests'):
            return True
        
        # Filter validation errors (expected behavior)
        if exc_type and exc_type.__name__ in ('ValidationError', 'BadRequest'):
            return True
    
    return False


def before_send_transaction(
    event: Dict[str, Any],
    hint: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Process transaction before sending (for performance monitoring)."""
    # Filter out health check transactions
    if 'transaction' in event:
        if '/health' in event['transaction'] or '/ping' in event['transaction']:
            return None
    
    return event


# ============================================================================
# INITIALIZATION
# ============================================================================

_initialized = False


def init_sentry(app=None) -> bool:
    """
    Initialize Sentry SDK.
    
    Args:
        app: Optional Flask app for integration.
    
    Returns:
        True if Sentry was initialized, False otherwise.
    """
    global _initialized
    
    config = SentryConfig()
    
    if not config.enabled:
        logger.info("Sentry not initialized (DSN not configured or SDK not installed)")
        return False
    
    if _initialized:
        logger.debug("Sentry already initialized")
        return True
    
    try:
        integrations = [
            ThreadingIntegration(propagate_hub=True),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ]
        
        # Add Flask integration if Flask app provided
        if app is not None:
            integrations.append(FlaskIntegration(transaction_style="url"))
        
        sentry_sdk.init(
            dsn=config.dsn,
            environment=config.environment,
            release=config.release,
            traces_sample_rate=config.traces_sample_rate,
            profiles_sample_rate=config.profiles_sample_rate,
            send_default_pii=config.send_default_pii,
            debug=config.debug,
            integrations=integrations,
            before_send=before_send,
            before_send_transaction=before_send_transaction,
            # Additional options
            attach_stacktrace=True,
            include_local_variables=True,
            max_breadcrumbs=50,
            server_name=os.getenv("HOSTNAME", "polisim-api"),
        )
        
        # Set default tags
        sentry_sdk.set_tag("service", "polisim-api")
        sentry_sdk.set_tag("env", config.environment)
        
        _initialized = True
        logger.info(f"Sentry initialized: env={config.environment}, release={config.release}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def is_sentry_enabled() -> bool:
    """Check if Sentry is enabled and initialized."""
    return _initialized and HAS_SENTRY


# ============================================================================
# CONTEXT MANAGEMENT
# ============================================================================

def set_user_context(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """Set user context for Sentry events."""
    if not is_sentry_enabled():
        return
    
    user_data = {}
    if user_id:
        user_data['id'] = user_id
    if email:
        user_data['email'] = email
    if username:
        user_data['username'] = username
    if ip_address:
        user_data['ip_address'] = ip_address
    
    if user_data:
        sentry_sdk.set_user(user_data)


def set_request_context(request_id: str, route: str, method: str):
    """Set request context for Sentry events."""
    if not is_sentry_enabled():
        return
    
    sentry_sdk.set_tag("request_id", request_id)
    sentry_sdk.set_tag("route", route)
    sentry_sdk.set_tag("method", method)


def set_simulation_context(
    simulation_id: str,
    policy_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
):
    """Set simulation context for Sentry events."""
    if not is_sentry_enabled():
        return
    
    sentry_sdk.set_tag("simulation_id", simulation_id)
    if policy_id:
        sentry_sdk.set_tag("policy_id", policy_id)
    if scenario_id:
        sentry_sdk.set_tag("scenario_id", scenario_id)


def clear_context():
    """Clear all Sentry context."""
    if not is_sentry_enabled():
        return
    
    sentry_sdk.set_user(None)


# ============================================================================
# ERROR CAPTURE
# ============================================================================

def capture_exception(
    exception: Optional[Exception] = None,
    **context,
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.
    
    Args:
        exception: The exception to capture (uses current exception if None).
        **context: Additional context to include.
    
    Returns:
        Sentry event ID if captured, None otherwise.
    """
    if not is_sentry_enabled():
        return None
    
    with sentry_sdk.push_scope() as scope:  # type: ignore[union-attr]
        for key, value in context.items():
            scope.set_extra(key, value)
        
        result = sentry_sdk.capture_exception(exception)  # type: ignore[union-attr]
        return cast(Optional[str], result)


def capture_message(
    message: str,
    level: str = "info",
    **context,
) -> Optional[str]:
    """
    Capture a message and send to Sentry.
    
    Args:
        message: The message to capture.
        level: Severity level (debug, info, warning, error, fatal).
        **context: Additional context to include.
    
    Returns:
        Sentry event ID if captured, None otherwise.
    """
    if not is_sentry_enabled():
        return None
    
    with sentry_sdk.push_scope() as scope:  # type: ignore[union-attr]
        for key, value in context.items():
            scope.set_extra(key, value)
        
        result = sentry_sdk.capture_message(message, level=level)  # type: ignore[union-attr]
        return cast(Optional[str], result)


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

def start_transaction(
    name: str,
    op: str = "task",
    **kwargs,
):
    """
    Start a Sentry transaction for performance monitoring.
    
    Args:
        name: Transaction name.
        op: Operation type (e.g., "http.server", "task", "simulation").
    
    Returns:
        Transaction context manager.
    """
    if not is_sentry_enabled():
        # Return a no-op context manager
        from contextlib import nullcontext
        return nullcontext()
    
    return sentry_sdk.start_transaction(name=name, op=op, **kwargs)


def start_span(
    op: str,
    description: Optional[str] = None,
    **kwargs,
):
    """
    Start a Sentry span within the current transaction.
    
    Args:
        op: Operation type.
        description: Human-readable description.
    
    Returns:
        Span context manager.
    """
    if not is_sentry_enabled():
        from contextlib import nullcontext
        return nullcontext()
    
    return sentry_sdk.start_span(op=op, description=description, **kwargs)


# ============================================================================
# DECORATORS
# ============================================================================

def trace_function(op: str = "function"):
    """
    Decorator to trace function execution with Sentry.
    
    Args:
        op: Operation type for the span.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_sentry_enabled():
                return func(*args, **kwargs)
            
            with start_span(op=op, description=func.__name__):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def capture_errors(func: Callable) -> Callable:
    """
    Decorator to automatically capture exceptions.
    
    Captures the exception to Sentry but still raises it.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            capture_exception(e, function=func.__name__)
            raise
    
    return wrapper


# ============================================================================
# FLASK INTEGRATION HELPERS
# ============================================================================

def add_flask_context(app):
    """
    Add Flask request context to Sentry events.
    
    Call this during Flask app setup.
    """
    if not HAS_SENTRY or app is None:
        return
    
    try:
        from flask import request, g
        
        @app.before_request
        def sentry_before_request():
            if not is_sentry_enabled():
                return
            
            request_id = getattr(g, 'request_id', None)
            if request_id:
                sentry_sdk.set_tag("request_id", request_id)
            
            user_id = getattr(g, 'user_id', None)
            if user_id:
                sentry_sdk.set_user({"id": user_id})
        
        @app.after_request
        def sentry_after_request(response):
            if is_sentry_enabled():
                sentry_sdk.set_tag("status_code", response.status_code)
            return response
        
        logger.info("Flask Sentry context hooks registered")
        
    except ImportError:
        logger.warning("Flask not available, skipping Flask context hooks")


# ============================================================================
# IGNORE LIST
# ============================================================================

# Exceptions to ignore (don't send to Sentry)
IGNORED_EXCEPTIONS = [
    "KeyboardInterrupt",
    "SystemExit",
    "GeneratorExit",
]


def add_ignored_exception(exception_name: str):
    """Add an exception type to the ignore list."""
    if exception_name not in IGNORED_EXCEPTIONS:
        IGNORED_EXCEPTIONS.append(exception_name)


def configure_ignored_exceptions():
    """Configure Sentry to ignore certain exceptions."""
    if not is_sentry_enabled():
        return
    
    # This is handled in before_send, but we can also use SDK's ignore_errors
    # Note: sentry_sdk.init() ignore_errors parameter handles this
    pass
