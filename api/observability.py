"""
Observability (logging, metrics, SLOs) for PoliSim API.

Phase 6.7: Enhanced observability with structured logging, metrics collection,
and SLO reporting. Integrates with the telemetry module for consistent
event taxonomy and correlation.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from pathlib import Path

try:
    from flask import request, g
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

# Import telemetry module (Phase 6.7.1)
try:
    from api.telemetry import (
        get_telemetry, TelemetryContext, TelemetryEmitter,
        APIEvent, AuthEvent, RateLimitEvent, SimulationEvent,
        Environment, extract_request_id, sanitize_api_key_for_logging
    )
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False


# ============================================================================
# STRUCTURED JSON LOGGING
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Phase 6.7.2: Ensures consistent JSON format for log aggregation.
    """
    
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 'authorization',
        'cookie', 'session', 'credential', 'private_key', 'access_key',
    }
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "env": os.getenv("POLISIM_ENV", "local"),
            "service": "polisim-api",
            "version": os.getenv("POLISIM_VERSION", "1.0.0"),
        }
        
        # Add extra fields if present (Phase 6.7.1 telemetry contract)
        extra_fields = [
            'request_id', 'user_id', 'api_key_id', 'endpoint', 'route',
            'method', 'status_code', 'response_time_ms', 'latency_ms',
            'error', 'input_size_kb', 'output_size_kb', 'event', 'event_category',
            'simulation_id', 'extraction_id', 'policy_id', 'scenario_id',
            'session_id', 'client_ip', 'user_agent',
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                # Sanitize sensitive data
                if any(sensitive in field.lower() for sensitive in self.SENSITIVE_FIELDS):
                    log_data[field] = "[REDACTED]"
                else:
                    log_data[field] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


def configure_api_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure structured JSON logging for API.
    
    Phase 6.7.2: Enhanced with consistent JSON format and multiple handlers.
    
    Args:
        log_file: Optional file path for logs (if None, logs to stdout).
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('polisim.api')
    logger.setLevel(logging.INFO)
    logger.handlers = []  # Clear existing handlers
    
    formatter = JSONFormatter()
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Also log to telemetry log if telemetry module available
    telemetry_log = "logs/telemetry.log"
    if log_file != telemetry_log:
        telemetry_dir = Path(telemetry_log).parent
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        telemetry_handler = logging.FileHandler(telemetry_log)
        telemetry_handler.setFormatter(formatter)
        logger.addHandler(telemetry_handler)
    
    return logger


# Global logger
logger = configure_api_logging(log_file="logs/api.log")


def log_request(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: int,
    error: Optional[str] = None,
    input_size_kb: float = 0,
    output_size_kb: float = 0,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """
    Log an API request with structured data.
    
    Phase 6.7.2: Enhanced with full telemetry contract compliance.
    
    Args:
        endpoint: API endpoint path.
        method: HTTP method (GET, POST, etc.).
        status_code: Response status code.
        response_time_ms: Response time in milliseconds.
        error: Error message (if any).
        input_size_kb: Request payload size in KB.
        output_size_kb: Response payload size in KB.
        client_ip: Client IP address.
        user_agent: Client user agent string.
    """
    # Get context from Flask g object if available
    request_id = 'unknown'
    user_id = 'anonymous'
    api_key_id = None
    session_id = None
    
    if HAS_FLASK:
        try:
            request_id = getattr(g, 'request_id', 'unknown')
            user_id = getattr(g, 'user_id', 'anonymous')
            api_key_id = getattr(g, 'api_key_id', None)
            session_id = getattr(g, 'session_id', None)
        except RuntimeError:
            pass  # Outside of request context
    
    # Determine event type based on status code
    if error or status_code >= 500:
        event = "api.request_failed"
        level = logging.ERROR
    elif status_code >= 400:
        event = "api.validation_error"
        level = logging.WARNING
    else:
        event = "api.request_completed"
        level = logging.INFO
    
    log_record = logging.LogRecord(
        name='polisim.api',
        level=level,
        pathname='',
        lineno=0,
        msg='API Request',
        args=(),
        exc_info=None,
    )
    
    # Telemetry contract fields (Phase 6.7.1)
    log_record.event = event
    log_record.event_category = "api"
    log_record.request_id = request_id
    log_record.user_id = user_id
    log_record.route = endpoint
    log_record.endpoint = endpoint  # Alias for compatibility
    log_record.method = method
    log_record.status_code = status_code
    log_record.response_time_ms = response_time_ms
    log_record.latency_ms = response_time_ms  # Alias
    log_record.error = error
    log_record.input_size_kb = input_size_kb
    log_record.output_size_kb = output_size_kb
    
    # Optional fields
    if api_key_id:
        log_record.api_key_id = api_key_id[:8] + "..." if len(api_key_id) > 8 else api_key_id
    if session_id:
        log_record.session_id = session_id
    if client_ip:
        log_record.client_ip = client_ip
    if user_agent:
        log_record.user_agent = user_agent
    
    logger.handle(log_record)
    
    # Also emit to telemetry module if available
    if HAS_TELEMETRY:
        try:
            telemetry = get_telemetry()
            telemetry.api_event(
                APIEvent.REQUEST_COMPLETED if status_code < 400 else APIEvent.REQUEST_FAILED,
                request_id=request_id,
                route=endpoint,
                method=method,
                status_code=status_code,
                latency_ms=response_time_ms,
            )
        except Exception:
            pass  # Don't fail on telemetry errors


class MetricsCollector:
    """
    Collect API metrics for observability.
    
    Phase 6.7.2: Enhanced with Prometheus-compatible metrics export,
    histogram buckets for latency, and comprehensive event tracking.
    """
    
    # Histogram buckets for latency (in milliseconds)
    LATENCY_BUCKETS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000]
    
    def __init__(self):
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        self.errors: Dict[str, int] = {}
        self.status_codes: Dict[int, int] = {}
        self.total_requests = 0
        self.total_errors = 0
        self.auth_failures = 0
        self.rate_limit_exceeded = 0
        self.simulation_count = 0
        self.simulation_failures = 0
        self.simulation_timeouts = 0
        self.latency_histogram: Dict[str, Dict[Union[int, str], int]] = {}
        self._start_time = datetime.now(timezone.utc)
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        error: Optional[str] = None,
    ):
        """Record a request metric."""
        self.total_requests += 1
        
        # Track status codes
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        
        # Track by endpoint+method
        key = f"{method} {endpoint}"
        if key not in self.endpoints:
            self.endpoints[key] = {
                "count": 0,
                "total_time_ms": 0,
                "min_time_ms": response_time_ms,
                "max_time_ms": response_time_ms,
                "errors": 0,
                "avg_time_ms": 0,
                "status_codes": {},
            }
            # Initialize latency histogram for this endpoint
            self.latency_histogram[key] = {bucket: 0 for bucket in self.LATENCY_BUCKETS}
            self.latency_histogram[key]["inf"] = 0
        
        stats = self.endpoints[key]
        stats["count"] += 1
        stats["total_time_ms"] += response_time_ms
        stats["min_time_ms"] = min(stats["min_time_ms"], response_time_ms)
        stats["max_time_ms"] = max(stats["max_time_ms"], response_time_ms)
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["count"]
        stats["status_codes"][status_code] = stats["status_codes"].get(status_code, 0) + 1
        
        # Update latency histogram
        for bucket in self.LATENCY_BUCKETS:
            if response_time_ms <= bucket:
                self.latency_histogram[key][bucket] += 1
                break
        else:
            self.latency_histogram[key]["inf"] += 1
        
        if error or status_code >= 500:
            stats["errors"] += 1
            self.total_errors += 1
            error_key = f"{status_code} {(error or 'Unknown error')[:50]}"
            self.errors[error_key] = self.errors.get(error_key, 0) + 1
    
    def record_auth_failure(self):
        """Record an authentication failure."""
        self.auth_failures += 1
    
    def record_rate_limit_exceeded(self):
        """Record a rate limit exceeded event."""
        self.rate_limit_exceeded += 1
    
    def record_simulation(self, success: bool, timeout: bool = False):
        """Record a simulation event."""
        self.simulation_count += 1
        if not success:
            self.simulation_failures += 1
        if timeout:
            self.simulation_timeouts += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        uptime_seconds = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / self.total_requests if self.total_requests > 0 else 0,
            "status_codes": self.status_codes,
            "endpoints": self.endpoints,
            "error_breakdown": self.errors,
            "auth_failures": self.auth_failures,
            "rate_limit_exceeded": self.rate_limit_exceeded,
            "simulation_count": self.simulation_count,
            "simulation_failures": self.simulation_failures,
            "simulation_timeouts": self.simulation_timeouts,
            "uptime_seconds": uptime_seconds,
        }
    
    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Phase 6.7.2: Prometheus-compatible metrics endpoint.
        """
        lines = []
        summary = self.get_summary()
        
        # Help and type declarations
        lines.append("# HELP polisim_http_requests_total Total HTTP requests")
        lines.append("# TYPE polisim_http_requests_total counter")
        lines.append(f"polisim_http_requests_total {summary['total_requests']}")
        
        lines.append("# HELP polisim_http_errors_total Total HTTP errors")
        lines.append("# TYPE polisim_http_errors_total counter")
        lines.append(f"polisim_http_errors_total {summary['total_errors']}")
        
        # Requests by status code
        lines.append("# HELP polisim_http_requests_by_status HTTP requests by status code")
        lines.append("# TYPE polisim_http_requests_by_status counter")
        for status, count in summary["status_codes"].items():
            lines.append(f'polisim_http_requests_by_status{{status="{status}"}} {count}')
        
        # Auth failures
        lines.append("# HELP polisim_auth_failures_total Total authentication failures")
        lines.append("# TYPE polisim_auth_failures_total counter")
        lines.append(f"polisim_auth_failures_total {summary['auth_failures']}")
        
        # Rate limit exceeded
        lines.append("# HELP polisim_rate_limit_exceeded_total Total rate limit exceeded events")
        lines.append("# TYPE polisim_rate_limit_exceeded_total counter")
        lines.append(f"polisim_rate_limit_exceeded_total {summary['rate_limit_exceeded']}")
        
        # Simulation metrics
        lines.append("# HELP polisim_simulation_total Total simulations")
        lines.append("# TYPE polisim_simulation_total counter")
        lines.append(f"polisim_simulation_total {summary['simulation_count']}")
        
        lines.append("# HELP polisim_simulation_failures_total Total simulation failures")
        lines.append("# TYPE polisim_simulation_failures_total counter")
        lines.append(f"polisim_simulation_failures_total {summary['simulation_failures']}")
        
        lines.append("# HELP polisim_simulation_timeouts_total Total simulation timeouts")
        lines.append("# TYPE polisim_simulation_timeouts_total counter")
        lines.append(f"polisim_simulation_timeouts_total {summary['simulation_timeouts']}")
        
        # Latency histogram
        lines.append("# HELP polisim_http_request_duration_seconds HTTP request duration in seconds")
        lines.append("# TYPE polisim_http_request_duration_seconds histogram")
        for endpoint_key, histogram in self.latency_histogram.items():
            # Clean endpoint key for label
            clean_key = endpoint_key.replace('"', '\\"')
            cumulative = 0
            for bucket in self.LATENCY_BUCKETS:
                cumulative += histogram.get(bucket, 0)
                bucket_seconds = bucket / 1000.0
                lines.append(f'polisim_http_request_duration_seconds_bucket{{endpoint="{clean_key}",le="{bucket_seconds}"}} {cumulative}')
            cumulative += histogram.get("inf", 0)
            lines.append(f'polisim_http_request_duration_seconds_bucket{{endpoint="{clean_key}",le="+Inf"}} {cumulative}')
            
            # Sum and count
            if endpoint_key in self.endpoints:
                total_time_s = self.endpoints[endpoint_key]["total_time_ms"] / 1000.0
                count = self.endpoints[endpoint_key]["count"]
                lines.append(f'polisim_http_request_duration_seconds_sum{{endpoint="{clean_key}"}} {total_time_s}')
                lines.append(f'polisim_http_request_duration_seconds_count{{endpoint="{clean_key}"}} {count}')
        
        # Uptime
        lines.append("# HELP polisim_uptime_seconds Service uptime in seconds")
        lines.append("# TYPE polisim_uptime_seconds gauge")
        lines.append(f"polisim_uptime_seconds {summary['uptime_seconds']}")
        
        return "\n".join(lines)


# Global metrics collector
metrics = MetricsCollector()


def emit_slo_report(output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate SLO report based on collected metrics.
    
    Phase 6.7.4: Enhanced SLO reporting with comprehensive status tracking.
    
    Target SLOs:
    - Availability: 99.5%
    - Latency (p95): <500ms for most endpoints, <30s for simulate
    - Error rate: <1%
    - Simulation success rate: >95%
    
    Args:
        output_file: Optional file to write report to.
    
    Returns:
        SLO report dictionary.
    """
    summary = metrics.get_summary()
    
    # Calculate SLO status
    error_rate = summary["error_rate"]
    error_rate_ok = error_rate < 0.01  # <1%
    
    # Simulation success rate
    sim_count = summary["simulation_count"]
    sim_failures = summary["simulation_failures"]
    sim_success_rate = (sim_count - sim_failures) / sim_count if sim_count > 0 else 1.0
    sim_success_ok = sim_success_rate >= 0.95
    
    # Get endpoint stats
    endpoint_stats = summary["endpoints"]
    latency_ok = True
    latency_issues = []
    for endpoint_key, stats in endpoint_stats.items():
        if "scenarios" in endpoint_key and stats["max_time_ms"] > 500:
            latency_ok = False
            latency_issues.append(f"{endpoint_key}: {stats['max_time_ms']}ms > 500ms")
        if "ingestion-health" in endpoint_key and stats["max_time_ms"] > 100:
            latency_ok = False
            latency_issues.append(f"{endpoint_key}: {stats['max_time_ms']}ms > 100ms")
        if "simulate" in endpoint_key and stats["max_time_ms"] > 30000:
            latency_ok = False
            latency_issues.append(f"{endpoint_key}: {stats['max_time_ms']}ms > 30000ms")
    
    # Calculate availability (based on error rate as proxy)
    availability = 1.0 - error_rate
    availability_ok = availability >= 0.995
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "env": os.getenv("POLISIM_ENV", "local"),
        "service": "polisim-api",
        "version": os.getenv("POLISIM_VERSION", "1.0.0"),
        "uptime_seconds": summary["uptime_seconds"],
        "slos": {
            "availability": {
                "target": "99.5%",
                "actual": f"{availability * 100:.2f}%",
                "status": "pass" if availability_ok else "fail",
            },
            "latency": {
                "target": "<500ms (p95), <30s (simulate)",
                "status": "pass" if latency_ok else "fail",
                "issues": latency_issues if not latency_ok else [],
            },
            "error_rate": {
                "target": "<1%",
                "actual": f"{error_rate * 100:.2f}%",
                "status": "pass" if error_rate_ok else "fail",
            },
            "simulation_success_rate": {
                "target": ">95%",
                "actual": f"{sim_success_rate * 100:.2f}%",
                "status": "pass" if sim_success_ok else "fail",
                "total": sim_count,
                "failures": sim_failures,
                "timeouts": summary["simulation_timeouts"],
            },
        },
        "overall_status": "healthy" if all([
            availability_ok, latency_ok, error_rate_ok, sim_success_ok
        ]) else "degraded",
        "metrics_summary": summary,
    }
    
    if output_file:
        output_dir = Path(output_file).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    return report


def log_exception(exception: Exception, endpoint: str = "unknown"):
    """Log an exception with context."""
    request_id = 'unknown'
    if HAS_FLASK:
        try:
            request_id = getattr(g, 'request_id', 'unknown')
        except RuntimeError:
            pass
    logger.exception(f"Unhandled exception in {endpoint}", extra={"request_id": request_id})

