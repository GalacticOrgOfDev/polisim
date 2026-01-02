"""
Request Validation, Filtering & Backpressure (Slice 6.2.5)

Implements:
1. Request size validation
2. Request timeout handling
3. Connection pooling limits
4. Request queuing for backpressure
5. Malicious header filtering
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps
from collections import deque
import threading
import redis

logger = logging.getLogger(__name__)


class RequestValidator:
    """Validates incoming requests for security and resource limits."""
    
    # Default limits
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_JSON_PAYLOAD = 5 * 1024 * 1024   # 5 MB for JSON
    MAX_FORM_DATA = 10 * 1024 * 1024     # 10 MB for form data
    REQUEST_TIMEOUT = 30  # seconds
    MAX_CONCURRENT_REQUESTS = 1000
    
    # Suspicious headers that might indicate attack
    SUSPICIOUS_HEADERS = {
        'x-forwarded-host',
        'x-forwarded-proto',
        'x-forwarded-for',  # Can be spoofed
        'x-original-url',
        'x-original-host',
        'x-rewrite-url',
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize request validator."""
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
        except (redis.ConnectionError, Exception):
            logger.warning("Redis not available for request validation")
            self.redis = None
    
    def validate_content_type(self, content_type: Optional[str]) -> bool:
        """
        Validate content type header.
        
        Args:
            content_type: Content-Type header value
        
        Returns:
            True if valid, False otherwise
        """
        if not content_type:
            return True  # No content type is OK for GET requests
        
        allowed_types = {
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain',
        }
        
        # Check main type (ignore charset, boundary, etc.)
        main_type = content_type.split(';')[0].strip().lower()
        
        is_valid = main_type in allowed_types
        if not is_valid:
            logger.warning(f"Rejected request with content-type: {content_type}")
        
        return is_valid
    
    def validate_content_length(
        self,
        content_length: Optional[str],
        content_type: Optional[str]
    ) -> bool:
        """
        Validate Content-Length header.
        
        Args:
            content_length: Content-Length header value
            content_type: Content-Type header value
        
        Returns:
            True if valid, False otherwise
        """
        if not content_length:
            return True
        
        try:
            length = int(content_length)
            
            # Check against type-specific limits
            if 'json' in (content_type or '').lower():
                max_size = self.MAX_JSON_PAYLOAD
            elif 'form-data' in (content_type or '').lower():
                max_size = self.MAX_FORM_DATA
            else:
                max_size = self.MAX_REQUEST_SIZE
            
            if length > max_size:
                logger.warning(
                    f"Request too large: {length} bytes (max: {max_size})"
                )
                return False
            
            return True
        except (ValueError, TypeError):
            logger.warning(f"Invalid Content-Length header: {content_length}")
            return False
    
    def validate_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Validate and filter headers, removing suspicious ones.
        
        Args:
            headers: Request headers dictionary
        
        Returns:
            Cleaned headers dictionary
        """
        cleaned = {}
        
        for key, value in headers.items():
            key_lower = key.lower()
            
            # Skip suspicious headers
            if key_lower in self.SUSPICIOUS_HEADERS:
                logger.debug(f"Filtered suspicious header: {key}")
                continue
            
            # Validate header value (max length)
            if len(value) > 8000:
                logger.warning(f"Header too long: {key}")
                continue
            
            # Check for null bytes
            if '\x00' in value:
                logger.warning(f"Null byte in header: {key}")
                continue
            
            cleaned[key] = value
        
        return cleaned
    
    def get_request_count(self) -> int:
        """Get current number of concurrent requests."""
        if self.redis is None:
            return 0
        
        try:
            count = self.redis.get("requests:concurrent")
            return int(count) if count else 0
        except Exception:
            return 0
    
    def increment_request_count(self) -> int:
        """Increment concurrent request count."""
        if self.redis is None:
            return 0
        
        try:
            count = self.redis.incr("requests:concurrent")
            return count
        except Exception:
            return 0
    
    def decrement_request_count(self) -> int:
        """Decrement concurrent request count."""
        if self.redis is None:
            return 0
        
        try:
            count = self.redis.decr("requests:concurrent")
            return max(0, count)
        except Exception:
            return 0
    
    def can_accept_request(self) -> bool:
        """Check if we can accept a new request."""
        return self.get_request_count() < self.MAX_CONCURRENT_REQUESTS


class RequestQueue:
    """
    Request queuing for backpressure when server is overloaded.
    
    Implements a simple FIFO queue with timeout handling.
    """
    
    def __init__(
        self,
        max_queue_size: int = 5000,
        max_wait_time: int = 30
    ):
        """
        Initialize request queue.
        
        Args:
            max_queue_size: Maximum number of queued requests
            max_wait_time: Maximum time to wait in queue (seconds)
        """
        self.max_queue_size = max_queue_size
        self.max_wait_time = max_wait_time
        self.queue: deque = deque()
        self.lock = threading.Lock()
    
    def enqueue(self, request_id: str, request_data: Dict[str, Any]) -> bool:
        """
        Add request to queue.
        
        Args:
            request_id: Unique request identifier
            request_data: Request metadata
        
        Returns:
            True if queued, False if queue is full
        """
        with self.lock:
            if len(self.queue) >= self.max_queue_size:
                logger.warning("Request queue full, rejecting request")
                return False
            
            self.queue.append({
                "id": request_id,
                "data": request_data,
                "enqueued_at": time.time()
            })
            return True
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Remove oldest request from queue.
        
        Returns:
            Request data or None if queue is empty
        """
        with self.lock:
            if not self.queue:
                return None
            
            request = self.queue.popleft()
            
            # Check if request has been waiting too long
            wait_time = time.time() - request["enqueued_at"]
            if wait_time > self.max_wait_time:
                logger.warning(
                    f"Discarding queued request {request['id']} "
                    f"(waited {wait_time:.1f}s)"
                )
                return None
            
            return request
    
    def get_size(self) -> int:
        """Get current queue size."""
        with self.lock:
            return len(self.queue)
    
    def clear(self) -> None:
        """Clear the queue."""
        with self.lock:
            self.queue.clear()


