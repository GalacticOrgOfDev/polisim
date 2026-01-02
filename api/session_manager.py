"""
Secure Session Management

Phase 6.2.4: Manages user sessions with:
- Session creation and validation
- Session expiration
- Concurrent session limits
- Session security (CSRF protection, secure cookies)
"""

import logging
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Use timezone.utc for Python compatibility
UTC = timezone.utc

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Represents a user session."""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=30))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    csrf_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    is_active: bool = True
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(UTC) > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if session is valid (not expired and active)."""
        return self.is_active and not self.is_expired()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'csrf_token': self.csrf_token,
            'is_active': self.is_active,
        }


class SessionManager:
    """
    Manages user sessions for web applications.
    
    Features:
    - Session creation with unique ID
    - Session validation and expiration
    - CSRF token generation
    - Concurrent session tracking
    - Session termination
    """
    
    def __init__(
        self,
        session_timeout_minutes: int = 30,
        max_concurrent_sessions: int = 5,
        storage_file: Optional[str] = None,
    ):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: Session timeout in minutes
            max_concurrent_sessions: Maximum concurrent sessions per user
            storage_file: Path to session storage file
        """
        self.session_timeout_minutes = session_timeout_minutes
        self.max_concurrent_sessions = max_concurrent_sessions
        self.storage_file = Path(storage_file or Path(__file__).parent / '.sessions.json')
        
        # In-memory session storage
        self.sessions: Dict[str, Session] = {}
        
        # Load existing sessions
        self._load_sessions()
        
        logger.info(
            f"Session manager initialized "
            f"(timeout: {session_timeout_minutes}min, max_sessions: {max_concurrent_sessions})"
        )
    
    def _load_sessions(self):
        """Load sessions from storage."""
        if not self.storage_file.exists():
            logger.debug("No session storage file found")
            return
        
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                for session_id, session_dict in data.items():
                    try:
                        session = Session(
                            session_id=session_dict['session_id'],
                            user_id=session_dict['user_id'],
                            created_at=datetime.fromisoformat(session_dict['created_at']),
                            last_activity=datetime.fromisoformat(session_dict['last_activity']),
                            expires_at=datetime.fromisoformat(session_dict['expires_at']),
                            ip_address=session_dict.get('ip_address'),
                            user_agent=session_dict.get('user_agent'),
                            csrf_token=session_dict.get('csrf_token'),
                            is_active=session_dict.get('is_active', True),
                        )
                        # Only load non-expired sessions
                        if not session.is_expired():
                            self.sessions[session_id] = session
                    except Exception as e:
                        logger.warning(f"Failed to load session {session_id}: {e}")
            
            logger.info(f"Loaded {len(self.sessions)} sessions")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    def _save_sessions(self):
        """Save sessions to storage."""
        try:
            data = {
                session_id: session.to_dict()
                for session_id, session in self.sessions.items()
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Sessions saved")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired:
            del self.sessions[session_id]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired sessions")
    
    def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session ID of the newly created session
        """
        # Check concurrent session limit
        user_sessions = [
            s for s in self.sessions.values()
            if s.user_id == user_id and s.is_valid()
        ]
        
        if len(user_sessions) >= self.max_concurrent_sessions:
            # Terminate oldest session
            oldest = min(user_sessions, key=lambda s: s.created_at)
            logger.info(
                f"Terminating oldest session for user {user_id} "
                f"(new session limit reached)"
            )
            self.terminate_session(oldest.session_id)
        
        # Generate session ID
        session_id = secrets.token_urlsafe(32)
        
        # Create session
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=self.session_timeout_minutes),
            ip_address=ip_address,
            user_agent=user_agent,
            csrf_token=secrets.token_urlsafe(32),
            is_active=True,
        )
        
        self.sessions[session_id] = session
        self._save_sessions()
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Session]:
        """
        Validate a session and return it if valid.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session if valid, None otherwise
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        session = self.sessions.get(session_id)
        
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        if not session.is_valid():
            logger.warning(f"Session is invalid: {session_id}")
            return None
        
        # Update activity
        session.update_activity()
        self._save_sessions()
        
        return session
    
    def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a session (logout).
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if terminated successfully
        """
        session = self.sessions.get(session_id)
        
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        session.is_active = False
        self._save_sessions()
        
        logger.info(f"Terminated session {session_id} for user {session.user_id}")
        return True
    
    def terminate_user_sessions(self, user_id: str) -> int:
        """
        Terminate all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of sessions terminated
        """
        user_sessions = [
            s for s in self.sessions.values()
            if s.user_id == user_id and s.is_active
        ]
        
        for session in user_sessions:
            session.is_active = False
        
        if user_sessions:
            self._save_sessions()
            logger.info(f"Terminated {len(user_sessions)} sessions for user {user_id}")
        
        return len(user_sessions)
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        self._cleanup_expired_sessions()
        return [
            s for s in self.sessions.values()
            if s.user_id == user_id and s.is_valid()
        ]
    
    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        """
        Validate CSRF token for a session.
        
        Args:
            session_id: Session identifier
            token: CSRF token to validate
            
        Returns:
            True if token is valid
        """
        session = self.validate_session(session_id)
        
        if not session:
            return False
        
        return session.csrf_token == token
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        return session.to_dict()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information by ID.
        
        Alias for get_session_info for backwards compatibility.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session info dictionary if found, None otherwise
        """
        return self.get_session_info(session_id)


# Global instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
