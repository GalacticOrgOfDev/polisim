"""Database connection management for POLISIM API."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.models import Base
from api.secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)

# Database configuration
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / 'databases' / 'polisim.db'


def _resolve_database_url(override_url: Optional[str] = None) -> str:
    """
    Resolve database URL with priority order:
    1. Explicit override
    2. Secrets manager (AWS/Vault)
    3. Environment variable (DATABASE_URL)
    4. Default SQLite database
    """
    if override_url:
        logger.debug("Using explicitly provided database URL")
        return override_url
    
    # Try secrets manager
    secrets = get_secrets_manager()
    secret_db_url = secrets.get('DATABASE_URL')
    if secret_db_url:
        logger.debug("Database URL loaded from secrets manager")
        return secret_db_url
    
    # Try environment variable
    import os
    if 'DATABASE_URL' in os.environ:
        logger.debug("Database URL loaded from environment variable")
        return os.environ['DATABASE_URL']
    
    # Default to SQLite
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Using default SQLite database at {DEFAULT_DB_PATH}")
    return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


def _create_engine(db_url: str):
    """Create SQLAlchemy engine with SQLite-friendly settings."""
    connect_args = {'check_same_thread': False} if 'sqlite' in db_url else {}
    pool_class = StaticPool if 'sqlite' in db_url else None
    return create_engine(db_url, connect_args=connect_args, poolclass=pool_class)


def configure_engine(database_url: Optional[str] = None):
    """Configure global engine/session factory (used by app init and tests)."""
    global DATABASE_URL, engine, SessionLocal

    target_url = _resolve_database_url(database_url)

    # Dispose old engine to avoid leaked connections during reconfiguration
    if 'engine' in globals() and 'SessionLocal' in globals():
        try:
            engine.dispose()
        except Exception as e:
            # Log but don't fail on dispose error (engine might be in inconsistent state)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to dispose existing engine: {e}")

    DATABASE_URL = target_url
    engine = _create_engine(target_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def dispose_engine():
    """Dispose engine to close underlying connections (primarily for tests)."""
    global engine
    if 'engine' in globals() and engine is not None:
        try:
            # Dispose pool and connections
            engine.dispose()
        except Exception as e:
            # Log but don't fail on dispose error during cleanup
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to dispose engine during cleanup: {e}")


# Initialize defaults at import time
configure_engine()


def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Get database session."""
    return SessionLocal()


@contextmanager
def get_db():
    """
    Context manager for database sessions.
    
    Usage:
        with get_db() as session:
            user = session.query(User).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
