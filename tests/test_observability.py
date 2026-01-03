"""
Tests for Phase 6.7: Monitoring & Observability

This module tests:
- 6.7.1: Telemetry contract and event taxonomy
- 6.7.2: Structured logging (observability.py enhancements)
- 6.7.3: Sentry integration (when available)
- 6.7.4: SLO reporting
- 6.7.5: Health monitoring and alert routing
"""

import json
import logging
import os
import sys
import time
import threading
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Ensure api module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# 6.7.1: TELEMETRY CONTRACT TESTS
# ============================================================================

class TestTelemetryContract:
    """Tests for telemetry.py - event taxonomy and contract."""
    
    def test_telemetry_context_creation(self):
        """Test TelemetryContext dataclass creation."""
        from api.telemetry import TelemetryContext
        
        ctx = TelemetryContext(
            request_id="req-123",
            user_id="user-456",
            service="polisim-api",
        )
        
        assert ctx.request_id == "req-123"
        assert ctx.user_id == "user-456"
        assert ctx.service == "polisim-api"
        assert ctx.env is not None
    
    def test_telemetry_context_to_dict(self):
        """Test TelemetryContext serialization."""
        from api.telemetry import TelemetryContext
        
        ctx = TelemetryContext(
            request_id="req-123",
            user_id="user-456",
            service="simulation",
            status_code=500,
        )
        
        data = ctx.to_dict()
        
        assert data["request_id"] == "req-123"
        assert data["user_id"] == "user-456"
        assert data["service"] == "simulation"
        assert data["status_code"] == 500
        assert "env" in data
    
    def test_telemetry_context_with_extra(self):
        """Test TelemetryContext with extra fields."""
        from api.telemetry import TelemetryContext
        
        ctx = TelemetryContext(
            request_id="req-123",
            user_id="user-456",
            service="api",
            extra={"custom_field": "custom_value", "duration_ms": 150},
        )
        
        data = ctx.to_dict()
        
        assert data["extra"]["custom_field"] == "custom_value"
        assert data["extra"]["duration_ms"] == 150
    
    def test_telemetry_context_with_request(self):
        """Test TelemetryContext.with_request() method."""
        from api.telemetry import TelemetryContext
        
        ctx = TelemetryContext(user_id="user-456")
        new_ctx = ctx.with_request("req-789", "/api/v1/policies", "GET")
        
        assert new_ctx.request_id == "req-789"
        assert new_ctx.route == "/api/v1/policies"
        assert new_ctx.method == "GET"
        assert new_ctx.user_id == "user-456"  # Preserved
    
    def test_auth_event_enum(self):
        """Test AuthEvent enum values."""
        from api.telemetry import AuthEvent
        
        assert AuthEvent.LOGIN_SUCCESS.value == "auth.login_success"
        assert AuthEvent.LOGIN_FAILURE.value == "auth.login_failure"
        assert AuthEvent.TOKEN_REFRESHED.value == "auth.token_refreshed"
        assert AuthEvent.LOGOUT.value == "auth.logout"
    
    def test_simulation_event_enum(self):
        """Test SimulationEvent enum values."""
        from api.telemetry import SimulationEvent
        
        assert SimulationEvent.STARTED.value == "simulation.started"
        assert SimulationEvent.COMPLETED.value == "simulation.completed"
        assert SimulationEvent.FAILED.value == "simulation.failed"
    
    def test_api_event_enum(self):
        """Test APIEvent enum values."""
        from api.telemetry import APIEvent
        
        assert APIEvent.REQUEST_RECEIVED.value == "api.request_received"
        assert APIEvent.REQUEST_COMPLETED.value == "api.request_completed"
        assert APIEvent.VALIDATION_ERROR.value == "api.validation_error"
    
    def test_rate_limit_event_enum(self):
        """Test RateLimitEvent enum values."""
        from api.telemetry import RateLimitEvent
        
        assert RateLimitEvent.LIMIT_EXCEEDED.value == "rate_limit.exceeded"
        assert RateLimitEvent.IP_BLOCKED.value == "rate_limit.ip_blocked"
    
    def test_circuit_breaker_event_enum(self):
        """Test CircuitBreakerEvent enum values."""
        from api.telemetry import CircuitBreakerEvent
        
        assert CircuitBreakerEvent.OPENED.value == "circuit_breaker.opened"
        assert CircuitBreakerEvent.CLOSED.value == "circuit_breaker.closed"
    
    def test_security_event_enum(self):
        """Test SecurityEvent enum values."""
        from api.telemetry import SecurityEvent
        
        assert SecurityEvent.BRUTE_FORCE_DETECTED.value == "security.brute_force_detected"
        assert SecurityEvent.INJECTION_ATTEMPT.value == "security.injection_attempt"
    
    def test_telemetry_emitter_creation(self):
        """Test TelemetryEmitter initialization."""
        from api.telemetry import TelemetryEmitter
        
        emitter = TelemetryEmitter(service_name="test", enable_console=False, enable_file=False)
        assert emitter.service_name == "test"
    
    def test_telemetry_emitter_emit(self):
        """Test TelemetryEmitter.emit creates proper event."""
        from api.telemetry import TelemetryEmitter
        
        emitter = TelemetryEmitter(service_name="test_component", enable_console=False, enable_file=False)
        
        # Should not raise
        emitter.emit(
            event="test.event",
            message="Test message",
        )
    
    def test_telemetry_emitter_context(self):
        """Test TelemetryEmitter context manager."""
        from api.telemetry import TelemetryEmitter, TelemetryContext
        
        emitter = TelemetryEmitter(service_name="test", enable_console=False, enable_file=False)
        
        ctx = TelemetryContext(request_id="req-123", user_id="user-456")
        
        with emitter.context(ctx):
            current = emitter.get_context()
            assert current.request_id == "req-123"
        
        # Context should be popped
        after = emitter.get_context()
        assert after.request_id is None
    
    def test_environment_enum(self):
        """Test Environment enum values."""
        from api.telemetry import Environment
        
        assert Environment.LOCAL.value == "local"
        assert Environment.DEV.value == "dev"
        assert Environment.STAGING.value == "staging"
        assert Environment.PROD.value == "prod"
    
    def test_event_category_enum(self):
        """Test EventCategory enum values."""
        from api.telemetry import EventCategory
        
        assert EventCategory.AUTH.value == "auth"
        assert EventCategory.SIMULATION.value == "simulation"
        assert EventCategory.SECURITY.value == "security"


