"""
Telemetry Contract & Event Taxonomy for PoliSim API.

Phase 6.7.1: Defines required telemetry fields, event taxonomy,
and centralized telemetry management for the entire application.

This module serves as the single source of truth for:
- Required telemetry fields (logs + metrics tags)
- Event taxonomy (what gets logged/metric'd)
- Correlation ID propagation
- Domain context fields
"""

import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from contextlib import contextmanager
from functools import wraps


# ============================================================================
# TELEMETRY CONTRACT - Required Fields
# ============================================================================

class Environment(str, Enum):
    """Deployment environment identifiers."""
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    
    @classmethod
    def current(cls) -> "Environment":
        """Get current environment from env var."""
        env = os.getenv("POLISIM_ENV", os.getenv("ENV", "local")).lower()
        try:
            return cls(env)
        except ValueError:
            return cls.LOCAL


@dataclass
class TelemetryContext:
    """
    Required telemetry fields for all logged events.
    
    Phase 6.7.1 Contract:
    - env: local/dev/staging/prod
    - request_id: UUID, propagated from inbound X-Request-ID header if present
    - user_id: Authenticated user ID (never log secrets)
    - api_key_id: API key identifier (first 8 chars only, never full key)
    - route: API endpoint path
    - method: HTTP method
    - status: Response status code
    - latency_ms: Request duration in milliseconds
    - policy_id: Policy identifier (when applicable)
    - scenario_id: Scenario identifier (when applicable)
    """
    # Environment context
    env: str = field(default_factory=lambda: Environment.current().value)
    service: str = "polisim-api"
    version: str = field(default_factory=lambda: os.getenv("POLISIM_VERSION", "1.0.0"))
    
    # Request correlation
    request_id: Optional[str] = None
    trace_id: Optional[str] = None  # For distributed tracing
    span_id: Optional[str] = None   # For distributed tracing
    
    # Actor context (NEVER log secrets)
    user_id: Optional[str] = None
    api_key_id: Optional[str] = None  # First 8 chars only
    session_id: Optional[str] = None
    
    # Request/Response context
    route: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: Optional[int] = None
    input_size_bytes: Optional[int] = None
    output_size_bytes: Optional[int] = None
    
    # Domain context
    policy_id: Optional[str] = None
    scenario_id: Optional[str] = None
    simulation_id: Optional[str] = None
    extraction_id: Optional[str] = None
    
    # Additional metadata
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, dict) and not value:
                    continue
                result[key] = value
        return result
    
    def with_request(self, request_id: str, route: str, method: str) -> "TelemetryContext":
        """Create copy with request context."""
        ctx = TelemetryContext(**asdict(self))
        ctx.request_id = request_id
        ctx.route = route
        ctx.method = method
        return ctx


# ============================================================================
# EVENT TAXONOMY - What Gets Logged/Metric'd
# ============================================================================

class EventCategory(str, Enum):
    """High-level event categories."""
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    CIRCUIT_BREAKER = "circuit_breaker"
    SIMULATION = "simulation"
    EXTRACTION = "extraction"
    API = "api"
    SECURITY = "security"
    SYSTEM = "system"
    AUDIT = "audit"


class AuthEvent(str, Enum):
    """Authentication/authorization event types."""
    LOGIN_SUCCESS = "auth.login_success"
    LOGIN_FAILURE = "auth.login_failure"
    LOGOUT = "auth.logout"
    TOKEN_ISSUED = "auth.token_issued"
    TOKEN_REFRESHED = "auth.token_refreshed"
    TOKEN_REVOKED = "auth.token_revoked"
    TOKEN_EXPIRED = "auth.token_expired"
    TOKEN_INVALID = "auth.token_invalid"
    API_KEY_CREATED = "auth.api_key_created"
    API_KEY_REVOKED = "auth.api_key_revoked"
    API_KEY_USED = "auth.api_key_used"
    API_KEY_INVALID = "auth.api_key_invalid"
    PERMISSION_DENIED = "auth.permission_denied"
    MFA_CHALLENGE = "auth.mfa_challenge"
    MFA_SUCCESS = "auth.mfa_success"
    MFA_FAILURE = "auth.mfa_failure"


