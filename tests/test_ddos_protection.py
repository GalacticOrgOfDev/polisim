"""
Test cases for DDoS protection and resilience (Slice 6.2.5)

Tests for:
- Rate limiting
- Circuit breaker
- Request validation
- Backpressure/queuing
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from api.rate_limiter import RateLimiter, RateLimitError, init_rate_limiter, require_rate_limit
from api.circuit_breaker import (
    CircuitBreaker, CircuitBreakerError, CircuitState,
    CircuitBreakerManager, with_circuit_breaker, init_circuit_breakers
)
from api.request_validator import (
    RequestValidator, RequestQueue, BackpressureManager,
    init_request_validation, get_request_validator, get_backpressure_manager
)


@pytest.fixture(autouse=True)
def cleanup_circuit_breaker_state():
    """Clean up circuit breaker in-memory state between tests."""
    yield
    # Clear in-memory state after each test to prevent pollution
    CircuitBreaker._in_memory_state.clear()


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter()
        assert limiter is not None
    
    def test_ip_rate_limit_allowed(self):
        """Test allowed IP rate limit."""
        limiter = RateLimiter()
        if not limiter._is_redis_available():
            pytest.skip("Redis not available")
        
        # First request should be allowed
        allowed, retry_after = limiter.check_ip_rate_limit(
            "192.168.1.1",
            endpoint="test",
            limit=5,
            window=60
        )
        assert allowed is True
        assert retry_after is None
    
    def test_ip_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        limiter = RateLimiter()
        if not limiter._is_redis_available():
            pytest.skip("Redis not available")
        
        # Make requests up to limit
        for i in range(5):
            limiter.check_ip_rate_limit(
                "192.168.1.2",
                endpoint="test",
                limit=5,
                window=60
            )
        
        # Next request should fail
        with pytest.raises(RateLimitError) as exc_info:
            limiter.check_ip_rate_limit(
                "192.168.1.2",
                endpoint="test",
                limit=5,
                window=60
            )
        
        assert exc_info.value.retry_after is not None
    
    def test_ip_blocking(self):
        """Test IP blocking functionality."""
        limiter = RateLimiter()
        if not limiter._is_redis_available():
            pytest.skip("Redis not available")
        
        ip = "192.168.1.3"
        assert not limiter.is_ip_blocked(ip)
        
        # Block the IP
        limiter.block_ip(ip, duration=60, reason="Test block")
        assert limiter.is_ip_blocked(ip)
        
        # Unblock the IP
        limiter.unblock_ip(ip)
        assert not limiter.is_ip_blocked(ip)
    
    def test_user_rate_limit(self):
        """Test user-based rate limiting."""
        limiter = RateLimiter()
        if not limiter._is_redis_available():
            pytest.skip("Redis not available")
        
        # Users should have higher limit
        for i in range(10):
            allowed, _ = limiter.check_user_rate_limit(
                "user123",
                endpoint="test",
                limit=100,
                window=3600
            )
            assert allowed is True


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_init(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker(
            "test_service",
            failure_threshold=3,
            recovery_timeout=60
        )
        assert breaker.service_name == "test_service"
        assert breaker._get_state() == CircuitState.CLOSED
    
    def test_circuit_breaker_closed_success(self):
        """Test successful call with circuit closed."""
        breaker = CircuitBreaker(
            "test_service",
            failure_threshold=3
        )
        
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        assert result == "success"
    
    def test_circuit_breaker_failure_threshold(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(
            "test_service_failure_threshold",
            failure_threshold=3,
            expected_exception=ValueError
        )
        
        def failing_func():
            raise ValueError("Test error")
        
        # First few failures don't open circuit
        for i in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # After threshold, circuit should open
        with pytest.raises(CircuitBreakerError):
            breaker.call(failing_func)
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit recovery from HALF_OPEN state."""
        breaker = CircuitBreaker(
            "test_service_half_open",
            failure_threshold=1,
            recovery_timeout=0,  # Immediate recovery attempt
            expected_exception=ValueError
        )
        
        # Force circuit open
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Test")))
        
        # Wait for recovery attempt
        time.sleep(0.1)
        
        # Successful call should close circuit
        def success_func():
            return "recovered"
        
        result = breaker.call(success_func)
        assert result == "recovered"
        assert breaker._get_state() == CircuitState.CLOSED
    
    def test_circuit_breaker_manager(self):
        """Test circuit breaker manager."""
        breaker = CircuitBreakerManager.register_breaker(
            "test_service_2",
            failure_threshold=5
        )
        
        assert breaker is not None
        retrieved = CircuitBreakerManager.get_breaker("test_service_2")
        assert retrieved is not None
    
    def test_with_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        call_count = 0
        
        @with_circuit_breaker(
            "test_service_3",
            failure_threshold=1
        )
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 1