class TestTelemetryDecorators:
    """Tests for telemetry decorators."""
    
    def test_trace_simulation_decorator(self):
        """Test @trace_simulation decorator."""
        from api.telemetry import trace_simulation
        
        call_count = 0
        
        @trace_simulation()
        def sample_simulation(simulation_id: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result-{simulation_id}"
        
        result = sample_simulation(simulation_id="sim-123")
        
        assert result == "result-sim-123"
        assert call_count == 1
    
    def test_trace_simulation_with_exception(self):
        """Test @trace_simulation handles exceptions."""
        from api.telemetry import trace_simulation
        
        @trace_simulation()
        def failing_simulation(simulation_id: str):
            raise ValueError("Simulation error")
        
        with pytest.raises(ValueError, match="Simulation error"):
            failing_simulation(simulation_id="sim-fail")
    
    def test_trace_extraction_decorator(self):
        """Test @trace_extraction decorator."""
        from api.telemetry import trace_extraction
        
        call_count = 0
        
        @trace_extraction()
        def sample_extraction(extraction_id: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"extracted-{extraction_id}"
        
        result = sample_extraction(extraction_id="ext-456")
        
        assert result == "extracted-ext-456"
        assert call_count == 1


# ============================================================================
# 6.7.2: STRUCTURED LOGGING TESTS
# ============================================================================

class TestStructuredLogging:
    """Tests for observability.py structured logging."""
    
    def test_json_formatter_basic(self):
        """Test basic JSON formatter output."""
        from api.observability import JSONFormatter
        
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="polisim",
            level=logging.WARNING,
            pathname="api/rest_server.py",
            lineno=42,
            msg="Request failed",
            args=(),
            exc_info=None,
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["level"] == "WARNING"
        assert data["message"] == "Request failed"
        assert data["logger"] == "polisim"
    
    def test_json_formatter_scrubs_sensitive_fields(self):
        """Test JSONFormatter redacts sensitive data."""
        from api.observability import JSONFormatter
        
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="polisim",
            level=logging.INFO,
            pathname="api/auth.py",
            lineno=100,
            msg="User login",
            args=(),
            exc_info=None,
        )
        record.password = "secret123"
        record.token = "jwt-token-xyz"
        record.api_key = "ak-12345"
        
        output = formatter.format(record)
        data = json.loads(output)
        
        # Sensitive fields should be redacted
        assert "secret123" not in output
        assert "jwt-token-xyz" not in output
        assert "ak-12345" not in output
    
    def test_configure_api_logging(self):
        """Test configure_api_logging creates JSON logger."""
        from api.observability import configure_api_logging
        
        logger = configure_api_logging()
        
        assert logger.name == "polisim.api"


class TestMetricsCollector:
    """Tests for MetricsCollector."""
    
    def test_metrics_collector_creation(self):
        """Test MetricsCollector creation."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        assert collector.total_requests == 0
        assert collector.total_errors == 0
    
    def test_record_request(self):
        """Test recording request metrics."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_request(
            endpoint="/api/v1/policies",
            method="GET",
            status_code=200,
            response_time_ms=150,
        )
        
        assert collector.total_requests == 1
        assert collector.total_errors == 0
    
    def test_record_request_with_error(self):
        """Test recording request with error."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_request(
            endpoint="/api/v1/simulate",
            method="POST",
            status_code=500,
            response_time_ms=500,
            error="Internal error",
        )
        
        assert collector.total_requests == 1
        assert collector.total_errors == 1
    
    def test_record_auth_failure(self):
        """Test recording auth failure."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_auth_failure()
        
        assert collector.auth_failures == 1
    
    def test_record_rate_limit(self):
        """Test recording rate limit exceeded."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_rate_limit_exceeded()
        
        assert collector.rate_limit_exceeded == 1
    
    def test_record_simulation(self):
        """Test recording simulation events."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_simulation(success=True)
        collector.record_simulation(success=False)
        collector.record_simulation(success=False, timeout=True)
        
        assert collector.simulation_count == 3
        assert collector.simulation_failures == 2
        assert collector.simulation_timeouts == 1
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_request("/test", "GET", 200, 100)
        collector.record_request("/test", "GET", 500, 200, "Error")
        
        summary = collector.get_summary()
        
        assert summary["total_requests"] == 2
        assert summary["total_errors"] == 1
        assert summary["error_rate"] == 0.5
    
    def test_prometheus_export_format(self):
        """Test Prometheus metrics export format."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        collector.record_request("/health", "GET", 200, 10)
        
        prometheus_output = collector.get_prometheus_metrics()
        
        # Verify Prometheus format
        assert "# HELP" in prometheus_output
        assert "# TYPE" in prometheus_output
        assert "polisim_" in prometheus_output


class TestSLOReporting:
    """Tests for SLO reporting functionality."""
    
    def test_emit_slo_report_structure(self):
        """Test SLO report structure."""
        from api.observability import emit_slo_report
        
        # Should not raise
        report = emit_slo_report()
        
        assert "timestamp" in report
        assert "slos" in report
        assert "overall_status" in report


# ============================================================================
# 6.7.3: SENTRY INTEGRATION TESTS
# ============================================================================

class TestSentryIntegration:
    """Tests for sentry_integration.py (mocked when SDK unavailable)."""
    
    def test_sentry_config_properties(self):
        """Test SentryConfig properties."""
        from api.sentry_integration import SentryConfig
        
        config = SentryConfig()
        
        # Test property access
        assert config.environment is not None
        assert config.release is not None
        assert isinstance(config.traces_sample_rate, float)
        assert isinstance(config.profiles_sample_rate, float)
        assert isinstance(config.send_default_pii, bool)
        assert isinstance(config.enabled, bool)
    
    def test_sentry_config_environment(self):
        """Test SentryConfig environment property."""
        from api.sentry_integration import SentryConfig
        
        with patch.dict(os.environ, {"POLISIM_ENV": "staging"}):
            config = SentryConfig()
            assert config.environment == "staging"
    
    def test_scrub_sensitive_data(self):
        """Test sensitive data scrubbing."""
        from api.sentry_integration import _scrub_dict
        
        data = {
            "username": "john",
            "password": "secret123",
            "token": "jwt-xyz",
            "nested": {
                "api_key": "ak-123",
                "safe_field": "visible",
            }
        }
        
        scrubbed = _scrub_dict(data)
        
        assert scrubbed["username"] == "john"
        assert scrubbed["password"] == "[REDACTED]"
        assert scrubbed["token"] == "[REDACTED]"
        assert scrubbed["nested"]["api_key"] == "[REDACTED]"
        assert scrubbed["nested"]["safe_field"] == "visible"
    
    def test_sentry_enabled_flag(self):
        """Test HAS_SENTRY flag behavior."""
        from api.sentry_integration import HAS_SENTRY
        
        # Should be False in test env without sentry installed
        # or True if sentry-sdk is installed
        assert isinstance(HAS_SENTRY, bool)
    
    def test_capture_exception_without_sentry(self):
        """Test capture_exception gracefully handles missing Sentry."""
        from api.sentry_integration import capture_exception, HAS_SENTRY
        
        if not HAS_SENTRY:
            # Should not raise even without Sentry
            result = capture_exception(ValueError("test"))
            assert result is None
    
    def test_capture_message_without_sentry(self):
        """Test capture_message gracefully handles missing Sentry."""
        from api.sentry_integration import capture_message, HAS_SENTRY
        
        if not HAS_SENTRY:
            result = capture_message("Test message")
            assert result is None


# ============================================================================
# 6.7.5: HEALTH MONITORING TESTS
# ============================================================================

class TestHealthStatus:
    """Tests for HealthStatus enum."""
    
    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        from api.health_monitoring import HealthStatus
        
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestDependencyHealth:
    """Tests for DependencyHealth dataclass."""
    
    def test_dependency_health_creation(self):
        """Test DependencyHealth dataclass creation."""
        from api.health_monitoring import DependencyHealth, HealthStatus
        
        health = DependencyHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=15.5,
            message="Connected",
        )
        
        assert health.name == "database"
        assert health.status == HealthStatus.HEALTHY
        assert health.latency_ms == 15.5
        assert health.message == "Connected"
    
    def test_dependency_health_to_dict(self):
        """Test DependencyHealth serialization."""
        from api.health_monitoring import DependencyHealth, HealthStatus
        
        health = DependencyHealth(
            name="redis",
            status=HealthStatus.DEGRADED,
            latency_ms=250.123,
            message="Slow",
        )
        
        data = health.to_dict()
        
        assert data["name"] == "redis"
        assert data["status"] == "degraded"
        assert data["latency_ms"] == 250.12  # rounded
        assert data["message"] == "Slow"


class TestHealthCheckRegistry:
    """Tests for HealthCheckRegistry."""
    
    def test_registry_creation(self):
        """Test HealthCheckRegistry initialization."""
        from api.health_monitoring import HealthCheckRegistry
        
        registry = HealthCheckRegistry()
        
        assert registry._start_time is not None
    
    def test_registry_register_check(self):
        """Test registering a health check."""
        from api.health_monitoring import HealthCheckRegistry, DependencyHealth, HealthStatus
        
        registry = HealthCheckRegistry()
        
        def my_check() -> DependencyHealth:
            return DependencyHealth(
                name="my_service",
                status=HealthStatus.HEALTHY,
            )
        
        registry.register("my_service", my_check)
        
        assert "my_service" in registry._checks
    
    def test_registry_check_all(self):
        """Test checking all registered health checks."""
        from api.health_monitoring import HealthCheckRegistry, DependencyHealth, HealthStatus
        
        registry = HealthCheckRegistry()
        
        def healthy_check() -> DependencyHealth:
            return DependencyHealth(name="service1", status=HealthStatus.HEALTHY)
        
        registry.register("service1", healthy_check)
        
        result = registry.check_all()
        
        assert result.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY)
        assert result.uptime_seconds >= 0
    
    def test_registry_liveness_check(self):
        """Test liveness check always returns True when running."""
        from api.health_monitoring import HealthCheckRegistry
        
        registry = HealthCheckRegistry()
        
        assert registry.check_liveness() is True
    
    def test_registry_readiness_check(self):
        """Test readiness check logic."""
        from api.health_monitoring import HealthCheckRegistry, DependencyHealth, HealthStatus
        
        registry = HealthCheckRegistry()
        
        def healthy_check() -> DependencyHealth:
            return DependencyHealth(name="test", status=HealthStatus.HEALTHY)
        
        registry.register("test", healthy_check)
        
        # Should be ready when healthy
        assert registry.check_readiness() is True


class TestHealthCheckFunctions:
    """Tests for built-in health check functions."""
    
    def test_check_self(self):
        """Test self health check."""
        from api.health_monitoring import _check_self, HealthStatus
        
        result = _check_self()
        
        assert result.name == "self"
        assert result.status == HealthStatus.HEALTHY
    
    def test_check_database_import_error(self):
        """Test database check handles missing module."""
        from api.health_monitoring import _check_database, HealthStatus
        
        # Should not raise, returns appropriate status
        result = _check_database()
        
        assert result.name == "database"
        assert result.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY)
    
    def test_check_redis_import_error(self):
        """Test redis check handles missing module."""
        from api.health_monitoring import _check_redis, HealthStatus
        
        result = _check_redis()
        
        assert result.name == "redis"


class TestAlertRouting:
    """Tests for alert routing configuration."""
    
    def test_alert_routes_defined(self):
        """Test ALERT_ROUTES configuration exists."""
        from api.health_monitoring import ALERT_ROUTES
        
        assert isinstance(ALERT_ROUTES, dict)
        assert "service_down" in ALERT_ROUTES
        assert "high_error_rate" in ALERT_ROUTES
        assert "auth_failures" in ALERT_ROUTES
    
    def test_alert_severity_enum(self):
        """Test AlertSeverity enum values."""
        from api.health_monitoring import AlertSeverity
        
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.LOW.value == "low"
    
    def test_alert_route_structure(self):
        """Test AlertRoute structure."""
        from api.health_monitoring import AlertRoute, AlertSeverity
        
        route = AlertRoute(
            severity=AlertSeverity.HIGH,
            channels=["pagerduty", "slack"],
            escalation_minutes=15,
            runbook_url="https://docs.example.com/runbook",
        )
        
        assert route.severity == AlertSeverity.HIGH
        assert "pagerduty" in route.channels
        assert route.escalation_minutes == 15
    
    def test_get_alert_route(self):
        """Test get_alert_route function."""
        from api.health_monitoring import get_alert_route
        
        route = get_alert_route("service_down")
        
        assert route is not None
        assert "pagerduty" in route.channels


class TestSlackAlertFormatting:
    """Tests for Slack alert formatting."""
    
    def test_format_alert_for_slack(self):
        """Test Slack alert message formatting."""
        from api.health_monitoring import format_alert_for_slack, AlertSeverity
        
        payload = format_alert_for_slack(
            alert_type="high_error_rate",
            title="High Error Rate",
            description="Error rate exceeded 5%",
            severity=AlertSeverity.HIGH,
            endpoint="/api/v1/simulate",
        )
        
        assert "attachments" in payload
        assert len(payload["attachments"]) > 0
        assert payload["attachments"][0]["title"] == "High Error Rate"


class TestPagerDutyAlertFormatting:
    """Tests for PagerDuty alert formatting."""
    
    def test_format_alert_for_pagerduty(self):
        """Test PagerDuty alert payload formatting."""
        from api.health_monitoring import format_alert_for_pagerduty, AlertSeverity
        
        payload = format_alert_for_pagerduty(
            alert_type="service_down",
            title="Service Unavailable",
            description="API not responding",
            severity=AlertSeverity.CRITICAL,
        )
        
        assert "routing_key" in payload
        assert payload["event_action"] == "trigger"
        assert payload["payload"]["summary"] == "Service Unavailable"


class TestHealthEndpoints:
    """Tests for Flask health endpoints integration."""
    
    def test_add_health_endpoints(self):
        """Test add_health_endpoints registers routes."""
        from flask import Flask
        from api.health_monitoring import add_health_endpoints
        
        app = Flask(__name__)
        add_health_endpoints(app)
        
        # Check routes were registered
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        
        assert "/health" in rules or "/health/" in rules
        assert "/health/live" in rules or "/health/live/" in rules
        assert "/health/ready" in rules or "/health/ready/" in rules
    
    def test_health_endpoint_response(self):
        """Test health endpoint returns proper response."""
        from flask import Flask
        from api.health_monitoring import add_health_endpoints
        
        app = Flask(__name__)
        add_health_endpoints(app)
        
        with app.test_client() as client:
            response = client.get("/health")
            
            assert response.status_code in (200, 503)  # Healthy or unhealthy
            data = response.get_json()
            assert "status" in data
    
    def test_liveness_endpoint(self):
        """Test liveness endpoint always returns 200 when running."""
        from flask import Flask
        from api.health_monitoring import add_health_endpoints
        
        app = Flask(__name__)
        add_health_endpoints(app)
        
        with app.test_client() as client:
            response = client.get("/health/live")
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "alive"
    
    def test_readiness_endpoint(self):
        """Test readiness endpoint checks dependencies."""
        from flask import Flask
        from api.health_monitoring import add_health_endpoints
        
        app = Flask(__name__)
        add_health_endpoints(app)
        
        with app.test_client() as client:
            response = client.get("/health/ready")
            
            # Can be 200 or 503 depending on dependency status
            assert response.status_code in (200, 503)
            data = response.get_json()
            assert "status" in data


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestObservabilityIntegration:
    """Integration tests for observability stack."""
    
    def test_telemetry_to_logging_integration(self):
        """Test telemetry events flow to structured logging."""
        from api.telemetry import TelemetryEmitter
        
        emitter = TelemetryEmitter(service_name="integration_test", enable_console=False, enable_file=False)
        
        # This should not raise
        emitter.emit(
            event="test.integration",
            message="Integration test event",
        )
    
    def test_metrics_and_slo_integration(self):
        """Test metrics collection feeds SLO reporting."""
        from api.observability import MetricsCollector, emit_slo_report
        
        collector = MetricsCollector()
        
        # Simulate traffic
        for _ in range(100):
            collector.record_request("/api/v1/health", "GET", 200, 50)
        
        for _ in range(3):
            collector.record_request("/api/v1/simulate", "POST", 500, 1000, "Error")
        
        # Should not raise
        report = emit_slo_report()
        assert "timestamp" in report
    
    def test_health_check_with_metrics(self):
        """Test health checks report to metrics."""
        from api.health_monitoring import get_health_registry
        
        registry = get_health_registry()
        
        # Run health check
        result = registry.check_all()
        
        assert result is not None
        assert result.dependencies is not None


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in observability modules."""
    
    def test_telemetry_handles_none_values(self):
        """Test telemetry handles None values gracefully."""
        from api.telemetry import TelemetryContext
        
        ctx = TelemetryContext(
            request_id=None,
            user_id=None,
            service="test",
        )
        
        # Should not raise
        data = ctx.to_dict()
        # None values should be excluded from dict
        assert "request_id" not in data or data.get("request_id") is None
    
    def test_health_check_timeout_handling(self):
        """Test health checks handle slow dependencies."""
        from api.health_monitoring import HealthCheckRegistry, DependencyHealth, HealthStatus
        
        registry = HealthCheckRegistry()
        
        def slow_check() -> DependencyHealth:
            time.sleep(0.1)  # Simulate slow check
            return DependencyHealth(name="slow", status=HealthStatus.DEGRADED)
        
        registry.register("slow_service", slow_check)
        
        start = time.time()
        result = registry.check_all()
        duration = time.time() - start
        
        assert duration >= 0.1  # Confirm it waited
        assert result is not None
    
    def test_metrics_collector_thread_safety(self):
        """Test MetricsCollector handles concurrent access."""
        from api.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        def record_requests():
            for _ in range(100):
                collector.record_request("/test", "GET", 200, 10)
        
        threads = [threading.Thread(target=record_requests) for _ in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        summary = collector.get_summary()
        assert summary["total_requests"] >= 500
    
    def test_json_formatter_handles_exception_info(self):
        """Test JSONFormatter properly formats exception info."""
        from api.observability import JSONFormatter
        
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["level"] == "ERROR"


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfiguration:
    """Tests for configuration handling."""
    
    def test_alert_route_defaults(self):
        """Test AlertRoute default values."""
        from api.health_monitoring import AlertRoute, AlertSeverity
        
        route = AlertRoute(
            severity=AlertSeverity.MEDIUM,
            channels=["email"],
            escalation_minutes=30,
        )
        
        assert route.runbook_url is None  # default
    
    def test_sentry_config_sample_rates(self):
        """Test SentryConfig sample rate properties."""
        from api.sentry_integration import SentryConfig
        
        config = SentryConfig()
        
        assert 0.0 <= config.traces_sample_rate <= 1.0
        assert 0.0 <= config.profiles_sample_rate <= 1.0
    
    def test_environment_detection(self):
        """Test environment detection for configurations."""
        from api.sentry_integration import SentryConfig
        
        with patch.dict(os.environ, {"POLISIM_ENV": "production"}):
            config = SentryConfig()
            assert config.environment == "production"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
