"""
Database models for POLISIM API.

Typed SQLAlchemy models with Postgres-friendly JSONB fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator
from typing import TYPE_CHECKING
from werkzeug.security import check_password_hash, generate_password_hash
import secrets


if TYPE_CHECKING:
    from sqlalchemy.dialects.postgresql import JSONB as JSONBType


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class JSONBCompat(TypeDecorator):
    """Use JSONB on Postgres, JSON elsewhere (SQLite-friendly)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from sqlalchemy.dialects.postgresql import JSONB as JSONBTypeRuntime

                return dialect.type_descriptor(JSONBTypeRuntime())
            except ImportError:
                # PostgreSQL JSONB not available, fall back to standard JSON
                pass
        return dialect.type_descriptor(JSON())


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    organization: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")  # user, researcher, admin

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    usage_logs: Mapped[List["UsageLog"]] = relationship(
        "UsageLog", back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash and set password."""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""

        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""

        data = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "organization": self.organization,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_sensitive:
            data["api_key_count"] = len(self.api_keys)
        return data


class UserPreferences(Base):
    """User UI preferences and settings."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Display Settings
    theme: Mapped[str] = mapped_column(String(50), default="light")
    tooltips_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    show_advanced_options: Mapped[bool] = mapped_column(Boolean, default=False)
    decimal_places: Mapped[int] = mapped_column(Integer, default=1)
    number_format: Mapped[str] = mapped_column(String(20), default="us")
    currency_symbol: Mapped[str] = mapped_column(String(10), default="$")

    # Chart Settings
    chart_theme: Mapped[str] = mapped_column(String(50), default="plotly_white")
    default_chart_type: Mapped[str] = mapped_column(String(20), default="line")
    color_palette: Mapped[str] = mapped_column(String(50), default="default")
    legend_position: Mapped[str] = mapped_column(String(20), default="top")

    # Animation Settings
    animation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    animation_speed: Mapped[str] = mapped_column(String(20), default="normal")

    # Performance Settings
    cache_duration_policies: Mapped[int] = mapped_column(Integer, default=3600)
    cache_duration_cbo_data: Mapped[int] = mapped_column(Integer, default=86400)
    cache_duration_charts: Mapped[int] = mapped_column(Integer, default=600)
    auto_refresh_data: Mapped[bool] = mapped_column(Boolean, default=False)
    max_monte_carlo_iterations: Mapped[int] = mapped_column(Integer, default=10000)

    # Advanced Settings
    debug_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    experimental_features: Mapped[bool] = mapped_column(Boolean, default=False)
    api_endpoint: Mapped[str] = mapped_column(String(255), default="http://localhost:5000")

    # Notification Preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_simulation_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_policy_updates: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_new_features: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_weekly_digest: Mapped[bool] = mapped_column(Boolean, default=False)

    # Locale Settings
    language: Mapped[str] = mapped_column(String(10), default="en")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    date_format: Mapped[str] = mapped_column(String(20), default="MM/DD/YYYY")

    # Custom Theme Configuration
    custom_theme_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONBCompat())

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""

        return {
            "id": self.id,
            "user_id": self.user_id,
            "theme": self.theme,
            "tooltips_enabled": self.tooltips_enabled,
            "show_advanced_options": self.show_advanced_options,
            "decimal_places": self.decimal_places,
            "number_format": self.number_format,
            "currency_symbol": self.currency_symbol,
            "chart_theme": self.chart_theme,
            "default_chart_type": self.default_chart_type,
            "color_palette": self.color_palette,
            "legend_position": self.legend_position,
            "animation_enabled": self.animation_enabled,
            "animation_speed": self.animation_speed,
            "cache_duration_policies": self.cache_duration_policies,
            "cache_duration_cbo_data": self.cache_duration_cbo_data,
            "cache_duration_charts": self.cache_duration_charts,
            "auto_refresh_data": self.auto_refresh_data,
            "max_monte_carlo_iterations": self.max_monte_carlo_iterations,
            "debug_mode": self.debug_mode,
            "experimental_features": self.experimental_features,
            "api_endpoint": self.api_endpoint,
            "email_notifications": self.email_notifications,
            "notify_simulation_complete": self.notify_simulation_complete,
            "notify_policy_updates": self.notify_policy_updates,
            "notify_new_features": self.notify_new_features,
            "notify_weekly_digest": self.notify_weekly_digest,
            "language": self.language,
            "timezone": self.timezone,
            "date_format": self.date_format,
            "custom_theme_config": self.custom_theme_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def get_default_preferences() -> Dict[str, Any]:
        """Get default preference values."""

        return {
            "theme": "light",
            "tooltips_enabled": True,
            "show_advanced_options": False,
            "decimal_places": 1,
            "number_format": "us",
            "currency_symbol": "$",
            "chart_theme": "plotly_white",
            "default_chart_type": "line",
            "color_palette": "default",
            "legend_position": "top",
            "animation_enabled": True,
            "animation_speed": "normal",
            "cache_duration_policies": 3600,
            "cache_duration_cbo_data": 86400,
            "cache_duration_charts": 600,
            "auto_refresh_data": False,
            "max_monte_carlo_iterations": 10000,
            "debug_mode": False,
            "experimental_features": False,
            "api_endpoint": "http://localhost:5000",
            "email_notifications": True,
            "notify_simulation_complete": True,
            "notify_policy_updates": False,
            "notify_new_features": True,
            "notify_weekly_digest": False,
            "language": "en",
            "timezone": "UTC",
            "date_format": "MM/DD/YYYY",
        }


class APIKey(Base):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Key details
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))  # User-friendly name
    prefix: Mapped[Optional[str]] = mapped_column(String(8))  # First 8 chars for display

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Rate limiting
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000)  # requests per hour

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key() -> str:
        """Generate secure API key."""

        return f"ps_{secrets.token_urlsafe(48)}"

    def to_dict(self, include_full_key: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""

        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "key": self.key if include_full_key else f"{self.prefix}...",
            "is_active": self.is_active,
            "rate_limit": self.rate_limit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class UsageLog(Base):
    """API usage tracking."""

    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Request details
    endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    method: Mapped[Optional[str]] = mapped_column(String(10))
    status_code: Mapped[Optional[int]] = mapped_column(Integer)

    # Performance
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float)

    # Metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_logs")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""

        return {
            "id": self.id,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


def init_db(engine) -> None:
    """Initialize database tables."""

    Base.metadata.create_all(engine)


def create_admin_user(session, email: str, username: str, password: str) -> User:
    """Create initial admin user."""

    user = User(
        email=email,
        username=username,
        full_name="Administrator",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    user.set_password(password)
    session.add(user)
    session.commit()
    return user
