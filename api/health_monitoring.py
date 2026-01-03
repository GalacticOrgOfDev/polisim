"""
Uptime Monitoring & Health Checks for PoliSim API.

Phase 6.7.5: Provides health check endpoints and uptime monitoring
configuration for external monitoring services.

Features:
- Comprehensive health check endpoint
- Dependency health checks (DB, Redis, external services)
- Readiness and liveness probes for Kubernetes
- Integration with external uptime monitors
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# HEALTH STATUS DEFINITIONS
# ============================================================================

class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DependencyHealth:
    """Health status of a single dependency."""
    name: str
    status: HealthStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    last_check: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
        }
        if self.latency_ms is not None:
            result["latency_ms"] = round(self.latency_ms, 2)
        if self.message:
            result["message"] = self.message
        if self.last_check:
            result["last_check"] = self.last_check
        return result


@dataclass
class HealthCheckResult:
    """Overall health check result."""
    status: HealthStatus
    version: str
    uptime_seconds: float
    timestamp: str
    dependencies: List[DependencyHealth] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": self.timestamp,
            "dependencies": [d.to_dict() for d in self.dependencies],
        }


# ============================================================================
# HEALTH CHECK REGISTRY
# ============================================================================

class HealthCheckRegistry:
    """
    Registry for health check functions.
    
    Allows registering custom health checks for dependencies.
    """
    
    def __init__(self):
        self._checks: Dict[str, Callable[[], DependencyHealth]] = {}
        self._start_time = datetime.now(timezone.utc)
        self._version = os.getenv("POLISIM_VERSION", "1.0.0")
    
    def register(
        self,
        name: str,
        check_fn: Callable[[], DependencyHealth],
    ):
        """
        Register a health check function.
        
        Args:
            name: Name of the dependency.
            check_fn: Function that returns DependencyHealth.
        """
        self._checks[name] = check_fn
    
    def check_all(self) -> HealthCheckResult:
        """
        Run all health checks and return overall status.
        """
        dependencies = []
        overall_status = HealthStatus.HEALTHY
        
        for name, check_fn in self._checks.items():
            try:
                dep_health = check_fn()
                dependencies.append(dep_health)
                
                # Determine overall status
                if dep_health.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif dep_health.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                dependencies.append(DependencyHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    last_check=datetime.now(timezone.utc).isoformat(),
                ))
                overall_status = HealthStatus.UNHEALTHY
        
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        return HealthCheckResult(
            status=overall_status,
            version=self._version,
            uptime_seconds=uptime,
            timestamp=datetime.now(timezone.utc).isoformat(),
            dependencies=dependencies,
        )
    
    def check_liveness(self) -> bool:
        """
        Simple liveness check (is the service running?).
        
        Used by Kubernetes liveness probes.
        """
        return True
    
    def check_readiness(self) -> bool:
        """
        Readiness check (is the service ready to accept traffic?).
        
        Used by Kubernetes readiness probes.
        """
        result = self.check_all()
        return result.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


# Global registry
_health_registry: Optional[HealthCheckRegistry] = None


def get_health_registry() -> HealthCheckRegistry:
    """Get or create global health check registry."""
    global _health_registry
    if _health_registry is None:
        _health_registry = HealthCheckRegistry()
        _register_default_checks(_health_registry)
    return _health_registry


# ============================================================================
# DEFAULT HEALTH CHECKS
# ============================================================================

def _register_default_checks(registry: HealthCheckRegistry):
    """Register default health checks."""
    # Self check
    registry.register("self", _check_self)
    
    # Database check (if available)
    registry.register("database", _check_database)
    
    # Redis check (if available)
    registry.register("redis", _check_redis)


def _check_self() -> DependencyHealth:
    """Self health check - always healthy if running."""
    return DependencyHealth(
        name="self",
        status=HealthStatus.HEALTHY,
        message="Service is running",
        last_check=datetime.now(timezone.utc).isoformat(),
    )


def _check_database() -> DependencyHealth:
    """Database health check."""
    start = time.time()
    
    try:
        # Try to import database module
        from api.database import get_db_session
        from sqlalchemy import text
        
        with get_db_session() as session:
            # Simple query to check connectivity
            session.execute(text("SELECT 1"))
            
        latency = (time.time() - start) * 1000
        
        return DependencyHealth(
            name="database",
            status=HealthStatus.HEALTHY if latency < 1000 else HealthStatus.DEGRADED,
            latency_ms=latency,
            message="Connected" if latency < 1000 else "Slow response",
            last_check=datetime.now(timezone.utc).isoformat(),
        )
        
    except ImportError:
        return DependencyHealth(
            name="database",
            status=HealthStatus.UNKNOWN,
            message="Database module not available",
            last_check=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return DependencyHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=str(e)[:100],
            last_check=datetime.now(timezone.utc).isoformat(),
        )


def _check_redis() -> DependencyHealth:
    """Redis health check."""
    start = time.time()
    
    try:
        import redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, socket_timeout=5)
        client.ping()
        
        latency = (time.time() - start) * 1000
        
        return DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY if latency < 100 else HealthStatus.DEGRADED,
            latency_ms=latency,
            message="Connected" if latency < 100 else "Slow response",
            last_check=datetime.now(timezone.utc).isoformat(),
        )
        
    except ImportError:
        return DependencyHealth(
            name="redis",
            status=HealthStatus.UNKNOWN,
            message="Redis module not available",
            last_check=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return DependencyHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=str(e)[:100],
            last_check=datetime.now(timezone.utc).isoformat(),
        )


# ============================================================================
# FLASK INTEGRATION
# ============================================================================

def add_health_endpoints(app):
    """
    Add health check endpoints to Flask app.
    
    Endpoints:
    - GET /health - Full health check with dependencies
    - GET /health/live - Liveness probe (always 200 if running)
    - GET /health/ready - Readiness probe (200 if ready to serve)
    
    Args:
        app: Flask application instance.
    """
    try:
        from flask import jsonify
    except ImportError:
        logger.warning("Flask not available, skipping health endpoints")
        return
    
    registry = get_health_registry()
    
    @app.route("/health", methods=["GET"])
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Full health check endpoint."""
        result = registry.check_all()
        status_code = 200 if result.status == HealthStatus.HEALTHY else (
            503 if result.status == HealthStatus.UNHEALTHY else 200
        )
        return jsonify(result.to_dict()), status_code
    
    @app.route("/health/live", methods=["GET"])
    @app.route("/api/health/live", methods=["GET"])
    def liveness_probe():
        """Kubernetes liveness probe."""
        if registry.check_liveness():
            return jsonify({"status": "alive"}), 200
        return jsonify({"status": "dead"}), 503
    
    @app.route("/health/ready", methods=["GET"])
    @app.route("/api/health/ready", methods=["GET"])
    def readiness_probe():
        """Kubernetes readiness probe."""
        if registry.check_readiness():
            return jsonify({"status": "ready"}), 200
        return jsonify({"status": "not ready"}), 503
    
    logger.info("Health check endpoints registered")