class RateLimitEvent(str, Enum):
    """Rate limiting event types."""
    LIMIT_CHECKED = "rate_limit.checked"
    LIMIT_EXCEEDED = "rate_limit.exceeded"
    LIMIT_WARNING = "rate_limit.warning"  # Approaching limit
    IP_BLOCKED = "rate_limit.ip_blocked"
    IP_UNBLOCKED = "rate_limit.ip_unblocked"


class CircuitBreakerEvent(str, Enum):
    """Circuit breaker event types."""
    OPENED = "circuit_breaker.opened"
    CLOSED = "circuit_breaker.closed"
    HALF_OPEN = "circuit_breaker.half_open"
    CALL_BLOCKED = "circuit_breaker.call_blocked"
    FAILURE_RECORDED = "circuit_breaker.failure_recorded"


class SimulationEvent(str, Enum):
    """Simulation lifecycle event types."""
    QUEUED = "simulation.queued"
    STARTED = "simulation.started"
    PROGRESS = "simulation.progress"
    COMPLETED = "simulation.completed"
    FAILED = "simulation.failed"
    CANCELLED = "simulation.cancelled"
    TIMEOUT = "simulation.timeout"
    VALIDATION_ERROR = "simulation.validation_error"


class ExtractionEvent(str, Enum):
    """Policy extraction lifecycle event types."""
    INGESTED = "extraction.ingested"
    PARSING_STARTED = "extraction.parsing_started"
    PARSING_COMPLETED = "extraction.parsing_completed"
    PARSING_FAILED = "extraction.parsing_failed"
    VALIDATION_STARTED = "extraction.validation_started"
    VALIDATION_COMPLETED = "extraction.validation_completed"
    VALIDATION_FAILED = "extraction.validation_failed"
    OUTPUT_GENERATED = "extraction.output_generated"


class APIEvent(str, Enum):
    """API request/response event types."""
    REQUEST_RECEIVED = "api.request_received"
    REQUEST_COMPLETED = "api.request_completed"
    REQUEST_FAILED = "api.request_failed"
    VALIDATION_ERROR = "api.validation_error"
    PAYLOAD_TOO_LARGE = "api.payload_too_large"
    TIMEOUT = "api.timeout"


class SecurityEvent(str, Enum):
    """Security-related event types."""
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    BRUTE_FORCE_DETECTED = "security.brute_force_detected"
    INJECTION_ATTEMPT = "security.injection_attempt"
    INVALID_INPUT = "security.invalid_input"
    CORS_VIOLATION = "security.cors_violation"
    CERT_EXPIRING = "security.cert_expiring"
    SECRET_ACCESSED = "security.secret_accessed"
    CONFIG_CHANGED = "security.config_changed"


class SystemEvent(str, Enum):
    """System-level event types."""
    STARTUP = "system.startup"
    SHUTDOWN = "system.shutdown"
    HEALTH_CHECK = "system.health_check"
    HEALTH_DEGRADED = "system.health_degraded"
    HEALTH_RESTORED = "system.health_restored"
    ERROR = "system.error"
    WARNING = "system.warning"
    DB_CONNECTION_ERROR = "system.db_connection_error"
    CACHE_MISS = "system.cache_miss"
    CACHE_HIT = "system.cache_hit"


# ============================================================================
# TELEMETRY EMITTER
# ============================================================================