class TestRequestValidator:
    """Test request validation functionality."""
    
    def test_content_type_validation(self):
        """Test content type validation."""
        validator = RequestValidator()
        
        # Valid types
        assert validator.validate_content_type("application/json")
        assert validator.validate_content_type("text/plain")
        assert validator.validate_content_type("application/json; charset=utf-8")
        
        # Invalid types
        assert not validator.validate_content_type("application/x-executable")
    
    def test_content_length_validation(self):
        """Test content length validation."""
        validator = RequestValidator()
        
        # Valid size
        assert validator.validate_content_length(
            "1000",
            "application/json"
        )
        
        # Too large
        assert not validator.validate_content_length(
            str(RequestValidator.MAX_JSON_PAYLOAD + 1),
            "application/json"
        )
    
    def test_header_validation(self):
        """Test header filtering."""
        validator = RequestValidator()
        
        headers = {
            "content-type": "application/json",
            "x-forwarded-for": "8.8.8.8",  # Suspicious
            "authorization": "Bearer token",
            "x-custom": "value"
        }
        
        cleaned = validator.validate_headers(headers)
        
        # Suspicious header should be removed
        assert "x-forwarded-for" not in cleaned
        # Valid headers should remain
        assert "content-type" in cleaned
        assert "authorization" in cleaned


class TestRequestQueue:
    """Test request queuing functionality."""
    
    def test_queue_enqueue_dequeue(self):
        """Test basic enqueue/dequeue."""
        queue = RequestQueue(max_queue_size=100)
        
        # Enqueue request
        success = queue.enqueue("req1", {"method": "POST"})
        assert success is True
        assert queue.get_size() == 1
        
        # Dequeue request
        request = queue.dequeue()
        assert request is not None
        assert request["id"] == "req1"
        assert queue.get_size() == 0
    
    def test_queue_full(self):
        """Test queue full condition."""
        queue = RequestQueue(max_queue_size=2)
        
        # Fill queue
        assert queue.enqueue("req1", {})
        assert queue.enqueue("req2", {})
        
        # Queue full
        assert not queue.enqueue("req3", {})
    
    def test_queue_timeout(self):
        """Test request timeout in queue."""
        queue = RequestQueue(
            max_queue_size=100,
            max_wait_time=1  # 1 second timeout
        )
        
        # Enqueue request
        queue.enqueue("req1", {})
        
        # Wait for timeout
        time.sleep(1.5)
        
        # Request should be discarded
        request = queue.dequeue()
        assert request is None


class TestBackpressureManager:
    """Test backpressure management."""
    
    def test_backpressure_init(self):
        """Test backpressure manager initialization."""
        bp = BackpressureManager()
        assert bp.is_overloaded is False
        assert bp.request_queue is not None
    
    def test_backpressure_status(self):
        """Test backpressure status reporting."""
        bp = BackpressureManager()
        
        status = bp.get_backpressure_status()
        assert "is_overloaded" in status
        assert "queue_size" in status
        assert "queue_max" in status


class TestDDoSScenarios:
    """Integration tests for DDoS protection scenarios."""
    
    def test_rate_limit_with_multiple_ips(self):
        """Test rate limiting with multiple IP addresses."""
        limiter = RateLimiter()
        if not limiter._is_redis_available():
            pytest.skip("Redis not available")
        
        # Different IPs should have independent limits
        for i in range(3):
            allowed, _ = limiter.check_ip_rate_limit(
                f"192.168.1.{i}",
                limit=10,
                window=60
            )
            assert allowed is True
    
    def test_circuit_breaker_fallback(self):
        """Test circuit breaker with fallback function."""
        fallback_called = False
        
        def fallback_handler(*args, **kwargs):
            nonlocal fallback_called
            fallback_called = True
            return {"cached": True}
        
        @with_circuit_breaker(
            "test_service_4",
            failure_threshold=1,
            fallback=fallback_handler
        )
        def unreliable_service():
            raise Exception("Service down")
        
        # Trigger circuit breaker
        try:
            unreliable_service()
        except:
            pass
        
        # Fallback should be used
        result = unreliable_service()
        assert result["cached"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