# ============================================================================
# EXTERNAL UPTIME MONITORING CONFIGURATION
# ============================================================================

UPTIME_MONITOR_CONFIG = """
# External Uptime Monitoring Configuration
# Phase 6.7.5: PoliSim Uptime Monitoring

# ============================================================================
# OPTION 1: UptimeRobot (Free tier available)
# ============================================================================
# 
# Setup:
# 1. Create account at https://uptimerobot.com
# 2. Add new monitor:
#    - Monitor Type: HTTP(s)
#    - Friendly Name: PoliSim API - {environment}
#    - URL: https://{your-domain}/health
#    - Monitoring Interval: 5 minutes
# 3. Configure alerts:
#    - Add alert contacts (email, Slack, webhook)
#    - Set up status page (optional)

# ============================================================================
# OPTION 2: Pingdom
# ============================================================================
#
# Setup:
# 1. Create account at https://www.pingdom.com
# 2. Add uptime check:
#    - Name: PoliSim API
#    - URL: https://{your-domain}/health
#    - Check interval: 1 minute
#    - Check locations: Multiple regions
# 3. Configure integrations:
#    - PagerDuty, Slack, email

# ============================================================================
# OPTION 3: AWS CloudWatch Synthetics
# ============================================================================
#
# For AWS-hosted deployments:
# 
# aws synthetics create-canary \\
#   --name polisim-health-check \\
#   --artifact-s3-location s3://your-bucket/canary-artifacts/ \\
#   --execution-role-arn arn:aws:iam::123456789:role/CanaryRole \\
#   --schedule Expression='rate(5 minutes)' \\
#   --runtime-version syn-python-selenium-1.0 \\
#   --code Handler=health_check.handler \\
#   --run-config TimeoutInSeconds=60

# ============================================================================
# HEALTH ENDPOINT EXPECTED RESPONSE
# ============================================================================
#
# Healthy response (HTTP 200):
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "uptime_seconds": 86400.5,
#   "timestamp": "2026-01-02T12:00:00Z",
#   "dependencies": [
#     {"name": "self", "status": "healthy"},
#     {"name": "database", "status": "healthy", "latency_ms": 5.2},
#     {"name": "redis", "status": "healthy", "latency_ms": 1.1}
#   ]
# }
#
# Degraded response (HTTP 200):
# {
#   "status": "degraded",
#   ...
# }
#
# Unhealthy response (HTTP 503):
# {
#   "status": "unhealthy",
#   ...
# }

# ============================================================================
# ALERT ROUTING CONFIGURATION
# ============================================================================
#
# Critical alerts (service down):
#   - Route to: PagerDuty on-call rotation
#   - Channels: SMS + Push + Call
#   - Response time: 1 minute
#   - Runbook: docs/INCIDENT_RESPONSE.md#service-down
#
# High alerts (degraded service):
#   - Route to: Slack #polisim-ops
#   - Channels: Slack + Email
#   - Response time: 15 minutes
#   - Runbook: docs/INCIDENT_RESPONSE.md#service-degraded
#
# Medium alerts (warnings):
#   - Route to: Email ops@polisim.org
#   - Response time: 1 hour
#   - Review in next business day
"""


