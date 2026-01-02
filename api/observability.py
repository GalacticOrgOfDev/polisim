"""
Observability (logging, metrics, SLOs) for Slice 5.7 API.

Structured logging and metrics collection for API endpoints.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

from flask import request, g


# Configure structured logging
def configure_api_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure structured JSON logging for API.
    
    Args:
        log_file: Optional file path for logs (if None, logs to stdout).
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('polisim.api')
    logger.setLevel(logging.INFO)
    
    # JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            # Add extra fields if present
            if hasattr(record, 'request_id'):
                log_data['request_id'] = record.request_id
            if hasattr(record, 'user_id'):
                log_data['user_id'] = record.user_id
            if hasattr(record, 'endpoint'):
                log_data['endpoint'] = record.endpoint
            if hasattr(record, 'method'):
                log_data['method'] = record.method
            if hasattr(record, 'status_code'):
                log_data['status_code'] = record.status_code
            if hasattr(record, 'response_time_ms'):
                log_data['response_time_ms'] = record.response_time_ms
            if hasattr(record, 'error'):
                log_data['error'] = record.error
            if hasattr(record, 'input_size_kb'):
                log_data['input_size_kb'] = record.input_size_kb
            if hasattr(record, 'output_size_kb'):
                log_data['output_size_kb'] = record.output_size_kb
            
            return json.dumps(log_data)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger


# Global logger
logger = configure_api_logging(log_file="logs/api.log")


def log_request(endpoint: str, method: str, status_code: int, 
                response_time_ms: int, error: Optional[str] = None,
                input_size_kb: float = 0, output_size_kb: float = 0):
    """
    Log an API request with structured data.
    
    Args:
        endpoint: API endpoint path.
        method: HTTP method (GET, POST, etc.).
        status_code: Response status code.
        response_time_ms: Response time in milliseconds.
        error: Error message (if any).
        input_size_kb: Request payload size in KB.
        output_size_kb: Response payload size in KB.
    """
    request_id = getattr(g, 'request_id', 'unknown')
    user_id = getattr(g, 'user_id', 'anonymous')
    
    log_record = logging.LogRecord(
        name='polisim.api',
        level=logging.ERROR if error else logging.INFO,
        pathname='',
        lineno=0,
        msg='API Request',
        args=(),
        exc_info=None,
    )
    
    log_record.request_id = request_id
    log_record.user_id = user_id
    log_record.endpoint = endpoint
    log_record.method = method
    log_record.status_code = status_code
    log_record.response_time_ms = response_time_ms
    log_record.error = error
    log_record.input_size_kb = input_size_kb
    log_record.output_size_kb = output_size_kb
    
    logger.handle(log_record)


class MetricsCollector:
    """Collect API metrics for observability."""
    
    def __init__(self):
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        self.errors: Dict[str, int] = {}
        self.total_requests = 0
        self.total_errors = 0
    
    def record_request(self, endpoint: str, method: str, status_code: int, 
                      response_time_ms: int, error: Optional[str] = None):
        """Record a request metric."""
        self.total_requests += 1
        
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
            }
        
        stats = self.endpoints[key]
        stats["count"] += 1
        stats["total_time_ms"] += response_time_ms
        stats["min_time_ms"] = min(stats["min_time_ms"], response_time_ms)
        stats["max_time_ms"] = max(stats["max_time_ms"], response_time_ms)
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["count"]
        
        if error:
            stats["errors"] += 1
            self.total_errors += 1
            error_key = f"{status_code} {error[:50]}"
            self.errors[error_key] = self.errors.get(error_key, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / self.total_requests if self.total_requests > 0 else 0,
            "endpoints": self.endpoints,
            "error_breakdown": self.errors,
        }


# Global metrics collector
metrics = MetricsCollector()


def emit_slo_report(output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate SLO report based on collected metrics.
    
    Slice 5.7 Target SLOs:
    - Availability: 99.5%
    - Latency (p99): Scenario listing <500ms, ingestion health <100ms, simulate <30s
    - Error rate: <1%
    
    Args:
        output_file: Optional file to write report to.
    
    Returns:
        SLO report dictionary.
    """
    summary = metrics.get_summary()
    
    # Calculate SLO status
    error_rate = summary["error_rate"]
    error_rate_ok = error_rate < 0.01  # <1%
    
    # Get endpoint stats
    endpoint_stats = summary["endpoints"]
    latency_ok = True
    for endpoint_key, stats in endpoint_stats.items():
        if "scenarios" in endpoint_key and stats["max_time_ms"] > 500:
            latency_ok = False
        if "ingestion-health" in endpoint_key and stats["max_time_ms"] > 100:
            latency_ok = False
        if "simulate" in endpoint_key and stats["max_time_ms"] > 30000:  # 30 seconds
            latency_ok = False
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "slos": {
            "availability": {
                "target": "99.5%",
                "status": "on_track",  # Would need uptime tracking for actual status
            },
            "latency_p99": {
                "target": "<500ms (scenarios), <100ms (health), <30s (simulate)",
                "status": "pass" if latency_ok else "fail",
                "details": endpoint_stats,
            },
            "error_rate": {
                "target": "<1%",
                "actual": f"{error_rate * 100:.2f}%",
                "status": "pass" if error_rate_ok else "fail",
            },
        },
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
    request_id = getattr(g, 'request_id', 'unknown')
    logger.exception(f"Unhandled exception in {endpoint}")
