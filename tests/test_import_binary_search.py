#!/usr/bin/env python
"""Binary search for which import combination hangs - Unix only debug script.

This is a manual debugging script, not an automated test.
On Windows, these tests are skipped because signal.SIGALRM is not available.
"""

import sys
import platform
import pytest

# Skip entire module on Windows - signal.SIGALRM not available
pytestmark = pytest.mark.skipif(
    platform.system() == "Windows",
    reason="signal.SIGALRM not available on Windows"
)


@pytest.fixture
def setup_signal():
    """Set up signal handler for Unix systems only."""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Import timed out")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    yield signal
    signal.alarm(0)  # Cancel any pending alarm


def test_streamlit_social_security_import(setup_signal):
    """Test streamlit + social_security imports don't hang."""
    setup_signal.alarm(5)
    import streamlit as st
    from core.social_security import SocialSecurityModel
    setup_signal.alarm(0)


def test_streamlit_revenue_modeling_import(setup_signal):
    """Test streamlit + revenue_modeling imports don't hang."""
    setup_signal.alarm(5)
    import streamlit as st
    from core.revenue_modeling import FederalRevenueModel
    setup_signal.alarm(0)


def test_streamlit_medicare_medicaid_import(setup_signal):
    """Test streamlit + medicare_medicaid imports don't hang."""
    setup_signal.alarm(5)
    import streamlit as st
    from core.medicare_medicaid import MedicareModel
    setup_signal.alarm(0)


def test_streamlit_monte_carlo_import(setup_signal):
    """Test streamlit + monte_carlo_scenarios imports don't hang."""
    setup_signal.alarm(5)
    import streamlit as st
    from core.monte_carlo_scenarios import MonteCarloPolicySimulator
    setup_signal.alarm(0)


def test_streamlit_policy_extractor_import(setup_signal):
    """Test streamlit + policy_mechanics_extractor imports don't hang."""
    setup_signal.alarm(5)
    import streamlit as st
    from core.policy_mechanics_extractor import PolicyMechanicsExtractor
    setup_signal.alarm(0)