def get_uptime_config() -> str:
    """Return uptime monitoring configuration documentation."""
    return UPTIME_MONITOR_CONFIG


# ============================================================================
# ALERT ROUTING
# ============================================================================

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AlertRoute:
    """Configuration for routing an alert."""
    severity: AlertSeverity
    channels: List[str]
    escalation_minutes: int
    runbook_url: Optional[str] = None


# Alert routing configuration
ALERT_ROUTES: Dict[str, AlertRoute] = {
    "service_down": AlertRoute(
        severity=AlertSeverity.CRITICAL,
        channels=["pagerduty", "slack-critical", "sms"],
        escalation_minutes=1,
        runbook_url="https://github.com/GalacticOrgOfDev/polisim/blob/main/docs/INCIDENT_RESPONSE.md#service-down",
    ),
    "high_error_rate": AlertRoute(
        severity=AlertSeverity.HIGH,
        channels=["slack-ops", "email"],
        escalation_minutes=15,
        runbook_url="https://github.com/GalacticOrgOfDev/polisim/blob/main/docs/INCIDENT_RESPONSE.md#elevated-errors",
    ),
    "high_latency": AlertRoute(
        severity=AlertSeverity.HIGH,
        channels=["slack-ops", "email"],
        escalation_minutes=15,
        runbook_url="https://github.com/GalacticOrgOfDev/polisim/blob/main/docs/INCIDENT_RESPONSE.md#performance-degradation",
    ),
    "auth_failures": AlertRoute(
        severity=AlertSeverity.HIGH,
        channels=["slack-security", "pagerduty"],
        escalation_minutes=5,
        runbook_url="https://github.com/GalacticOrgOfDev/polisim/blob/main/docs/INCIDENT_RESPONSE.md#suspected-breach",
    ),
    "rate_limit_violations": AlertRoute(
        severity=AlertSeverity.MEDIUM,
        channels=["slack-ops", "email"],
        escalation_minutes=30,
        runbook_url="https://github.com/GalacticOrgOfDev/polisim/blob/main/docs/INCIDENT_RESPONSE.md#ddos-attack",
    ),
    "simulation_failures": AlertRoute(
        severity=AlertSeverity.MEDIUM,
        channels=["slack-ops", "email"],
        escalation_minutes=60,
        runbook_url="https://github.com/GalacticOrgOfDev/polisim/blob/main/docs/INCIDENT_RESPONSE.md#simulation-errors",
    ),
}


def get_alert_route(alert_type: str) -> Optional[AlertRoute]:
    """Get alert routing configuration for an alert type."""
    return ALERT_ROUTES.get(alert_type)


def format_alert_for_slack(
    alert_type: str,
    title: str,
    description: str,
    severity: AlertSeverity,
    **context,
) -> Dict[str, Any]:
    """
    Format an alert for Slack webhook.
    
    Returns a Slack message payload.
    """
    route = get_alert_route(alert_type)
    
    color = {
        AlertSeverity.CRITICAL: "#ff0000",
        AlertSeverity.HIGH: "#ff9900",
        AlertSeverity.MEDIUM: "#ffcc00",
        AlertSeverity.LOW: "#00ff00",
    }.get(severity, "#808080")
    
    fields = [
        {"title": "Severity", "value": severity.value.upper(), "short": True},
        {"title": "Environment", "value": os.getenv("POLISIM_ENV", "unknown"), "short": True},
    ]
    
    for key, value in context.items():
        fields.append({"title": key.replace("_", " ").title(), "value": str(value), "short": True})
    
    message = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": description,
                "fields": fields,
                "footer": "PoliSim Monitoring",
                "ts": int(datetime.now().timestamp()),
            }
        ]
    }
    
    if route and route.runbook_url:
        message["attachments"][0]["actions"] = [
            {
                "type": "button",
                "text": "View Runbook",
                "url": route.runbook_url,
            }
        ]
    
    return message


def format_alert_for_pagerduty(
    alert_type: str,
    title: str,
    description: str,
    severity: AlertSeverity,
    **context,
) -> Dict[str, Any]:
    """
    Format an alert for PagerDuty Events API v2.
    
    Returns a PagerDuty event payload.
    """
    route = get_alert_route(alert_type)
    
    pd_severity = {
        AlertSeverity.CRITICAL: "critical",
        AlertSeverity.HIGH: "error",
        AlertSeverity.MEDIUM: "warning",
        AlertSeverity.LOW: "info",
    }.get(severity, "info")
    
    payload = {
        "routing_key": os.getenv("PAGERDUTY_ROUTING_KEY", ""),
        "event_action": "trigger",
        "dedup_key": f"polisim-{alert_type}-{os.getenv('POLISIM_ENV', 'unknown')}",
        "payload": {
            "summary": title,
            "source": f"polisim-{os.getenv('POLISIM_ENV', 'unknown')}",
            "severity": pd_severity,
            "custom_details": {
                "description": description,
                **context,
            },
        },
    }
    
    if route and route.runbook_url:
        payload["links"] = [
            {"href": route.runbook_url, "text": "Runbook"}  # type: ignore[list-item]
        ]
    
    return payload