class TelemetryEmitter:
    """
    Central telemetry emitter for structured logging and metrics.
    
    Ensures consistent telemetry format across all components.
    """
    
    def __init__(
        self,
        service_name: str = "polisim-api",
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True,
    ):
        self.service_name = service_name
        self.env = Environment.current()
        self.version = os.getenv("POLISIM_VERSION", "1.0.0")
        self._context_stack: List[TelemetryContext] = []
        
        # Configure logger
        self.logger = logging.getLogger(f"polisim.telemetry.{service_name}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []  # Clear existing handlers
        
        formatter = _JSONFormatter()
        
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        if enable_file and log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def get_context(self) -> TelemetryContext:
        """Get current telemetry context."""
        if self._context_stack:
            return self._context_stack[-1]
        return TelemetryContext(service=self.service_name)
    
    @contextmanager
    def context(self, ctx: TelemetryContext):
        """Context manager for scoped telemetry context."""
        self._context_stack.append(ctx)
        try:
            yield ctx
        finally:
            self._context_stack.pop()
    
    def emit(
        self,
        event: str,
        level: int = logging.INFO,
        message: Optional[str] = None,
        context: Optional[TelemetryContext] = None,
        **extra_fields,
    ):
        """
        Emit a telemetry event.
        
        Args:
            event: Event type from taxonomy (e.g., "auth.login_success")
            level: Logging level
            message: Human-readable message
            context: Optional telemetry context (uses current if not provided)
            **extra_fields: Additional fields to include
        """
        ctx = context or self.get_context()
        
        record = logging.LogRecord(
            name=self.logger.name,
            level=level,
            pathname="",
            lineno=0,
            msg=message or event,
            args=(),
            exc_info=None,
        )
        
        # Add telemetry context
        record.telemetry_context = ctx.to_dict()
        record.event = event
        record.event_category = event.split(".")[0] if "." in event else "unknown"
        
        # Add extra fields
        for key, value in extra_fields.items():
            setattr(record, key, value)
        
        self.logger.handle(record)
    
    # Convenience methods for each event category
    def auth_event(self, event: AuthEvent, success: bool = True, **kwargs):
        """Emit authentication event."""
        level = logging.INFO if success else logging.WARNING
        self.emit(event.value, level=level, success=success, **kwargs)
    
    def rate_limit_event(self, event: RateLimitEvent, **kwargs):
        """Emit rate limit event."""
        level = logging.WARNING if event == RateLimitEvent.LIMIT_EXCEEDED else logging.INFO
        self.emit(event.value, level=level, **kwargs)
    
    def circuit_breaker_event(self, event: CircuitBreakerEvent, **kwargs):
        """Emit circuit breaker event."""
        level = logging.WARNING if event in (
            CircuitBreakerEvent.OPENED, CircuitBreakerEvent.CALL_BLOCKED
        ) else logging.INFO
        self.emit(event.value, level=level, **kwargs)
    
    def simulation_event(self, event: SimulationEvent, **kwargs):
        """Emit simulation lifecycle event."""
        if event in (SimulationEvent.FAILED, SimulationEvent.TIMEOUT):
            level = logging.ERROR
        elif event == SimulationEvent.VALIDATION_ERROR:
            level = logging.WARNING
        else:
            level = logging.INFO
        self.emit(event.value, level=level, **kwargs)
    
    def extraction_event(self, event: ExtractionEvent, **kwargs):
        """Emit extraction lifecycle event."""
        if event in (ExtractionEvent.PARSING_FAILED, ExtractionEvent.VALIDATION_FAILED):
            level = logging.ERROR
        else:
            level = logging.INFO
        self.emit(event.value, level=level, **kwargs)
    
    def api_event(self, event: APIEvent, **kwargs):
        """Emit API event."""
        if event == APIEvent.REQUEST_FAILED:
            level = logging.ERROR
        elif event in (APIEvent.VALIDATION_ERROR, APIEvent.PAYLOAD_TOO_LARGE, APIEvent.TIMEOUT):
            level = logging.WARNING
        else:
            level = logging.INFO
        self.emit(event.value, level=level, **kwargs)
    
    def security_event(self, event: SecurityEvent, **kwargs):
        """Emit security event."""
        level = logging.WARNING if event in (
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            SecurityEvent.BRUTE_FORCE_DETECTED,
            SecurityEvent.INJECTION_ATTEMPT,
        ) else logging.INFO
        self.emit(event.value, level=level, **kwargs)
    
    def system_event(self, event: SystemEvent, **kwargs):
        """Emit system event."""
        if event == SystemEvent.ERROR:
            level = logging.ERROR
        elif event in (SystemEvent.WARNING, SystemEvent.HEALTH_DEGRADED, SystemEvent.DB_CONNECTION_ERROR):
            level = logging.WARNING
        else:
            level = logging.INFO
        self.emit(event.value, level=level, **kwargs)


class _JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 'authorization',
        'cookie', 'session', 'credential', 'private_key', 'access_key',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add event info
        if hasattr(record, 'event'):
            log_data['event'] = record.event
        if hasattr(record, 'event_category'):
            log_data['event_category'] = record.event_category
        
        # Add telemetry context
        if hasattr(record, 'telemetry_context'):
            log_data.update(record.telemetry_context)
        
        # Add extra fields (excluding standard LogRecord attributes)
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'taskName', 'telemetry_context', 'event', 'event_category',
            'message',
        }
        
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                # Sanitize sensitive fields
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    log_data[key] = "[REDACTED]"
                else:
                    log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


