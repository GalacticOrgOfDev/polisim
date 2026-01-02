"""
Circuit Breaker Pattern for Resilience (Slice 6.2.5)

Protects the API from cascading failures by:
1. Monitoring external service health (CBO scraper, database)
2. Opening circuit when service fails
3. Returning cached/fallback responses during outage
4. Attempting recovery with exponential backoff
5. Logging failures for monitoring
"""

import logging
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, Any, Dict
from functools import wraps
import redis

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Service failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open."""
    def __init__(self, service_name: str, message: str = None):
        self.service_name = service_name
        self.message = message or f"Circuit breaker open for {service_name}"
        super().__init__(self.message)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation with Redis state management.
    
    Monitors external services and protects against cascading failures.
    Falls back to in-memory state when Redis is unavailable.
    """
    
    # In-memory state for testing/fallback when Redis unavailable
    _in_memory_state: Dict[str, Dict[str, Any]] = {}
    
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        redis_url: str = "redis://localhost:6379"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            service_name: Name of service being protected
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that counts as failure
            redis_url: Redis connection URL for state management
        """
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        # Initialize in-memory state
        if service_name not in self._in_memory_state:
            self._in_memory_state[service_name] = {
                'state': CircuitState.CLOSED.value,
                'failures': 0,
                'last_failure_time': None,
            }
        
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
        except (redis.ConnectionError, Exception):
            logger.warning(f"Redis not available for circuit breaker {service_name}, using in-memory state")
            self.redis = None
    
    def _get_state(self) -> CircuitState:
        """Get current circuit state from Redis or in-memory."""
        if self.redis is not None:
            try:
                state = self.redis.get(f"circuit:{self.service_name}:state")
                if state:
                    return CircuitState(state)
                return CircuitState.CLOSED
            except Exception as e:
                logger.error(f"Error getting circuit state from Redis: {e}")
        
        # In-memory fallback
        if self.service_name in self._in_memory_state:
            state_str = self._in_memory_state[self.service_name]['state']
            try:
                return CircuitState(state_str)
            except ValueError:
                return CircuitState.CLOSED
        return CircuitState.CLOSED
    
    def _set_state(self, state: CircuitState) -> None:
        """Set circuit state in Redis or in-memory."""
        # Always update in-memory state
        if self.service_name not in self._in_memory_state:
            self._in_memory_state[self.service_name] = {
                'state': CircuitState.CLOSED.value,
                'failures': 0,
                'last_failure_time': None,
            }
        self._in_memory_state[self.service_name]['state'] = state.value
        
        # Also update Redis if available
        if self.redis is not None:
            try:
                self.redis.set(f"circuit:{self.service_name}:state", state.value)
            except Exception as e:
                logger.error(f"Error setting circuit state in Redis: {e}")
        
        logger.info(f"Circuit breaker {self.service_name} state: {state.value}")
    
    def _get_failure_count(self) -> int:
        """Get current failure count from Redis or in-memory."""
        if self.redis is not None:
            try:
                count = self.redis.get(f"circuit:{self.service_name}:failures")
                return int(count) if count else 0
            except Exception as e:
                logger.error(f"Error getting failure count from Redis: {e}")
        
        # In-memory fallback
        if self.service_name in self._in_memory_state:
            return self._in_memory_state[self.service_name].get('failures', 0)
        return 0
    
    def _increment_failures(self) -> int:
        """Increment failure count and return new count."""
        # Ensure in-memory state exists
        if self.service_name not in self._in_memory_state:
            self._in_memory_state[self.service_name] = {
                'state': CircuitState.CLOSED.value,
                'failures': 0,
                'last_failure_time': None,
            }
        
        # Update in-memory
        self._in_memory_state[self.service_name]['failures'] += 1
        count = self._in_memory_state[self.service_name]['failures']
        self._in_memory_state[self.service_name]['last_failure_time'] = datetime.now()
        
        # Also update Redis if available
        if self.redis is not None:
            try:
                key = f"circuit:{self.service_name}:failures"
                count = self.redis.incr(key)
                # Reset after 24 hours
                self.redis.expire(key, 86400)
            except Exception as e:
                logger.error(f"Error incrementing failures in Redis: {e}")
        
        return count
    
    def _reset_failures(self) -> None:
        """Reset failure count in Redis and in-memory."""
        # Reset in-memory
        if self.service_name in self._in_memory_state:
            self._in_memory_state[self.service_name]['failures'] = 0
            self._in_memory_state[self.service_name]['last_failure_time'] = None
        
        # Reset Redis if available
        if self.redis is not None:
            try:
                self.redis.delete(f"circuit:{self.service_name}:failures")
            except Exception as e:
                logger.error(f"Error resetting failures in Redis: {e}")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.redis is None:
            return True
        
        try:
            last_failure = self.redis.get(f"circuit:{self.service_name}:last_failure")
            if not last_failure:
                return True
            
            last_failure_time = datetime.fromisoformat(last_failure)
            elapsed = (datetime.utcnow() - last_failure_time).total_seconds()
            return elapsed >= self.recovery_timeout
        except Exception:
            return True
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result or cached fallback
        
        Raises:
            CircuitBreakerError: If circuit is open
        """
        state = self._get_state()
        
        if state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._set_state(CircuitState.HALF_OPEN)
                logger.info(f"Circuit breaker {self.service_name} attempting reset")
            else:
                raise CircuitBreakerError(
                    self.service_name,
                    f"Circuit breaker open. Retry in {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset if in HALF_OPEN
            if state == CircuitState.HALF_OPEN:
                self._set_state(CircuitState.CLOSED)
                self._reset_failures()
                logger.info(f"Circuit breaker {self.service_name} recovered")
            
            return result
            
        except self.expected_exception as e:
            failures = self._increment_failures()
            
            if self.redis:
                try:
                    self.redis.set(
                        f"circuit:{self.service_name}:last_failure",
                        datetime.utcnow().isoformat()
                    )
                except Exception:
                    pass
            
            logger.warning(
                f"Service {self.service_name} failed "
                f"(failures: {failures}/{self.failure_threshold}): {e}"
            )
            
            if failures > self.failure_threshold:
                self._set_state(CircuitState.OPEN)
                raise CircuitBreakerError(self.service_name) from e
            else:
                # Still allow requests but track failures
                raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        state = self._get_state()
        
        return {
            "service_name": self.service_name,
            "state": state.value,
            "failure_count": self._get_failure_count(),
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


class CircuitBreakerManager:
    """Manages multiple circuit breakers for different services."""
    
    _breakers: Dict[str, CircuitBreaker] = {}
    
    @classmethod
    def register_breaker(
        cls,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        redis_url: str = "redis://localhost:6379"
    ) -> CircuitBreaker:
        """Register a new circuit breaker."""
        if service_name not in cls._breakers:
            cls._breakers[service_name] = CircuitBreaker(
                service_name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                redis_url=redis_url
            )
        return cls._breakers[service_name]
    
    @classmethod
    def get_breaker(cls, service_name: str) -> Optional[CircuitBreaker]:
        """Get a registered circuit breaker."""
        return cls._breakers.get(service_name)
    
    @classmethod
    def get_all_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {
            name: breaker.get_status()
            for name, breaker in cls._breakers.items()
        }


def with_circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    fallback: Optional[Callable] = None
):
    """
    Decorator for circuit breaker protection.
    
    Args:
        service_name: Name of service being protected
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before recovery attempt
        fallback: Function to call if circuit is open
    """
    def decorator(f):
        breaker = CircuitBreakerManager.register_breaker(
            service_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return breaker.call(f, *args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker triggered: {e}")
                
                if fallback:
                    logger.info(f"Using fallback for {service_name}")
                    return fallback(*args, **kwargs)
                else:
                    return {
                        "error": f"Service temporarily unavailable",
                        "service": service_name,
                        "status": 503
                    }
        
        # Attach breaker reference for testing
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Pre-configured circuit breakers for common services
def init_circuit_breakers(redis_url: str = "redis://localhost:6379"):
    """Initialize circuit breakers for all external services."""
    
    # CBO data scraper
    CircuitBreakerManager.register_breaker(
        "cbo_scraper",
        failure_threshold=3,
        recovery_timeout=300,  # 5 minutes
        redis_url=redis_url
    )
    
    # Database
    CircuitBreakerManager.register_breaker(
        "database",
        failure_threshold=5,
        recovery_timeout=60,
        redis_url=redis_url
    )
    
    # External API calls
    CircuitBreakerManager.register_breaker(
        "external_api",
        failure_threshold=5,
        recovery_timeout=120,
        redis_url=redis_url
    )
    
    logger.info("Circuit breakers initialized")
