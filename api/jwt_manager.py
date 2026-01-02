"""
JWT Token Management with Refresh Token Support

Phase 6.2.4: Enhanced JWT token handling with:
- Access token generation and validation
- Refresh token rotation
- Token blacklisting
- Token metadata tracking
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import json
from pathlib import Path
import secrets
import hashlib

import jwt
from jwt import InvalidTokenError, ExpiredSignatureError, DecodeError

from api.secrets_manager import get_secrets_manager
from api.config_manager import get_config

# Use timezone.utc for Python compatibility
UTC = timezone.utc

logger = logging.getLogger(__name__)


@dataclass
class TokenMetadata:
    """Metadata for a JWT token."""
    token_id: str
    user_id: str
    token_type: str  # 'access' or 'refresh'
    issued_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(hours=24))
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'token_id': self.token_id,
            'user_id': self.user_id,
            'token_type': self.token_type,
            'issued_at': self.issued_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'revoked': self.revoked,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
        }


class TokenManager:
    """
    Manages JWT tokens including access and refresh tokens.
    
    Implements:
    - Token generation with metadata
    - Token validation and claims verification
    - Refresh token rotation
    - Token blacklisting
    - Automatic expiration
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize token manager."""
        self.config = get_config()
        self.secrets = get_secrets_manager()
        self.storage_path = Path(storage_path or Path(__file__).parent / '.token_metadata.json')
        
        # Load token metadata
        self.token_metadata: Dict[str, TokenMetadata] = {}
        self._load_token_metadata()
        
        logger.info("Token manager initialized")
    
    def _load_token_metadata(self):
        """Load token metadata from storage."""
        if not self.storage_path.exists():
            logger.debug("No token metadata file found, starting fresh")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for token_id, metadata_dict in data.items():
                    try:
                        metadata = TokenMetadata(
                            token_id=metadata_dict['token_id'],
                            user_id=metadata_dict['user_id'],
                            token_type=metadata_dict['token_type'],
                            issued_at=datetime.fromisoformat(metadata_dict['issued_at']),
                            expires_at=datetime.fromisoformat(metadata_dict['expires_at']),
                            revoked=metadata_dict.get('revoked', False),
                            revoked_at=datetime.fromisoformat(metadata_dict['revoked_at']) 
                                      if metadata_dict.get('revoked_at') else None,
                            ip_address=metadata_dict.get('ip_address'),
                            user_agent=metadata_dict.get('user_agent'),
                        )
                        self.token_metadata[token_id] = metadata
                    except Exception as e:
                        logger.warning(f"Failed to load token metadata {token_id}: {e}")
            
            logger.info(f"Loaded {len(self.token_metadata)} token metadata entries")
        except Exception as e:
            logger.error(f"Failed to load token metadata: {e}")
    
    def _save_token_metadata(self):
        """Save token metadata to storage."""
        try:
            data = {
                token_id: metadata.to_dict()
                for token_id, metadata in self.token_metadata.items()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Token metadata saved")
        except Exception as e:
            logger.error(f"Failed to save token metadata: {e}")
    
    def _cleanup_expired_tokens(self):
        """Remove expired tokens from metadata."""
        now = datetime.now(UTC)
        expired = [
            token_id for token_id, metadata in self.token_metadata.items()
            if metadata.expires_at < now
        ]
        
        for token_id in expired:
            del self.token_metadata[token_id]
            logger.debug(f"Cleaned up expired token: {token_id}")
    
    def generate_access_token(
        self,
        user_id: str,
        user_email: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        email: Optional[str] = None,
        roles: Optional[List[str]] = None,
    ) -> str:
        """
        Generate an access token with metadata tracking.
        
        Args:
            user_id: Unique user identifier
            user_email: User email address
            user_roles: List of user roles (e.g., ['admin', 'expert_reviewer'])
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit
            email: Alternative parameter name for user_email
            roles: Alternative parameter name for user_roles
            
        Returns:
            JWT access token
        """
        # Handle alternative parameter names for backwards compatibility
        if email is not None and user_email is None:
            user_email = email
        if roles is not None and user_roles is None:
            user_roles = roles
        
        # Validate required parameters
        if not user_email:
            raise ValueError("user_email (or email) is required")
        
        try:
            # Generate token ID for tracking
            token_id = secrets.token_urlsafe(32)
            
            # Get secrets and configuration
            jwt_secret = self.secrets.get('JWT_SECRET_KEY')
            if not jwt_secret:
                jwt_secret = self.config.jwt.secret_key
            
            # Calculate expiration
            expiration_hours = self.config.jwt.expiration_hours
            issued_at = datetime.now(UTC)
            expires_at = issued_at + timedelta(hours=expiration_hours)
            
            # Create claims
            claims = {
                'jti': token_id,  # JWT ID for tracking
                'sub': user_id,  # Subject (user ID)
                'email': user_email,
                'roles': user_roles or ['user'],
                'type': 'access',
                'iat': int(issued_at.timestamp()),
                'exp': int(expires_at.timestamp()),
            }
            
            # Encode token
            token = jwt.encode(
                claims,
                jwt_secret,
                algorithm=self.config.jwt.algorithm
            )
            
            # Store metadata
            metadata = TokenMetadata(
                token_id=token_id,
                user_id=user_id,
                token_type='access',
                issued_at=issued_at,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.token_metadata[token_id] = metadata
            self._save_token_metadata()
            
            logger.info(f"Generated access token for user {user_id} (token_id: {token_id})")
            return token
        
        except Exception as e:
            logger.error(f"Failed to generate access token: {e}")
            raise
    
    def generate_refresh_token(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Generate a refresh token for token renewal.
        
        Args:
            user_id: Unique user identifier
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit
            
        Returns:
            JWT refresh token
        """
        try:
            # Generate token ID for tracking
            token_id = secrets.token_urlsafe(32)
            
            # Get secrets
            refresh_secret = self.secrets.get('JWT_REFRESH_SECRET')
            if not refresh_secret:
                refresh_secret = self.config.jwt.refresh_secret_key
            
            # Calculate expiration
            refresh_days = self.config.jwt.refresh_expiration_days
            issued_at = datetime.now(UTC)
            expires_at = issued_at + timedelta(days=refresh_days)
            
            # Create claims
            claims = {
                'jti': token_id,
                'sub': user_id,
                'type': 'refresh',
                'iat': int(issued_at.timestamp()),
                'exp': int(expires_at.timestamp()),
            }
            
            # Encode token
            token = jwt.encode(
                claims,
                refresh_secret,
                algorithm=self.config.jwt.algorithm
            )
            
            # Store metadata
            metadata = TokenMetadata(
                token_id=token_id,
                user_id=user_id,
                token_type='refresh',
                issued_at=issued_at,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.token_metadata[token_id] = metadata
            self._save_token_metadata()
            
            logger.info(f"Generated refresh token for user {user_id} (token_id: {token_id})")
            return token
        
        except Exception as e:
            logger.error(f"Failed to generate refresh token: {e}")
            raise
    
    def validate_token(self, token: str, token_type: str = 'access') -> Dict[str, Any]:
        """
        Validate a token and return claims.
        
        Args:
            token: JWT token to validate
            token_type: Type of token ('access' or 'refresh')
            
        Returns:
            Token claims
            
        Raises:
            InvalidTokenError: If token is invalid
            ExpiredSignatureError: If token is expired
        """
        try:
            # Get appropriate secret
            if token_type == 'refresh':
                secret = self.secrets.get('JWT_REFRESH_SECRET')
                if not secret:
                    secret = self.config.jwt.refresh_secret_key
            else:
                secret = self.secrets.get('JWT_SECRET_KEY')
                if not secret:
                    secret = self.config.jwt.secret_key
            
            # Decode token
            decoded: Any = jwt.decode(
                token,
                secret,
                algorithms=[self.config.jwt.algorithm]
            )
            claims: Dict[str, Any] = decoded if isinstance(decoded, dict) else {}
            
            # Verify token type
            if claims.get('type') != token_type:
                raise InvalidTokenError(f"Expected {token_type} token, got {claims.get('type')}")
            
            # Check if token is revoked
            token_id = claims.get('jti')
            if token_id and token_id in self.token_metadata:
                metadata = self.token_metadata[token_id]
                if metadata.revoked:
                    raise InvalidTokenError("Token has been revoked")
            
            logger.debug(f"Validated token for user {claims.get('sub')} (jti: {token_id})")
            return claims
        
        except ExpiredSignatureError:
            logger.warning(f"Token has expired")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            raise InvalidTokenError(f"Token validation failed: {e}")
    
    def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        try:
            # Validate refresh token
            claims = self.validate_token(refresh_token, token_type='refresh')
            
            # Type assertions for required claims
            user_id: str = claims.get('sub')  # type: ignore[assignment]
            old_token_id: str = claims.get('jti')  # type: ignore[assignment]
            
            # Validate required claims
            if not user_id:
                raise ValueError("Refresh token missing user_id (sub claim)")
            if not old_token_id:
                raise ValueError("Refresh token missing token_id (jti claim)")
            
            # Get email from claims (stored during initial token generation)
            user_email = claims.get('email', 'unknown@example.com')
            if not isinstance(user_email, str):
                user_email = 'unknown@example.com'
            
            # Revoke old refresh token
            if old_token_id in self.token_metadata:
                self.token_metadata[old_token_id].revoked = True
                self.token_metadata[old_token_id].revoked_at = datetime.now(UTC)
            
            # Generate new tokens
            access_token = self.generate_access_token(
                user_id=user_id,
                user_email=user_email,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            new_refresh_token = self.generate_refresh_token(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            self._save_token_metadata()
            
            logger.info(f"Refreshed tokens for user {user_id}")
            return access_token, new_refresh_token
        
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (blacklist it).
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if revoked successfully
        """
        try:
            # Decode without verification to get jti
            unverified = jwt.decode(token, options={"verify_signature": False})
            token_id = unverified.get('jti')
            
            if token_id and token_id in self.token_metadata:
                self.token_metadata[token_id].revoked = True
                self.token_metadata[token_id].revoked_at = datetime.now(UTC)
                self._save_token_metadata()
                
                logger.info(f"Revoked token: {token_id}")
                return True
            
            logger.warning(f"Token not found in metadata: {token_id}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            raise
    
    def revoke_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a user (e.g., on logout or password change).
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of tokens revoked
        """
        try:
            revoked_count = 0
            now = datetime.now(UTC)
            
            for token_id, metadata in self.token_metadata.items():
                if metadata.user_id == user_id and not metadata.revoked:
                    metadata.revoked = True
                    metadata.revoked_at = now
                    revoked_count += 1
            
            if revoked_count > 0:
                self._save_token_metadata()
                logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            
            return revoked_count
        
        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {e}")
            raise
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token (without validation).
        
        Args:
            token: JWT token
            
        Returns:
            Token information including metadata
        """
        try:
            # Decode without verification
            claims = jwt.decode(token, options={"verify_signature": False})
            token_id = claims.get('jti')
            
            info = {'claims': claims}
            
            if token_id and token_id in self.token_metadata:
                metadata = self.token_metadata[token_id]
                info['metadata'] = metadata.to_dict()
            
            return info
        
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens from storage."""
        self._cleanup_expired_tokens()
        self._save_token_metadata()


# Global instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get or create global token manager."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