# ============================================================================
# GLOBAL TELEMETRY INSTANCE
# ============================================================================

# Global telemetry emitter (configured on first access)
_telemetry: Optional[TelemetryEmitter] = None


def get_telemetry() -> TelemetryEmitter:
    """Get or create global telemetry emitter."""
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryEmitter(
            service_name="polisim-api",
            log_file="logs/telemetry.log",
            enable_console=True,
            enable_file=True,
        )
    return _telemetry


def configure_telemetry(
    service_name: str = "polisim-api",
    log_file: Optional[str] = "logs/telemetry.log",
    enable_console: bool = True,
    enable_file: bool = True,
) -> TelemetryEmitter:
    """Configure and return global telemetry emitter."""
    global _telemetry
    _telemetry = TelemetryEmitter(
        service_name=service_name,
        log_file=log_file,
        enable_console=enable_console,
        enable_file=enable_file,
    )
    return _telemetry


# ============================================================================
# DECORATORS FOR TELEMETRY
# ============================================================================

def trace_simulation(simulation_id_param: str = "simulation_id"):
    """
    Decorator to trace simulation lifecycle.
    
    Usage:
        @trace_simulation()
        def run_simulation(simulation_id: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            telemetry = get_telemetry()
            simulation_id = kwargs.get(simulation_id_param) or str(uuid.uuid4())
            
            ctx = telemetry.get_context()
            ctx.simulation_id = simulation_id
            
            with telemetry.context(ctx):
                telemetry.simulation_event(SimulationEvent.STARTED, simulation_id=simulation_id)
                try:
                    result = func(*args, **kwargs)
                    telemetry.simulation_event(SimulationEvent.COMPLETED, simulation_id=simulation_id)
                    return result
                except Exception as e:
                    telemetry.simulation_event(
                        SimulationEvent.FAILED,
                        simulation_id=simulation_id,
                        error=str(e),
                    )
                    raise
        return wrapper
    return decorator


def trace_extraction(extraction_id_param: str = "extraction_id"):
    """
    Decorator to trace extraction lifecycle.
    
    Usage:
        @trace_extraction()
        def extract_policy(extraction_id: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            telemetry = get_telemetry()
            extraction_id = kwargs.get(extraction_id_param) or str(uuid.uuid4())
            
            ctx = telemetry.get_context()
            ctx.extraction_id = extraction_id
            
            with telemetry.context(ctx):
                telemetry.extraction_event(ExtractionEvent.INGESTED, extraction_id=extraction_id)
                try:
                    result = func(*args, **kwargs)
                    telemetry.extraction_event(ExtractionEvent.OUTPUT_GENERATED, extraction_id=extraction_id)
                    return result
                except Exception as e:
                    telemetry.extraction_event(
                        ExtractionEvent.PARSING_FAILED,
                        extraction_id=extraction_id,
                        error=str(e),
                    )
                    raise
        return wrapper
    return decorator


# ============================================================================
# REQUEST ID HELPERS
# ============================================================================

def generate_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


def extract_request_id(headers: Dict[str, str]) -> str:
    """
    Extract request ID from headers or generate new one.
    
    Propagates X-Request-ID from inbound requests.
    """
    return headers.get('X-Request-ID') or headers.get('x-request-id') or generate_request_id()


def sanitize_api_key_for_logging(api_key: str) -> str:
    """
    Sanitize API key for logging (show only first 8 chars).
    
    NEVER log full API keys.
    """
    if not api_key:
        return "none"
    return api_key[:8] + "..." if len(api_key) > 8 else api_key


# ============================================================================
# TELEMETRY CONTRACT DOCUMENTATION
# ============================================================================

TELEMETRY_CONTRACT = """
# PoliSim Telemetry Contract v1.0

## Required Fields (All Events)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| timestamp | ISO8601 | Event timestamp in UTC | 2026-01-02T12:00:00Z |
| env | string | Environment (local/dev/staging/prod) | prod |
| service | string | Service name | polisim-api |
| version | string | Service version | 1.0.0 |
| event | string | Event type from taxonomy | auth.login_success |
| level | string | Log level | INFO |

## Request Context Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| request_id | UUID | Request correlation ID | 550e8400-e29b-41d4-a716-446655440000 |
| trace_id | string | Distributed trace ID (optional) | abc123 |
| route | string | API endpoint path | /api/v1/simulate |
| method | string | HTTP method | POST |
| status_code | int | Response status code | 200 |
| latency_ms | int | Request duration in ms | 150 |

## Actor Context Fields (NEVER log secrets)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| user_id | string | Authenticated user ID | user_123 |
| api_key_id | string | API key prefix (8 chars max) | abc12345... |
| session_id | string | Session identifier | sess_xyz |

## Domain Context Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| policy_id | string | Policy identifier | policy_2024_budget |
| scenario_id | string | Scenario identifier | scenario_base |
| simulation_id | string | Simulation run ID | sim_550e8400 |
| extraction_id | string | Extraction job ID | ext_550e8400 |

## Event Taxonomy

### Authentication Events (auth.*)
- auth.login_success, auth.login_failure
- auth.logout
- auth.token_issued, auth.token_refreshed, auth.token_revoked
- auth.token_expired, auth.token_invalid
- auth.api_key_created, auth.api_key_revoked, auth.api_key_used
- auth.permission_denied

### Rate Limiting Events (rate_limit.*)
- rate_limit.checked, rate_limit.exceeded, rate_limit.warning
- rate_limit.ip_blocked, rate_limit.ip_unblocked

### Circuit Breaker Events (circuit_breaker.*)
- circuit_breaker.opened, circuit_breaker.closed, circuit_breaker.half_open
- circuit_breaker.call_blocked, circuit_breaker.failure_recorded

### Simulation Events (simulation.*)
- simulation.queued, simulation.started, simulation.progress
- simulation.completed, simulation.failed, simulation.cancelled
- simulation.timeout, simulation.validation_error

### Extraction Events (extraction.*)
- extraction.ingested
- extraction.parsing_started, extraction.parsing_completed, extraction.parsing_failed
- extraction.validation_started, extraction.validation_completed, extraction.validation_failed
- extraction.output_generated

### API Events (api.*)
- api.request_received, api.request_completed, api.request_failed
- api.validation_error, api.payload_too_large, api.timeout

### Security Events (security.*)
- security.suspicious_activity, security.brute_force_detected
- security.injection_attempt, security.invalid_input
- security.cors_violation, security.cert_expiring
- security.secret_accessed, security.config_changed

### System Events (system.*)
- system.startup, system.shutdown
- system.health_check, system.health_degraded, system.health_restored
- system.error, system.warning
- system.db_connection_error
- system.cache_miss, system.cache_hit
"""


def get_telemetry_contract() -> str:
    """Return the telemetry contract documentation."""
    return TELEMETRY_CONTRACT
