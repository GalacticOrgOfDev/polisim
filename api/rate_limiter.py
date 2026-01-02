"""
Rate Limiting & DDoS Protection (Slice 6.2.5)

Implements multi-layer rate limiting to protect the API from abuse:
1. Per-IP rate limiting (global)
2. Per-user rate limiting (authenticated users)
3. Per-endpoint rate limiting
4. IP blocking for repeated violations
5. Progressive backoff strategies
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps
import redis

# Setup logging
logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


class RateLimiter:
    """
    Advanced rate limiter with Redis backend.
    
    Supports:
    - Per-IP rate limiting
    - Per-user rate limiting
    - Per-endpoint rate limiting
    - IP blocking
    - Progressive backoff
    - Metrics tracking
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize rate limiter with Redis connection."""
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info(f"Rate limiter initialized with Redis: {redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    def _is_redis_available(self) -> bool:
        """Check if Redis is available."""
        if self.redis is None:
            logger.warning("Redis not available, rate limiting disabled")
            return False
        try:
            self.redis.ping()
            return True
        except redis.ConnectionError:
            logger.warning("Redis connection lost, rate limiting disabled")
            return False
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        endpoint: str = "unknown"
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if a request is within the rate limit.
        
        Args:
            key: Unique identifier (e.g., IP address or user ID)
            limit: Number of requests allowed
            window: Time window in seconds
            endpoint: API endpoint for logging
        
        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
            retry_after is the number of seconds to wait before retrying
        
        Raises:
            RateLimitError: If rate limit exceeded
        """
        if not self._is_redis_available():
            return True, None
        
        try:
            rate_key = f"ratelimit:{key}"
            count = self.redis.incr(rate_key)
            
            # Set expiry on first request
            if count == 1:
                self.redis.expire(rate_key, window)
            
            # Check if limit exceeded
            if count > limit:
                ttl = self.redis.ttl(rate_key)
                logger.warning(
                    f"Rate limit exceeded for {key} on {endpoint} "
                    f"(count: {count}/{limit}, retry in: {ttl}s)"
                )
                raise RateLimitError(
                    f"Rate limit exceeded. Allowed: {limit} requests per {window}s",
                    retry_after=max(1, ttl)
                )
            
            return True, None
            
        except redis.RedisError as e:
            logger.error(f"Redis error during rate limit check: {e}")
            # Fail open - allow request if Redis fails
            return True, None
    
    def check_ip_rate_limit(
        self,
        ip_address: str,
        endpoint: str = "api",
        limit: int = 100,
        window: int = 60
    ) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit for an IP address.
        
        Args:
            ip_address: Client IP address
            endpoint: API endpoint name
            limit: Requests per window (default: 100/min)
            window: Time window in seconds (default: 60s)
        
        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
        """
        key = f"ip:{ip_address}:{endpoint}"
        return self.check_rate_limit(key, limit, window, f"IP:{ip_address}")
    
    def check_user_rate_limit(
        self,
        user_id: str,
        endpoint: str = "api",
        limit: int = 1000,
        window: int = 3600
    ) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit for an authenticated user.
        
        Users get higher limits than anonymous IPs.
        
        Args:
            user_id: Authenticated user ID
            endpoint: API endpoint name
            limit: Requests per window (default: 1000/hour)
            window: Time window in seconds (default: 3600s)
        
        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
        """
        key = f"user:{user_id}:{endpoint}"
        return self.check_rate_limit(key, limit, window, f"User:{user_id}")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP is currently blocked."""
        if not self._is_redis_available():
            return False
        
        try:
            return self.redis.exists(f"blocked:{ip_address}") > 0
        except redis.RedisError:
            return False
    
    def block_ip(
        self,
        ip_address: str,
        duration: int = 3600,
        reason: str = "Rate limit violation"
    ) -> None:
        """
        Temporarily block an IP address.
        
        Args:
            ip_address: IP to block
            duration: Block duration in seconds (default: 1 hour)
            reason: Reason for blocking
        """
        if not self._is_redis_available():
            return
        
        try:
            key = f"blocked:{ip_address}"
            self.redis.setex(
                key,
                duration,
                json.dumps({
                    "reason": reason,
                    "blocked_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(seconds=duration)).isoformat()
                })
            )
            logger.warning(f"IP {ip_address} blocked for {duration}s: {reason}")
        except redis.RedisError as e:
            logger.error(f"Failed to block IP {ip_address}: {e}")
    
    def unblock_ip(self, ip_address: str) -> None:
        """Unblock an IP address."""
        if not self._is_redis_available():
            return
        
        try:
            self.redis.delete(f"blocked:{ip_address}")
            logger.info(f"IP {ip_address} unblocked")
        except redis.RedisError as e:
            logger.error(f"Failed to unblock IP {ip_address}: {e}")
    
    def get_ip_status(self, ip_address: str) -> Dict[str, Any]:
        """Get detailed rate limit status for an IP."""
        if not self._is_redis_available():
            return {"status": "unavailable"}
        
        try:
            status = {
                "ip_address": ip_address,
                "is_blocked": self.is_ip_blocked(ip_address),
                "endpoints": {}
            }
            
            # Check status for common endpoints
            for endpoint in ["simulate", "scenarios", "health"]:
                key = f"ip:{ip_address}:{endpoint}"
                count = self.redis.get(key)
                ttl = self.redis.ttl(key)
                
                status["endpoints"][endpoint] = {
                    "count": int(count) if count else 0,
                    "ttl_seconds": max(0, ttl) if ttl else 0
                }
            
            return status
        except redis.RedisError as e:
            logger.error(f"Failed to get IP status: {e}")
            return {"status": "error", "message": str(e)}
    
    def reset_limits(self, key_pattern: str = "*") -> int:
        """
        Reset rate limit counters matching a pattern.
        
        Args:
            key_pattern: Redis key pattern (default: "*" = all)
        
        Returns:
            Number of keys deleted
        """
        if not self._is_redis_available():
            return 0
        
        try:
            keys = self.redis.keys(f"ratelimit:{key_pattern}")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Reset rate limits for {deleted} keys")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.error(f"Failed to reset limits: {e}")
            return 0


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def init_rate_limiter(redis_url: str = "redis://localhost:6379") -> RateLimiter:
    """Initialize the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = RateLimiter(redis_url)
    return _rate_limiter


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def require_rate_limit(
    endpoint: str = "api",
    ip_limit: int = 100,
    ip_window: int = 60,
    user_limit: int = 1000,
    user_window: int = 3600
):
    """
    Decorator for rate limiting Flask endpoints.
    
    Args:
        endpoint: Endpoint name for logging
        ip_limit: Anonymous IP request limit
        ip_window: IP rate limit window (seconds)
        user_limit: Authenticated user request limit
        user_window: User rate limit window (seconds)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request as flask_request
            
            limiter = get_rate_limiter()
            ip_address = flask_request.remote_addr or "unknown"
            
            # Check if IP is blocked
            if limiter.is_ip_blocked(ip_address):
                return {
                    "error": "IP address blocked due to abuse",
                    "status": 429
                }, 429
            
            # Get user ID if authenticated
            user_id = getattr(flask_request, "user_id", None)
            
            try:
                if user_id:
                    # Authenticated user - higher limit
                    allowed, retry_after = limiter.check_user_rate_limit(
                        user_id, endpoint, user_limit, user_window
                    )
                else:
                    # Anonymous - stricter limit
                    allowed, retry_after = limiter.check_ip_rate_limit(
                        ip_address, endpoint, ip_limit, ip_window
                    )
                
                # Proceed with request
                response = f(*args, **kwargs)
                return response
                
            except RateLimitError as e:
                # After 5 violations in 5 minutes, block the IP
                violation_key = f"violations:{ip_address}"
                violations = int(limiter.redis.get(violation_key) or 0) if limiter._is_redis_available() else 0
                violations += 1
                
                if limiter._is_redis_available():
                    limiter.redis.setex(violation_key, 300, str(violations))
                
                if violations >= 5:
                    limiter.block_ip(ip_address, duration=3600, reason="Multiple rate limit violations")
                
                response = {
                    "error": e.message,
                    "status": 429,
                    "retry_after": e.retry_after
                }
                headers = {}
                if e.retry_after:
                    headers["Retry-After"] = str(e.retry_after)
                
                return response, 429, headers
        
        return decorated_function
    return decorator