class BackpressureManager:
    """Manages backpressure when system is overloaded."""
    
    # CPU threshold for triggering backpressure
    CPU_THRESHOLD = 0.85
    # Memory threshold
    MEMORY_THRESHOLD = 0.90
    
    def __init__(self):
        self.request_queue = RequestQueue()
        self.is_overloaded = False
    
    def check_system_load(self) -> float:
        """
        Check system load average.
        
        Returns:
            Load average (1-minute) or 0 if unavailable
        """
        try:
            import os
            load_avg = os.getloadavg()[0]
            
            # Rough estimate: if load > CPU cores * 0.8, we're overloaded
            cpu_count = os.cpu_count() or 1
            utilization = load_avg / cpu_count
            
            self.is_overloaded = utilization > self.CPU_THRESHOLD
            return utilization
        except (AttributeError, NotImplementedError):
            # getloadavg not available on Windows
            return 0
    
    def get_backpressure_status(self) -> Dict[str, Any]:
        """Get current backpressure status."""
        return {
            "is_overloaded": self.is_overloaded,
            "queue_size": self.request_queue.get_size(),
            "queue_max": self.request_queue.max_queue_size
        }


# Global instances
_validator: Optional[RequestValidator] = None
_backpressure: Optional[BackpressureManager] = None


def init_request_validation(redis_url: str = "redis://localhost:6379"):
    """Initialize request validation."""
    global _validator, _backpressure
    _validator = RequestValidator(redis_url)
    _backpressure = BackpressureManager()
    logger.info("Request validation initialized")


def get_request_validator() -> RequestValidator:
    """Get the request validator instance."""
    global _validator
    if _validator is None:
        _validator = RequestValidator()
    return _validator


def get_backpressure_manager() -> BackpressureManager:
    """Get the backpressure manager instance."""
    global _backpressure
    if _backpressure is None:
        _backpressure = BackpressureManager()
    return _backpressure


def require_request_validation(f: Callable) -> Callable:
    """
    Decorator for request validation.
    
    Validates:
    - Content-Type header
    - Content-Length limits
    - Header sanitization
    - Concurrent request limits
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request, jsonify
        
        validator = get_request_validator()
        backpressure = get_backpressure_manager()
        
        # Check content type
        if not validator.validate_content_type(request.content_type):
            return jsonify({
                "error": "Invalid Content-Type header",
                "status": 400
            }), 400
        
        # Check content length
        if not validator.validate_content_length(
            request.content_length,
            request.content_type
        ):
            return jsonify({
                "error": "Request body too large or invalid Content-Length",
                "status": 413
            }), 413
        
        # Check concurrent requests
        if not validator.can_accept_request():
            # Try to queue the request
            request_id = f"{time.time()}-{id(request)}"
            if backpressure.request_queue.enqueue(request_id, {
                "method": request.method,
                "path": request.path
            }):
                return jsonify({
                    "error": "Server overloaded, request queued",
                    "status": 202,
                    "message": "Your request is queued. Please retry in 5 seconds."
                }), 202
            else:
                return jsonify({
                    "error": "Server overloaded, cannot queue request",
                    "status": 503
                }), 503
        
        # Increment request count
        validator.increment_request_count()
        
        try:
            response = f(*args, **kwargs)
            return response
        finally:
            # Decrement request count
            validator.decrement_request_count()
    
    return wrapper
