"""
Pytest configuration and fixtures for the entire test suite.
"""

import pytest


def pytest_configure(config):
    """Register custom markers for flexible test execution."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow/resource-intensive (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests with high iteration counts"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


@pytest.fixture(scope="session", autouse=True)
def cleanup_databases():
    """
    Cleanup database connections at the end of all tests.
    This prevents resource warnings about unclosed SQLite connections.
    """
    yield
    
    # Cleanup at session end
    try:
        from api.database import dispose_engine
        dispose_engine()
    except Exception:
        pass
