"""
Authentication Audit Logging

Phase 6.2.4: Tracks all authentication-related events:
- Login attempts (success and failure)
- Token generation
- Password changes
- Permission changes
- Token revocation
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

# Use timezone.utc for Python compatibility
UTC = timezone.utc

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_GENERATED = "token_generated"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_REFRESHED = "token_refreshed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    PERMISSION_CHANGED = "permission_changed"
    ROLE_CHANGED = "role_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    FAILED_LOGIN_LIMIT_EXCEEDED = "failed_login_limit_exceeded"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"


@dataclass
class AuditEvent:
    """Represents an authentication audit event."""
    event_type: AuditEventType
    user_id: Optional[str] = None
    username: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"  # 'success', 'failure'
    description: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'username': self.username,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'description': self.description,
            'details': self.details,
        }


class AuthAuditLogger:
    """
    Logs authentication and authorization events for compliance and security.
    
    Events tracked:
    - Login attempts (success/failure)
    - Token generation and revocation
    - Password changes
    - Permission and role changes
    - MFA events
    - Session lifecycle
    - Security violations (unauthorized access, rate limiting)
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            log_file: Path to audit log file (JSON format)
        """
        self.log_file = Path(log_file or Path(__file__).parent / '.auth_audit.json')
        self.events: List[AuditEvent] = []
        
        # Load existing events
        self._load_events()
        
        logger.info(f"Auth audit logger initialized (log file: {self.log_file})")
    
    def _load_events(self):
        """Load events from log file."""
        if not self.log_file.exists():
            logger.debug("No audit log file found, starting fresh")
            return
        
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
                for event_dict in data.get('events', []):
                    try:
                        event = AuditEvent(
                            event_type=AuditEventType(event_dict['event_type']),
                            user_id=event_dict.get('user_id'),
                            username=event_dict.get('username'),
                            timestamp=datetime.fromisoformat(event_dict['timestamp']),
                            ip_address=event_dict.get('ip_address'),
                            user_agent=event_dict.get('user_agent'),
                            status=event_dict.get('status', 'success'),
                            description=event_dict.get('description'),
                            details=event_dict.get('details', {}),
                        )
                        self.events.append(event)
                    except Exception as e:
                        logger.warning(f"Failed to load audit event: {e}")
            
            logger.info(f"Loaded {len(self.events)} audit events")
        except Exception as e:
            logger.error(f"Failed to load audit events: {e}")
    
    def _save_events(self):
        """Save events to log file."""
        try:
            data = {
                'events': [event.to_dict() for event in self.events[-1000:]],  # Keep last 1000
                'total_events': len(self.events),
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Audit events saved")
        except Exception as e:
            logger.error(f"Failed to save audit events: {e}")
    
    def log_event(self, event: AuditEvent):
        """
        Log an audit event.
        
        Args:
            event: Audit event to log
        """
        self.events.append(event)
        
        # Log to Python logger as well
        log_message = f"[{event.event_type.value}] user_id={event.user_id} status={event.status}"
        if event.description:
            log_message += f" - {event.description}"
        
        if event.status == "success":
            logger.info(log_message)
        else:
            logger.warning(log_message)
        
        self._save_events()
    
    def log_login_success(
        self,
        user_id: str,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log successful login."""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            description=f"User {username} logged in successfully",
        )
        self.log_event(event)
    
    def log_login_failure(
        self,
        username: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log failed login attempt."""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_FAILURE,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            status="failure",
            description=f"Login failed for user {username}: {reason}",
            details={'reason': reason},
        )
        self.log_event(event)
    
    def log_logout(
        self,
        user_id: str,
        username: str,
        ip_address: Optional[str] = None,
    ):
        """Log user logout."""
        event = AuditEvent(
            event_type=AuditEventType.LOGOUT,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            status="success",
            description=f"User {username} logged out",
        )
        self.log_event(event)
    
    def log_token_generated(
        self,
        user_id: str,
        token_type: str,
        token_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Log token generation.
        
        Args:
            user_id: User ID
            token_type: Type of token (access, refresh, etc.)
            token_id: Optional token ID for tracking
            ip_address: Client IP address
            user_agent: Client user agent string
        """
        event = AuditEvent(
            event_type=AuditEventType.TOKEN_GENERATED,
            user_id=user_id,
            ip_address=ip_address,
            status="success",
            description=f"Generated {token_type} token",
            details={
                'token_type': token_type,
                'token_id': token_id,
                'user_agent': user_agent,
            },
        )
        self.log_event(event)
    
    def log_token_revoked(
        self,
        user_id: Optional[str],
        token_id: str,
        reason: str = "User requested revocation",
        ip_address: Optional[str] = None,
    ):
        """Log token revocation."""
        event = AuditEvent(
            event_type=AuditEventType.TOKEN_REVOKED,
            user_id=user_id,
            ip_address=ip_address,
            status="success",
            description=f"Token revoked: {reason}",
            details={'token_id': token_id, 'reason': reason},
        )
        self.log_event(event)
    
    def log_password_changed(
        self,
        user_id: str,
        username: str,
        ip_address: Optional[str] = None,
    ):
        """Log password change."""
        event = AuditEvent(
            event_type=AuditEventType.PASSWORD_CHANGED,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            status="success",
            description=f"Password changed for user {username}",
        )
        self.log_event(event)
    
    def log_permission_changed(
        self,
        user_id: str,
        username: str,
        old_permissions: List[str],
        new_permissions: List[str],
        changed_by: str,
        ip_address: Optional[str] = None,
    ):
        """Log permission change."""
        event = AuditEvent(
            event_type=AuditEventType.PERMISSION_CHANGED,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            status="success",
            description=f"Permissions changed for user {username} by {changed_by}",
            details={
                'old_permissions': old_permissions,
                'new_permissions': new_permissions,
                'changed_by': changed_by,
            },
        )
        self.log_event(event)
    
    def log_role_changed(
        self,
        user_id: str,
        username: str,
        old_roles: List[str],
        new_roles: List[str],
        changed_by: str,
        ip_address: Optional[str] = None,
    ):
        """Log role change."""
        event = AuditEvent(
            event_type=AuditEventType.ROLE_CHANGED,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            status="success",
            description=f"Roles changed for user {username} by {changed_by}",
            details={
                'old_roles': old_roles,
                'new_roles': new_roles,
                'changed_by': changed_by,
            },
        )
        self.log_event(event)
    
    def log_failed_login_limit_exceeded(
        self,
        username: str,
        attempt_count: int,
        ip_address: Optional[str] = None,
    ):
        """Log when failed login limit is exceeded."""
        event = AuditEvent(
            event_type=AuditEventType.FAILED_LOGIN_LIMIT_EXCEEDED,
            username=username,
            ip_address=ip_address,
            status="failure",
            description=f"Failed login limit exceeded for user {username}",
            details={'attempt_count': attempt_count},
        )
        self.log_event(event)
    
    def log_unauthorized_access_attempt(
        self,
        user_id: Optional[str],
        username: Optional[str],
        resource: str,
        required_permission: str,
        ip_address: Optional[str] = None,
    ):
        """Log unauthorized access attempt."""
        event = AuditEvent(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            status="failure",
            description=f"Unauthorized access attempt to {resource}",
            details={
                'resource': resource,
                'required_permission': required_permission,
            },
        )
        self.log_event(event)
    
    def get_user_events(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[AuditEvent]:
        """Get audit events for a specific user."""
        user_events = [e for e in self.events if e.user_id == user_id]
        return user_events[-limit:]
    
    def get_events_by_user(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[AuditEvent]:
        """
        Get audit events for a specific user.
        
        Alias for get_user_events for backwards compatibility.
        """
        return self.get_user_events(user_id, limit)
    
    def get_events_by_type(
        self,
        event_type: AuditEventType,
        limit: int = 50,
    ) -> List[AuditEvent]:
        """Get audit events of a specific type."""
        type_events = [e for e in self.events if e.event_type == event_type]
        return type_events[-limit:]
    
    def get_recent_events(self, limit: int = 50) -> List[AuditEvent]:
        """Get recent audit events."""
        return self.events[-limit:]


# Global instance
_auth_audit_logger: Optional[AuthAuditLogger] = None


def get_auth_audit_logger() -> AuthAuditLogger:
    """Get or create global auth audit logger."""
    global _auth_audit_logger
    if _auth_audit_logger is None:
        _auth_audit_logger = AuthAuditLogger()
    return _auth_audit_logger
