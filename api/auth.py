"""
Authentication and authorization for POLISIM API
JWT-based authentication with role-based access control.
"""

import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional, Dict, Any

import jwt
from flask import request, jsonify, current_app
from sqlalchemy.orm import Session

from api.models import User, APIKey, UsageLog


# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


class AuthError(Exception):
    """Authentication error."""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code


def create_jwt_token(user_id: int, email: str, role: str) -> str:
    """
    Create JWT token for user.
    
    Args:
        user_id: User ID
        email: User email
        role: User role (user, researcher, admin)
        
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload
        
    Raises:
        AuthError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError('Token has expired', 401)
    except jwt.InvalidTokenError:
        raise AuthError('Invalid token', 401)


def get_token_from_request() -> Optional[str]:
    """
    Extract JWT token from request headers.
    
    Supports:
    - Authorization: Bearer <token>
    - X-API-Key: <api_key>
    
    Returns:
        Token string or None
    """
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    
    # Also check for API key header
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return api_key
    
    return None


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.
    
    Args:
        session: Database session
        email: User email
        password: User password
        
    Returns:
        User object if authenticated, None otherwise
    """
    user = session.query(User).filter_by(email=email).first()
    if user and user.check_password(password):
        if not user.is_active:
            raise AuthError('Account is disabled', 403)
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        session.commit()
        
        return user
    return None


def authenticate_api_key(session: Session, api_key: str) -> Optional[User]:
    """
    Authenticate user with API key.
    
    Args:
        session: Database session
        api_key: API key string
        
    Returns:
        User object if authenticated, None otherwise
    """
    key = session.query(APIKey).filter_by(key=api_key, is_active=True).first()
    if key:
        # Check expiration
        if key.expires_at and key.expires_at < datetime.now(timezone.utc):
            raise AuthError('API key has expired', 401)
        
        # Update last used
        key.last_used = datetime.now(timezone.utc)
        session.commit()
        
        return key.user
    return None


def require_auth(roles: Optional[list] = None):
    """
    Decorator to require authentication for endpoints.
    
    Args:
        roles: List of allowed roles (default: any authenticated user)
        
    Usage:
        @app.route('/api/protected')
        @require_auth()
        def protected_route():
            user = g.current_user
            return jsonify({"message": "Hello " + user.email})
        
        @app.route('/api/admin')
        @require_auth(roles=['admin'])
        def admin_route():
            return jsonify({"message": "Admin only"})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import g
            from api.database import get_db_session
            
            # Get token from request
            token = get_token_from_request()
            if not token:
                return jsonify({'error': 'No authentication token provided'}), 401
            
            session = get_db_session()
            
            try:
                # Try JWT token first
                if token.startswith('ps_'):
                    # API key
                    user = authenticate_api_key(session, token)
                    if not user:
                        return jsonify({'error': 'Invalid API key'}), 401
                else:
                    # JWT token
                    payload = decode_jwt_token(token)
                    user = session.query(User).filter_by(id=payload['user_id']).first()
                    if not user:
                        return jsonify({'error': 'User not found'}), 401
                
                # Check if user is active
                if not user.is_active:
                    return jsonify({'error': 'Account is disabled'}), 403
                
                # Check role if specified
                if roles and user.role not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Store user in Flask's g object
                g.current_user = user
                g.db_session = session
                
                # Log usage
                log_api_usage(session, user, request)
                
                # Call the actual endpoint
                return f(*args, **kwargs)
                
            except AuthError as e:
                return jsonify({'error': e.message}), e.status_code
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                session.close()
        
        return decorated_function
    return decorator


def log_api_usage(session: Session, user: User, request):
    """
    Log API usage for analytics and rate limiting.
    
    Args:
        session: Database session
        user: User making the request
        request: Flask request object
    """
    try:
        log = UsageLog(
            user_id=user.id,
            endpoint=request.path,
            method=request.method,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None,
        )
        session.add(log)
        session.commit()
    except Exception as e:
        # Don't fail request if logging fails
        current_app.logger.warning(f"Failed to log API usage: {e}")


def check_rate_limit(session: Session, user: User, api_key: Optional[APIKey] = None) -> bool:
    """
    Check if user has exceeded rate limit.
    
    Args:
        session: Database session
        user: User object
        api_key: API key object (if using API key auth)
        
    Returns:
        True if within rate limit, False otherwise
    """
    # Get rate limit (from API key or default)
    rate_limit = api_key.rate_limit if api_key else 1000
    
    # Count requests in last hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    request_count = session.query(UsageLog).filter(
        UsageLog.user_id == user.id,
        UsageLog.timestamp >= one_hour_ago
    ).count()
    
    return request_count < rate_limit


def require_rate_limit(f):
    """Decorator to enforce rate limiting."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        
        user = g.current_user
        session = g.db_session
        
        if not check_rate_limit(session, user):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        return f(*args, **kwargs)
    
    return decorated_function
